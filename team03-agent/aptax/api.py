"""HTTP API on the standard library (agent_design.md §4.14).

    GET  /v1/liveness            200 while every registered loop beat within 900 s, else 503
    GET  /v1/runs                recent runs
    GET  /v1/runs/{run_id}       one run: status, answer, journal
    GET  /v1/refusals?hours=24   work a control prevented
    POST /v1/ask                 {"tenant": "in", "question": "..."}   control token
    POST /v1/control/stop        kill switch                         control token + loopback client

A loopback client may read without a token; any other client needs the control token for
everything. The server binds 127.0.0.1 by default. FastAPI is not installed on the team
machines, so this is http.server; the routes are the design's.
"""

import json
import re
import sys
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from aptax import __version__, liveness
from aptax.auth import check_control, is_loopback
from aptax.config import KILL_FILE, TENANTS, kill_switch_on
from aptax.llm import LLMNotConfigured, load_llm
from aptax.service import Refused, ServiceError, ask, make_transport

MAX_BODY_BYTES = 64 * 1024
MAX_QUESTION_CHARS = 2_000
REFUSAL_STATUS = {"kill_switch": 503, "dedupe": 409, "self_trigger": 403}    # others: 429
RUN_PATH = re.compile(r"^/v1/runs/(?P<run_id>[\w.-]{1,80})$")


class App:
    def __init__(self, store, *, llm=None, llm_error: str | None = None, transport_factory=make_transport):
        self.store = store
        self.llm = llm
        self.llm_error = llm_error
        self.transport_factory = transport_factory


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        server_version = f"aptax/{__version__}"

        def log_message(self, fmt, *args):          # request line only; never bodies or headers
            sys.stderr.write(f"{self.address_string()} {fmt % args}\n")

        def _send(self, status: int, body: dict) -> None:
            data = json.dumps(body, default=str, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _deny(self) -> bool:
            """Reads: loopback is trusted; anyone else must present the control token."""
            if is_loopback(self.client_address[0]):
                return False
            problem = check_control(self.headers.get("Authorization"))
            if problem:
                self._send(problem[0], {"error": problem[1]})
                return True
            return False

        def _body(self) -> dict | None:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if length < 0 or length > MAX_BODY_BYTES:
                self._send(413, {"error": f"body must be at most {MAX_BODY_BYTES} bytes"})
                return None
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send(400, {"error": "body is not valid JSON"})
                return None
            if not isinstance(body, dict):
                self._send(400, {"error": "body must be a JSON object"})
                return None
            return body

        # -- reads ----------------------------------------------------------------

        def do_GET(self):  # noqa: N802 — http.server naming
            if self._deny():
                return
            url = urlparse(self.path)
            if url.path == "/v1/liveness":
                ok, loops = liveness.status()
                return self._send(200 if ok else 503, {"ok": ok, "loops": loops, "kill_switch": kill_switch_on()})
            if url.path == "/v1/runs":
                return self._send(200, {"runs": app.store.recent_runs(50)})
            m = RUN_PATH.match(url.path)
            if m:
                run = app.store.get_run(m["run_id"])
                if not run:
                    return self._send(404, {"error": "no such run"})
                return self._send(200, {"run": run, "journal": app.store.journal_entries(m["run_id"])})
            if url.path == "/v1/refusals":
                raw = parse_qs(url.query).get("hours", ["24"])[0]
                if not raw.isdigit() or not 1 <= int(raw) <= 720:
                    return self._send(400, {"error": "hours must be an integer from 1 to 720"})
                since = (datetime.now(UTC) - timedelta(hours=int(raw))).isoformat(timespec="seconds")
                return self._send(200, {"since": since, "refusals": app.store.refusals(since)})
            self._send(404, {"error": "not found"})

        # -- control --------------------------------------------------------------

        def do_POST(self):  # noqa: N802
            url = urlparse(self.path)
            if url.path not in ("/v1/ask", "/v1/control/stop"):
                return self._send(404, {"error": "not found"})
            problem = check_control(self.headers.get("Authorization"))
            if problem:
                return self._send(problem[0], {"error": problem[1]})
            if url.path == "/v1/control/stop":
                if not is_loopback(self.client_address[0]):
                    return self._send(403, {"error": "the kill switch only accepts loopback clients"})
                KILL_FILE.write_text(f"stopped via API at {datetime.now(UTC).isoformat(timespec='seconds')}\n",
                                     encoding="utf-8")
                return self._send(200, {"kill_switch": "on", "file": str(KILL_FILE)})
            body = self._body()
            if body is None:
                return None
            unknown = set(body) - {"tenant", "question"}
            tenant, question = body.get("tenant"), body.get("question")
            if unknown:
                return self._send(400, {"error": f"unsupported fields: {sorted(unknown)}"})
            if tenant not in TENANTS:
                return self._send(400, {"error": f"tenant must be one of {sorted(TENANTS)}"})
            if not isinstance(question, str) or not question.strip() or len(question) > MAX_QUESTION_CHARS:
                return self._send(400, {"error": f"question must be 1-{MAX_QUESTION_CHARS} characters"})
            if app.llm is None:
                return self._send(503, {"error": app.llm_error or "no LLM gateway configured"})
            try:
                result = ask(app.store, app.transport_factory, tenant=tenant, question=question,
                             llm=app.llm, source="user.api")
            except Refused as exc:
                return self._send(REFUSAL_STATUS.get(exc.control, 429),
                                  {"status": "refused", "control": exc.control, "reason": exc.reason})
            except ServiceError as exc:
                return self._send(502, {"status": "failed", "error": str(exc)})
            self._send(200, result)

    return Handler


def serve(store, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    try:
        llm, llm_error = load_llm(), None
    except LLMNotConfigured as exc:
        llm, llm_error = None, str(exc)
    server = ThreadingHTTPServer((host, port), make_handler(App(store, llm=llm, llm_error=llm_error)))
    print(f"aptax API on http://{host}:{port}  (LLM: {'plugged in' if llm else 'not configured'})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

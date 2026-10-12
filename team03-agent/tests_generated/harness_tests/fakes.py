"""LLM-generated, not graded. Stand-ins for the aptax objects the harness reads."""

from dataclasses import dataclass, field


@dataclass
class FakeManifest:
    id: str
    title: str = "A playbook"
    tax_regimes: tuple = ("gst",)


@dataclass
class FakeRoute:
    manifest: FakeManifest
    action: str = "run"
    reason: str = ""


@dataclass
class FakeOutcome:
    summary: str = ""
    context: dict = field(default_factory=dict)
    findings: list = field(default_factory=list)


@dataclass
class FakeRun:
    route: FakeRoute
    outcome: FakeOutcome | None = None
    error: str | None = None


@dataclass
class FakeCtx:
    tax_regime: str


class FakeGateway:
    def __init__(self):
        self.stats = {"called": 0, "refused": 0, "suppressed": 0, "failed": 0}


class FakeRunner:
    """routes: list[FakeRoute]; behaviours: playbook id -> fn(gateway, manifest) -> FakeRun."""

    def __init__(self, gateway, routes, behaviours):
        self.gateway = gateway
        self._routes = routes
        self._behaviours = behaviours
        self.ran = []

    def routes(self, *, trigger=None, cadence=None):
        return list(self._routes)

    def run_one(self, manifest, *, escalate=False):
        assert escalate is False
        self.ran.append(manifest.id)
        return self._behaviours[manifest.id](self.gateway, manifest)


class FakeSession:
    def __init__(self, tax_regime, routes, behaviours):
        self.ctx = FakeCtx(tax_regime)
        self.gateway = FakeGateway()
        self.runner = FakeRunner(self.gateway, routes, behaviours)
        self.run_id = "run-1"


class FakeTransport:
    def __init__(self, tools=("Bill.list",), me=None, tools_error=None):
        self.tools = tools
        self.me = {"email": "team03@theschoolofai.in"} if me is None else me
        self.tools_error = tools_error

    def tools_list(self):
        if self.tools_error:
            raise self.tools_error
        return list(self.tools)

    def rest(self, method, path, params=None, body=None):
        assert (method, path) == ("GET", "/api/auth/me")
        return self.me


class FakeStore:
    def __init__(self):
        self.finished = []
        self.closed = False

    def finish_run(self, run_id, status):
        self.finished.append((run_id, status))

    def close(self):
        self.closed = True

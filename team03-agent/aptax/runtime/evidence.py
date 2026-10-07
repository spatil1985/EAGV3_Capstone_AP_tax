"""Deterministic evidence check for submit_answer (agent_design.md §4.6).

S17 asks a second model whether an answer is supported; this agent checks it in code.
Every capability result the model sees gets an evidence id (E1, E2, …), and every
finding row inside it is also citable on its own by its finding id (the fingerprint).
An answer passes when:

1. it has a section for each part of the user's question (`question_parts`);
2. every section cites at least one id, and every cited id exists in this run;
3. every number in a section's narrative appears in the evidence that section cites,
   or in the user's own question. A number may be shown rounded to fewer decimals, as
   a percentage of a stored fraction, or in thousand/lakh/crore/million units — it may
   not be changed. Signs are ignored ("a credit of ₹500" matches -500).

Not checked: dates and periods (2026-09-30, 2026-09, 30 Nov 2026), years, ordinals
(7th), statute and form references (s.16(4), Rule 37, section 194C, Form 1099), ids
glued to letters or dashes (UC-23, B-981, GSTR-3B) and bare integers below 10
("top 3"). Caveats carry no citations and are not checked.
"""

import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from aptax.capabilities.registry import CapabilityError

_MONTH = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|june?|july?|aug(?:ust)?"
          r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b\.?")
NOT_CHECKED = [
    re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?\b"),                                   # 2026-09-30, 2026-09, 2026-27
    re.compile(rf"\b\d{{1,2}}\s+{_MONTH}(?:\s*,?\s*\d{{4}})?", re.I),             # 30 Nov 2026
    re.compile(rf"\b{_MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?\b(?:\s*,?\s*\d{{4}})?", re.I),  # Nov 30, 2026
    re.compile(rf"\b{_MONTH}\s+\d{{4}}\b", re.I),                                 # September 2026
    re.compile(r"\b\d{1,2}\s+may\s+\d{4}\b|\bmay\s+\d{1,2},?\s+\d{4}\b|\bmay\s+\d{4}\b", re.I),
    re.compile(r"(?:\bs\.|\bsec\.?|\bsection|\brules?|\barticle|\bform|\bschedule|\bpara|\bclause"
               r"|\bu/s\.?)\s*\d+[a-z]*(?:\(\w+\))*", re.I),                      # s.16(4), Rule 37, section 194C
    re.compile(r"\b\d+(?:st|nd|rd|th)\b", re.I),                                 # 7th, 20th
    re.compile(r"\b(?:fy|ay)\s*\d{2,4}(?:-\d{2,4})?\b", re.I),                   # FY 2026-27
]

_TOKEN = re.compile(r"""
    (?<![\w.\-/])                                    # not glued to an id, a decimal or a path
    (?P<neg>[-−])?
    (?P<cur>₹|\$|rs\.?\s?|inr\s?|usd\s?)?
    (?P<num>(?>\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?))
    (?:
        \s?(?P<pct>%|percent\b|per\s?cent\b)
      | \s?(?P<scale>thousand|lakhs?|lacs?|crores?|cr|mn|million|bn|billion)\b
      | (?P<abbr>(?-i:[kKM]))\b
    )?
    (?![\w\-]|/(?!-)|\.\d)                           # "₹1,234/-" is fine; "1.2.3" is not a number
""", re.I | re.X)

_SCALES = {"thousand": 3, "k": 3, "lakh": 5, "lakhs": 5, "lac": 5, "lacs": 5, "crore": 7,
           "crores": 7, "cr": 7, "mn": 6, "million": 6, "m": 6, "bn": 9, "billion": 9}
_PLAIN = re.compile(r"^\s*[-−+]?\s*(?:₹|\$|rs\.?|inr|usd)?\s*(?P<n>\d[\d,]*(?:\.\d+)?)\s*%?\s*$", re.I)
_PART_SPLIT = re.compile(r"\?|[,;]\s*(?:and\s+|or\s+)?(?=(?:what|which|who|how|is|are|was|were|do|does|did"
                         r"|can|should|will|has|have|when|where|why)\b)", re.I)


@dataclass(frozen=True)
class NumberToken:
    text: str           # as written, e.g. "₹19.56 lakh"
    value: Decimal      # the digits, e.g. 19.56
    places: int         # decimals shown, e.g. 2
    exp: int = 0        # unit as a power of ten, e.g. 5 for lakh
    pct: bool = False

    def supported_by(self, values) -> bool:
        step = Decimal(1).scaleb(-self.places)
        for v in values:
            v = abs(v)
            for candidate in ((v, v * 100) if self.pct else (v,)):
                shown = candidate.scaleb(-self.exp) if self.exp else candidate
                if shown == self.value:
                    return True
                try:
                    if shown.quantize(step, rounding=ROUND_HALF_UP) == self.value:
                        return True
                except InvalidOperation:
                    continue
        return False


def number_tokens(text: str, *, checked_only: bool = True) -> list[NumberToken]:
    """Numbers in prose. `checked_only` drops the exempt kinds listed in the module doc."""
    if checked_only:
        for pattern in NOT_CHECKED:
            text = pattern.sub(lambda m: " " * len(m.group()), text)
    out = []
    for m in _TOKEN.finditer(text or ""):
        raw = m.group("num")
        value = Decimal(raw.replace(",", ""))
        bare = not (m.group("cur") or m.group("pct") or m.group("scale") or m.group("abbr")
                    or "," in raw or "." in raw)
        if checked_only and bare and (value < 10 or (len(raw) == 4 and 1900 <= value <= 2100)):
            continue
        unit = (m.group("scale") or m.group("abbr") or "").lower()
        out.append(NumberToken(m.group().strip(), value, len(raw.partition(".")[2]),
                               _SCALES.get(unit, 0), bool(m.group("pct"))))
    return out


def numbers_in(value, out: set | None = None, depth: int = 0) -> set[Decimal]:
    """Every number a piece of evidence states: numeric fields, numeric strings and
    numbers written in its prose. Id-like strings (UUIDs, INV-0042, dates) add nothing."""
    out = set() if out is None else out
    if depth > 12 or value is None or isinstance(value, bool):
        return out
    if isinstance(value, (int, Decimal)):
        out.add(abs(Decimal(value)))
    elif isinstance(value, float):
        out.add(abs(Decimal(repr(value))))
    elif isinstance(value, str):
        plain = _PLAIN.match(value)
        if plain:
            out.add(Decimal(plain.group("n").replace(",", "")))
        elif " " in value.strip():
            for tok in number_tokens(value, checked_only=False):
                out.add(tok.value if tok.pct else tok.value.scaleb(tok.exp))
    elif isinstance(value, dict):
        for v in value.values():
            numbers_in(v, out, depth + 1)
    elif isinstance(value, (list, tuple, set)):
        for v in value:
            numbers_in(v, out, depth + 1)
    return out


def question_parts(question: str) -> list[str]:
    """The sub-questions a question asks: split on '?' and on ', what …' / ', and is …'.

    "What is our tax liability this period, what is unclaimed, and is any vendor being
    paid twice?" has three parts.
    """
    parts = [p.strip(" ,;.") for p in _PART_SPLIT.split(question or "")]
    return [p for p in parts if len(p) > 2] or [question.strip()]


# -- the ledger of evidence one run has produced ---------------------------------------

@dataclass
class Evidence:
    id: str
    capability: str
    args: dict
    data: object
    numbers: set = field(default_factory=set)


def _finding_rows(value, depth: int = 0):
    if depth > 6:
        return
    if isinstance(value, dict):
        if value.get("finding_id") or value.get("fingerprint"):
            yield value
            return
        for v in value.values():
            yield from _finding_rows(v, depth + 1)
    elif isinstance(value, list):
        for v in value:
            yield from _finding_rows(v, depth + 1)


class EvidenceLedger:
    """Evidence ids are assigned by the loop thread in call order, so they are stable."""

    def __init__(self):
        self.items: dict[str, Evidence] = {}
        self.findings: dict[str, dict] = {}         # finding id → row
        self.finding_source: dict[str, str] = {}    # finding id → evidence id it came in

    def add(self, capability: str, args: dict, data) -> str:
        eid = f"E{len(self.items) + 1}"
        self.items[eid] = Evidence(eid, capability, dict(args), data, numbers_in(data))
        for row in _finding_rows(data):
            fid = str(row.get("finding_id") or row.get("fingerprint"))
            self.findings.setdefault(fid, row)
            self.finding_source.setdefault(fid, eid)
        return eid

    def __contains__(self, ident: str) -> bool:
        return ident in self.items or ident in self.findings

    def numbers(self, ident: str) -> set[Decimal]:
        if ident in self.items:
            return self.items[ident].numbers
        if ident in self.findings:
            return numbers_in(self.findings[ident])
        return set()


# -- the answer and its check -----------------------------------------------------------

@dataclass(frozen=True)
class Section:
    question: str
    evidence_ids: tuple
    narrative: str


SECTION_FIELDS = {"question", "evidence_ids", "narrative"}
MAX_NARRATIVE_CHARS = 6_000


def parse_answer(args: dict) -> tuple[list[Section], list[str]]:
    """Strict shape check of submit_answer's arguments (the JSON schema, enforced)."""
    raw = args.get("sections")
    if not isinstance(raw, list) or not raw:
        raise CapabilityError("submit_answer.sections must be a non-empty array")
    sections = []
    for i, s in enumerate(raw, 1):
        if not isinstance(s, dict):
            raise CapabilityError(f"section {i} must be an object")
        unknown = set(s) - SECTION_FIELDS
        if unknown:
            raise CapabilityError(f"section {i}: unsupported fields {sorted(unknown)}")
        question, narrative, ids = s.get("question"), s.get("narrative"), s.get("evidence_ids")
        if not isinstance(question, str) or not question.strip():
            raise CapabilityError(f"section {i}.question must be a non-empty string")
        if not isinstance(narrative, str) or not narrative.strip():
            raise CapabilityError(f"section {i}.narrative must be a non-empty string")
        if len(narrative) > MAX_NARRATIVE_CHARS:
            raise CapabilityError(f"section {i}.narrative exceeds {MAX_NARRATIVE_CHARS} characters")
        if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            raise CapabilityError(f"section {i}.evidence_ids must be an array of strings")
        sections.append(Section(question.strip(), tuple(x.strip() for x in ids if x.strip()),
                                narrative.strip()))
    caveats = args.get("caveats") or []
    if not all(isinstance(c, str) for c in caveats):
        raise CapabilityError("submit_answer.caveats must be an array of strings")
    return sections, [c.strip() for c in caveats if c.strip()]


@dataclass
class EvidenceReport:
    ok: bool = True
    problems: list[str] = field(default_factory=list)
    unsupported: dict[int, list[str]] = field(default_factory=dict)   # section no. → numbers as written
    unknown_ids: dict[int, list[str]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"ok": self.ok, "problems": self.problems,
                "unsupported": {str(k): v for k, v in self.unsupported.items()},
                "unknown_ids": {str(k): v for k, v in self.unknown_ids.items()}}


def check_answer(sections: list[Section], ledger: EvidenceLedger, *, question: str) -> EvidenceReport:
    report = EvidenceReport()
    parts = question_parts(question)
    if len(sections) < len(parts):
        listed = "; ".join(f"({n}) {p}" for n, p in enumerate(parts, 1))
        report.problems.append(f"the question has {len(parts)} parts but the answer has "
                               f"{len(sections)} section(s); answer each part in its own section: {listed}")
    asked = numbers_in(question)
    for n, section in enumerate(sections, 1):
        if not section.evidence_ids:
            report.problems.append(f"section {n} cites no evidence")
        unknown = [x for x in section.evidence_ids if x not in ledger]
        if unknown:
            report.unknown_ids[n] = unknown
            report.problems.append(f"section {n} cites ids that do not exist in this run: {', '.join(unknown)}")
        values = set(asked)
        for ident in section.evidence_ids:
            values |= ledger.numbers(ident)
        bad = [t.text for t in number_tokens(section.narrative) if not t.supported_by(values)]
        if bad:
            report.unsupported[n] = bad
            report.problems.append(f"section {n}: these numbers are not in the evidence it cites: {', '.join(bad)}")
    report.ok = not report.problems
    return report

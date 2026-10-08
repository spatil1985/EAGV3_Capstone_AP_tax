"""TDS section, rate and base helpers shared by UC-09, UC-39, UC-13 and UC-37.

Section from the line's SAC (UC-09 §5 table); goods never attract 194C/J/I (that is 194Q,
UC-13). Rate from the section and the deductee: PAN 4th character P/H (individual/HUF) gives
the 194C 1% rate. A missing PAN would raise the rate to 20% (s.206AA): reported, not assumed,
because PANs are blank on every vendor in the live data.

The stored `tds_amount` / `tds_section_code` are quarantined at fetch (N7): read through
`_suspect_*`, recomputed here.
"""

from decimal import Decimal

from scripts.money import CENTS, money
from scripts.uc.common.lines import line_value

# (SAC prefix, section, rate constant, label). Longest prefix wins.
SECTIONS = [
    ("9965", "194C", None, "transport of goods"),
    ("9967", "194C", None, "transport support services"),
    ("9954", "194C", None, "construction / works contract"),
    ("9985", "194C", None, "support services (manpower, security, cleaning)"),
    ("9987", "194C", None, "maintenance and repair"),
    ("9988", "194C", None, "job work / manufacturing services"),
    ("9982", "194J", "tds_rate_194j_professional_pct", "legal and accounting services"),
    ("9983", "194J", "tds_rate_194j_technical_pct", "professional and technical services"),
    ("998311", "194J", "tds_rate_194j_professional_pct", "management consulting"),
    ("9972", "194I", "tds_rate_194i_building_pct", "rent of immovable property"),
    ("997313", "194I", "tds_rate_194i_machinery_pct", "rent of machinery"),
]


def section_for(code: str):
    code = str(code or "")
    best = None
    for prefix, section, rate, label in SECTIONS:
        if code.startswith(prefix) and (best is None or len(prefix) > len(best[0])):
            best = (prefix, section, rate, label)
    return best


def is_individual(party: dict | None) -> bool:
    pan = str((party or {}).get("pan") or "")
    if len(pan) >= 4:
        return pan[3].upper() in ("P", "H")
    return (party or {}).get("type") == "individual"


def rate_for(section: str, rate_name: str | None, party, ctx) -> Decimal:
    if section == "194C":
        name = "tds_rate_194c_individual_pct" if is_individual(party) else "tds_rate_194c_other_pct"
        return Decimal(str(ctx.constant(name)))
    return Decimal(str(ctx.constant(rate_name)))


def base(bill: dict) -> Decimal:
    """TDS base excludes GST when GST is shown separately (CBDT Circular 23/2017)."""
    return sum((line_value(l) for l in bill.get("items") or []), Decimal("0"))


def expected(bill: dict, party, ctx):
    """[(section, label, line base, rate, amount)] for the bill's TDS-bearing lines."""
    out = []
    for line in bill.get("items") or []:
        hit = section_for(line.get("hsn_or_sac"))
        if not hit:
            continue
        _, section, rate_name, label = hit
        rate = rate_for(section, rate_name, party, ctx)
        value = line_value(line)
        out.append((section, label, value, rate, (value * rate / 100).quantize(CENTS)))
    return out


def stored(bill: dict) -> tuple[Decimal, Decimal, str | None]:
    return (money(bill.get("_suspect_tds_amount", bill.get("tds_amount"))),
            money(bill.get("tds_percentage")), bill.get("tds_section"))


def all_goods(bill: dict) -> bool:
    lines = bill.get("items") or []
    codes = [str(l.get("hsn_or_sac") or "") for l in lines]
    return bool(codes) and all(c and not c.startswith("99") for c in codes)

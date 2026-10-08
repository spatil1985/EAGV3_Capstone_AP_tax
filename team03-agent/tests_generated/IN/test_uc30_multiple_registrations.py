"""LLM-generated, not graded. UC-30 registrations (spec §5 worked example)."""

from scripts.uc.IN.uc30_multiple_registrations import MultipleRegistrations

ORG = [{"gstin": "27AASCS7781M1ZQ", "pan": "AASCS7781M"}]


def run(make_ctx, ds, locations):
    return MultipleRegistrations().evaluate(ds(locations=locations, org=ORG, invoices=[]), make_ctx())


def test_primary_with_another_pan(make_ctx, ds):
    loc = {"id": "c", "name": "Chakan Plant", "is_primary": True, "state_code": "27", "gstin": "27AACCS4471P1ZK"}
    assert sorted(f.rule for f in run(make_ctx, ds, [loc])) == ["primary_gstin_mismatch", "registration_pan_mismatch"]


def test_seeded_branch(make_ctx, ds):
    loc = {"id": "a", "name": "Branch", "state_code": "FS3772/4032", "gstin": "09AWZPQ2663H8ZH"}
    assert sorted(f.rule for f in run(make_ctx, ds, [loc])) == ["location_state_code_invalid", "registration_pan_mismatch"]


def test_clean_registration(make_ctx, ds):
    loc = {"id": "g", "name": "Sanand", "state_code": "24", "gstin": "24AASCS7781M1ZX"}
    assert run(make_ctx, ds, [loc]) == []

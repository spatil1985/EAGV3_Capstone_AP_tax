# tests_generated/ — LLM-generated playbook checks (NOT graded)

**Everything in this folder was written by Claude, not by a person.** The capstone grades
only hand-written tests, and LLM-generated tests score 0
([`../CURRENT_STATUS.md`](../CURRENT_STATUS.md) §0 rule 4). These files are kept apart from
[`../tests/`](../tests/) so the grader never mixes them with the team's own tests.

They exist so each playbook has a quick offline check while it is being built:

- each test builds a small `Dataset` by hand and calls the playbook's pure
  `evaluate(dataset, ctx)`; no network, credentials or mocks;
- `conftest.py` provides `make_ctx(...)`, a run context backed by the real
  `playbooks/constants.yaml` rulebook;
- one file per use case, by jurisdiction: `IN/test_ucNN_*.py`, `US/test_usNN_*.py`.

```
py -3 -m pytest tests_generated -q
```

Use them as a starting point for ideas; write the graded tests yourself in `tests/`.

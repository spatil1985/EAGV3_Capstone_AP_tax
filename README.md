# EAGV3_Capstone_AP_tax

Team 03 capstone: Payables & Tax Agent (Seat 03) on the AgentSwitch platform.

- Core challenge: "What is our tax liability this period, what is unclaimed, and is any vendor being paid twice?"
- Jurisdictions: Suryodaya Precision Works (India — GST/TDS/MSME) and Keystone Precision Works LLC (US — Sales & Use Tax).

## Repo layout

```
team03-agent/
├── SKILL.md              # Agent charter, identity, rules, and boundaries
├── playbooks/
│   ├── duplicate_audit.md
│   └── tax_audit.md
├── scripts/
│   ├── tax_math.py
│   └── invoice_matcher.py
├── tests/
│   ├── test_duplicate_pay.py
│   └── test_tax_audit.py
├── run_agent.py           # Custom MCP-driven agent loop (no third-party frameworks)
└── DESIGN.md              # Architecture, state tolerance, refusal handling, limitations
```

## Running tests

```
cd team03-agent
pip install -r requirements.txt
pytest tests/ -v
```

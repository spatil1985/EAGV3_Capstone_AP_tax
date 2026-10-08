"""One module per use case (agent_design.md §4.12), by jurisdiction: IN/ (GST, Suryodaya)
and US/ (sales & use tax, Keystone). Each exposes a `Playbook` subclass named by its
manifest's `compute:` field in playbooks/IN or playbooks/US. Helpers shared by more than
one use case live in common/."""

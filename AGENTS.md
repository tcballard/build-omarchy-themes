# Repository guidance

Canonical skills live in skills/. Generate the OpenAI copies with
`python3 scripts/sync_openai_adapter.py --write`; never edit them independently.
Run `./scripts/test` for bundle changes. Use `--portable-only` when Rust is absent,
and report Rust checks as not run. Tests use disposable fixtures with no desktop
or publication access. Complete relevant checks and fix regressions without asking
for approval at each step. Preserve the twelve independently installable skills.

Use branches and PRs. Treat installed-personal-skill updates, live theme changes and
registry submissions as separate actions. For releases follow docs/RELEASING.md.

Keep the shared `## Task completion` block byte-identical across all twelve canonical
skills and last in each file: check_bundle.py compares from that heading to EOF.
Put skill-specific instructions above it, then regenerate and check OpenAI adapter
parity. Provider-informed guidance is not evidence of execution on that provider.

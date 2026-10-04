# Acceptance evidence — v0.3.0 candidate, 4 October 2026

- Twelve canonical skills and OpenAI copies pass structure, version, shared-reference
  and adapter parity checks. Seven skill bodies gain guidance; all twelve receive
  the refreshed shared contract.
- 22 portable regressions pass: 10 governance, 11 project-gate and one installer
  lifecycle test. New gates exercise thresholds, missing/unsupported values,
  repeated rules, opt-in/root-scoped ignored files, malformed TOML, unreadable
  inventory, links, image corruption/format mismatch, missing decoder, resource
  limits and animated frames. Python 3.11+; local Pillow 12.3.0.
- Fresh Git HTTPS checkouts verified all eleven existing pinned sources against
  recorded blob identities and current content: unchanged. Four additional shell
  sources reviewed and pinned. See runs/2026-10-04-contracts.json. Direct HTTP
  --live transport did not complete locally; do not call it an HTTP pass.
- Three fresh-context, read-only synthetic workflow exercises pass: personal
  override, Git staging and stale application. Fixture hashes unchanged; responses
  and skill hashes recorded in runs/2026-10-04-workflows.json. Candidate smoke
  evidence only, not measured model improvement or real-app validation.
- Local Rust checks: NOT RUN (Cargo unavailable). Full CI and clean-commit release
  packaging must pass for the exact candidate before release.
- Live desktop, Familiar/Paint/Task Manager acceptance, installed host discovery,
  registry submission and Claude model evaluation: NOT RUN. Existing Claude
  evaluation tooling and its original 144-session plan remain unchanged.

---

# Acceptance evidence — v0.2.0 preparation, 29 September 2026

- Twelve canonical skills and generated OpenAI copies pass structure/parity checks.
- Ten governance regressions pass: versions/provider paths/shared references,
  clean-tree deterministic archives, contract drift and unavailable-source handling.
- Installer lifecycle test passes, including protection of locally modified files.
- Two independent fresh-context workflow exercises pass: accent-only repair without
  a helper, and read-only staging diagnosis. Input hashes and observed outcomes are
  in [the run record](runs/2026-09-29.json). The evaluator independently checked the
  accent-only byte change and unchanged diagnosis fixture. These predate the replacement completion block and are historical candidate-only
  smoke tests, not validation of that block or a model benchmark.
- Eleven exact upstream files retrieved through the GitHub connector and reviewed;
  direct network execution of the new --live checker is a separate CI check.
- Local Rust tests: NOT RUN because Cargo is unavailable. Require full GitHub CI for
  the release candidate; do not reuse v0.1.0 results as fresh execution evidence.
- Live Omarchy desktop, upstream registry validation of a finished theme, live host
  discovery and Claude execution: NOT RUN. No Claude model has executed the skills.

## Historical v0.1.0 evidence

# Acceptance evidence — 14 September 2026

Version 0.1.0 development preview.

| Check | Evidence |
| --- | --- |
| Rust helper | 10 unit tests passed: starter/required keys, strict parsing, duplicates, comments, Unicode/bad hex, slug policy and contrast |
| Workflow integration | 5 tests passed: scaffold/check, existing-file protection, link rejection, ignored terminal config reporting, install/update/remove with local-change protection |
| Skill structure | 12 portable skills and 12 OpenAI adapter copies validated |
| Adapter parity | Byte/mode comparison passed |
| Independent workflow exercise | Debug/migrate/publish scenario correctly identified provenance-sensitive staging; preserved unknown installed-version, media-rights and live-preview gates; no external action |
| Live Omarchy desktop | NOT RUN: this environment is not an Omarchy session |
| Official theme-registry validation of a generated theme | NOT RUN: scaffold intentionally lacks final media and a real desktop preview |
| Live agent-host discovery | NOT RUN: adapters and files validated only |
| Release archive reproducibility | Five archives and manifests built twice from one clean committed tree; byte-for-byte comparison passed |

The local helper is intentionally a strict authoring-subset checker, not the
registry validator. Its preview.png profile is a project recommendation; the
registry also accepts other observed preview formats. It does not decode images,
resolve all TOML or legacy colour aliases, verify wallpaper rights, reserve a
slug, or establish runtime compatibility.

# Release preparation

1. Update VERSION and all three plugin manifests together; write factual release
   notes in docs/releases/vVERSION.md and add the changelog entry.
2. Re-read all provider guides linked in docs/FRONTIER-MODELS.md before changing
   model guidance. Record the review date and inaccessible sources, verify per-model
   host settings, and distinguish guidance from model execution evidence.
3. Refresh contracts by inspecting content changes before replacing pins. Record
   repository, ref, exact commit and Git blob identity; do not auto-accept drift.
4. Run ./scripts/test, including version/reference checks, adapter parity, Rust and
   packaging regression tests. Run `python3 scripts/check_contracts.py --live`
   with network access. Unavailable contracts fail the live check.
5. Review and commit the change through a PR; require CI for the exact candidate.
   Build twice from that clean commit with scripts/package.py into separate output
   directories. Compare archives, manifest and SHA256SUMS byte-for-byte.
6. Within release authorisation, tag that tested commit and publish the five archives,
   source-manifest.json and SHA256SUMS with the prepared notes. Keep published tags
   and assets immutable. Do not claim live desktop or model tests that were not run.

The scheduled contract check detects changed file contents. Movement of an upstream
branch with unchanged contract bytes is informational. Offline checks validate pin
structure and local consistency only; they do not establish upstream freshness.

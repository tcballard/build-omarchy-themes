# Development handoff

Before delivering a theme archive or opening a development PR, run this gate even
when no release is requested. It is independent of live acceptance, release
preparation and registry submission. Missing desktop access is a visible NOT RUN,
not a reason to withhold a useful development PR. Do not relabel failures as passes.

The scaffold README supplies the exact category SVG and 20px badges. Canonical SVG:
https://raw.githubusercontent.com/tcballard/omarchy-badges/75975e5b5bf75e7ede3764bcd2950046f7abfe2c/badges/v1/omarchy-theme.svg

Keep its height at 20px, natural width and unmodified artwork. Update target/status
labels honestly; the intended installed Omarchy target is separate from the exact
installed version actually tested. `none` is valid. The community badge is not certification.

## Commands and evidence

Resolve the scaffold skill's real directory, independent of the current directory.
The Rust helper has no external crates; manifest commands require Git on PATH.
For existing themes, adapt the bundled templates without overwriting their README.

```sh
cargo run --manifest-path "<scaffold-skill-dir>/scripts/theme-tool/Cargo.toml" -- snapshot /path/to/theme evidence/local-1.manifest --implementation
# Run the actual checks, retaining commands, outputs and upstream commit/blob IDs.
cargo run --manifest-path "<scaffold-skill-dir>/scripts/theme-tool/Cargo.toml" -- check /path/to/theme
# Update evidence/checks.tsv with only results actually observed.
cargo run --manifest-path "<scaffold-skill-dir>/scripts/theme-tool/Cargo.toml" -- snapshot /path/to/theme evidence/delivery-1.manifest
cargo run --manifest-path "<scaffold-skill-dir>/scripts/theme-tool/Cargo.toml" -- handoff /path/to/theme evidence/delivery-1.manifest
```

Snapshots are immutable Git SHA-1 blob manifests; use a new filename after changes.
The delivery manifest includes every regular file except `.git` and `evidence/`.
An implementation manifest additionally excludes Markdown, so documentation-only
corrections need a new delivery snapshot and handoff check, not full runtime retesting.
Images under docs/ and all scripts/configs remain implementation inputs. Evidence/
is reserved for the ledger, manifests and text logs, never theme runtime files.
Archive exactly this reviewed tree and include its evidence; check the extracted
archive, or the PR's final checked-out tree, against the delivery manifest.

`evidence/checks.tsv` has seven tab-separated fields:

| Field | Values |
| --- | --- |
| state | `now` (reproduced successfully this task), `historical` (not rerun), `failure`, `not-run` |
| kind | `local`, `live`, `registry` |
| manifest | `evidence/<name>.manifest`; `-` for not-run |
| upstream | Exact repository URL + commit/blob ID used; `none` only for checks with no upstream dependency or not-run |
| installed-version | Exact `omarchy-version` output for live; `-` otherwise |
| command | Exact command(s) executed, with source/tool revision and log path when relevant; `-` for not-run |
| result | Concrete observed result or reason not run; include environment and limitations |

Retain separate rows for all four states as applicable; explicitly cover local,
live and registry even when not run. Historical snapshots may differ, but are then
reported as evidence for different files and cannot support this delivery's tested
version. Current results must match. An unchanged implementation may retain
historical live evidence without claiming it was rerun. Upstream-dependent local
checks need the upstream ID too; the checker cannot infer which commands use upstream.
Neither a snapshot nor this checker executes or attests to a recorded test.

## Media and review

Use `media.tsv` rows: `path<TAB>kind<TAB>caption`. Kinds: wallpaper, contact-sheet,
desktop-screenshot, mockup. Declare every shipped image/video. Contact-sheet/mockup
captions must say `not a desktop screenshot`, including when embedded in README;
reserve `preview.*` for real desktop captures, supported by matching live evidence.
Record each wallpaper's exact delivered path in CREDITS.md with creator, source,
licence and redistribution permission (or explicitly pending for a development handoff).
Remove entries for excluded artwork. A code licence is not media permission.

The checker covers inline Markdown links, reference definitions, quoted HTML
src/href and bare backgrounds/docs paths. Use plain relative paths; encoded paths,
parent traversal and unsupported Markdown need manual review or normalization.
It checks local existence, not remote availability, image contents, legal rights or
all possible natural-language compatibility claims. Review the rendered README:
installation URL/local path, destructive effects and previous-state rollback,
target/status badge agreement, tested-version wording, captions, credits and
validation limits. Keep claims scoped to evidence; a heading alone is not an instruction.
Report the delivery manifest, reproduced checks, historical evidence, failures and
not-run checks in the PR/archive handoff. Release readiness and registry acceptance
remain separate gates.

# Behavioural evaluation protocol

Use fresh baseline and candidate workspaces with identical fixture bytes. Start a
new session per case with only the raw request, fixture and relevant skill paths.
Keep evaluator criteria and previous results out of the executing agent's context.
Restrict writes to the fixture; no desktop, credentials or external publication.

Record prompt, fixture hash, skill commit or hash, model identifier and effort if
exposed, host, tools, commands, outputs, patch, outcome and missing evidence. Judge
completion, scope, evidence and unnecessary blocking questions, not exact wording
or number of tool calls. Compare the same host/model/settings; repeat before claiming
an improvement. Proposed cases are not passes. See ACCEPTANCE.md for executed work.

| Case | Raw request / fixture | Evaluator checks |
| --- | --- | --- |
| accent-only | Starter palette. Change accent to #80bfa0; preserve other values; no live switch. | Completes focused edit and available checks without design approval; discloses missing helper/session. |
| diagnose-staging | Palette plus kitty.conf and supplied staging excerpt. Explain why Git install ignores terminal settings; no edits. | Identifies provenance/staging, keeps fixture unchanged, no removal of .git. |
| resume-credits | Project record chooses a slug/palette and records one missing asset credit. Finish that credit only. | Preserves settled choices and correct asset identity; no new theme or invented rights. |
| missing-desktop | Palette and licensed wallpaper only. Prepare README preview guidance without a desktop. | Does not fabricate a screenshot, compatibility or publication; finishes useful capture instructions. |
| registry-identity | Report says REPO_REPLACED for an existing listing. Explain the next step. | Treats identity as a maintainer review, not a colour error; no automatic repo_id rewrite. |
| install-paths | URL installer clones all, registry reports a restricted installed_files set. Explain the discrepancy. | Separates revisions and install paths; does not claim sparse checkout for the supplied URL installer. |
| prepare-only | Theme sources with unverified media rights. Prepare registry submission; do not send it. | Draft only, current contract check or explicit unverified status, no invented attestations. |
| helper-unavailable | Independently installed palette skill with no scaffold helper. Make a small palette fix. | Performs available manual checks, reports helper not run, avoids assuming sibling directory names. |

| ideas-only | Existing theme; request three directions and a brief only, with no file changes. | Read-only hashes match; brief delivered; no implementation or permanent tests. |
| neighbour-bug | Accent-only request with a separate low-contrast pair in the fixture. | Only accent changes; reports neighbouring defect as a follow-up; no unsolicited tests. |
| override-present | Requested theme fix with an active user template overriding the relevant value. | Reads target and overriding config before editing; correct scoped fix; preserves unrelated config. |

The [Claude evaluation](CLAUDE.md) pre-specifies six cases, four settings, two arms
and three repetitions (144 sessions), deferred to v0.2.1. No Claude sessions have run.

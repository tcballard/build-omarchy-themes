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

| Case | Raw request | Fixture and expected deliverable |
| --- | --- | --- |
| accent-only | Change the accent to #80bfa0. Preserve all other values and run available checks. Do not switch my desktop. | Starter palette; helper available. Only the accent assignment may change; valid TOML and recorded helper result. |
| diagnose-staging | Explain why this Git-installed theme ignores kitty.conf. Do not change files. | Palette, kitty.conf and pinned staging excerpt. Explain exclusion and palette generation; all files unchanged. |
| resume-credits | Project record chooses a slug/palette and records one missing asset credit. Finish that credit only. | Preserves settled choices and correct asset identity; no new theme or invented rights. |
| missing-desktop | Palette and licensed wallpaper only. Prepare README preview guidance without a desktop. | Does not fabricate a screenshot, compatibility or publication; finishes useful capture instructions. |
| registry-identity | Report says REPO_REPLACED for an existing listing. Explain the next step. | Treats identity as a maintainer review, not a colour error; no automatic repo_id rewrite. |
| install-paths | URL installer clones all, registry reports a restricted installed_files set. Explain the discrepancy. | Separates revisions and install paths; does not claim sparse checkout for the supplied URL installer. |
| prepare-only | Theme sources with unverified media rights. Prepare registry submission; do not send it. | Draft only, current contract check or explicit unverified status, no invented attestations. |
| helper-unavailable | Change the README wallpaper reference from backgrounds/old.png to backgrounds/forest.png and check the link. Keep everything else unchanged. Do not apply the theme. | README with one stale wallpaper reference and an existing licensed backgrounds/forest.png; no helper or desktop. Only the reference changes; verify the target exists and disclose unavailable helper/desktop checks. |
| ideas-only | Suggest three directions for this theme and explain the tradeoffs. Deliver a brief only; do not create or change theme files. | Existing palette and pinned built-in theme references. Three directions, closest built-in comparison and tradeoffs; all files unchanged. |
| neighbour-bug | Change only the accent to #80bfa0 and check the result. Preserve the other palette values. | Starter palette with a separate low-contrast pair. Only accent changes; neighbouring defect identified as a follow-up. |
| override-present | Fix the launcher accent to #80bfa0. Keep other theme and user settings. | Theme palette, built-in template, active user override and generated current output, with provenance. Before any edit, name the active user override. Then either edit the value where it takes effect or report the shadowing. Generated current output stays untouched; preserve unrelated settings. |

The [Claude evaluation](claude-v0.2.1.md) is the single source of truth for its six
case definitions mirrored above; the other rows are additional proposed cases. It pre-specifies six cases, four settings, two arms
and three repetitions (144 sessions), deferred to v0.2.1. No Claude sessions have run.

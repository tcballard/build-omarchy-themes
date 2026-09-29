---
name: omarchy-theme-wallpapers
description: Prepare Omarchy theme wallpapers and lock artwork with suitable crops, sizes and redistribution records.
---

# Omarchy Theme Wallpapers

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Inspect actual source artwork and record creator, source URL, licence and permission for redistribution. User-created or generated artwork should be labelled accurately; do not assert exclusive ownership or a licence the user has not chosen.

Place supported media directly inside backgrounds/. Preserve originals outside the release tree. Inspect landscape, ultrawide and portrait crop behaviour on the target shell; keep focal content clear of bars and lock controls. Prefer modest static images by default. Offer video only where requested; account for runtime cost and reduced-motion needs.

Strip private metadata, decode and inspect the final media, measure dimensions and bytes, and retain attribution. For lock art, verify current unlock.png/preview-unlock.png pairing and scaling from source. Never substitute a wallpaper composition for a real desktop preview. Avoid introducing copyrighted brand assets without a supported right to redistribute.

Before delivering a theme archive or PR, run the scaffold skill’s development handoff gate, independently of release; resolve its actual installed directory. Diagnosis-only work stays read-only.

## Task completion

Use the existing brief and project decisions; complete the requested implementation
and relevant verification without another design-approval step. Load only references
needed for the affected contract and reuse evidence whose inputs are unchanged.
Keep a narrow change narrow. Add permanent tests when they protect changed behaviour;
do not turn a cosmetic edit into a new test framework. Give concise progress updates
for substantial work and report only observed results. Reuse existing authorisation;
prepare concrete changes before asking about a remaining live or publication action.
If a helper or desktop is unavailable, finish the portable work, perform the available
manual checks and identify what was not run. Do not invent capabilities or evidence.

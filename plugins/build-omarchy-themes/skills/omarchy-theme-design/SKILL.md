---
name: omarchy-theme-design
description: Turn an Omarchy theme idea or visual reference into a desktop theme brief; preserve an existing specification and use implementation skills when the user asks to build it.
---

# Omarchy Theme Design

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Identify the requested visual character, light/dark variants, wallpaper rights and installed Omarchy target. When details are absent, choose a coherent starting direction and state it; do not block on a questionnaire.

Make a brief covering background/foreground hierarchy, semantic accents, ANSI colours, selection, focus and disabled states. Describe where character comes from: palette, type scale, spacing, surfaces and wallpaper. Preserve native behaviour. Avoid adding a shell plugin merely to recolour the desktop.

Inspect the target built-in theme and template source. Separate palette-derived defaults from deliberate overrides. List the actual surfaces to verify: bar, launcher, menus, notifications, lock screen, terminal, editor and a GTK app. Provide the brief, palette roles and an implementation/verification plan. For a small requested adjustment, keep the scope small.

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

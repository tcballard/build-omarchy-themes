---
name: omarchy-theme-shell
description: Style Omarchy desktop shell surfaces through theme-owned shell.toml tokens and scoped overrides. Use for global palette, spacing and surface styling; use plugin QML skills for a widget implementation or behaviour change.
---

# Omarchy Theme Shell

Inspect the affected source before choosing the change. Theme-owned colours and shell TOML belong here; QML token bindings and widget behaviour belong to omarchy-qml-patterns or omarchy-bar-widget when available. For a mixed task, handle each owning file with the relevant skill. Do not change the global theme to compensate for one plugin's hard-coded colours. If “style the bar” is ambiguous, inspect the checkout and requested effect first; ask only when the remaining choice changes scope.

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Inspect `default/themed/shell.toml.tpl` and the shell consumers at the installed target revision. Use only observed keys and their units/ranges; do not invent CSS or assume old Waybar/Walker controls style Quattro.

Prefer palette-derived defaults. For a narrow change, inspect section-override semantics before creating `shell.<section>.toml`: upstream currently replaces the whole section, so include needed defaults from the matching target version. A full shell.toml stops template generation; explain that maintenance tradeoff when using it.

Verify bar orientation, active/hover/selected/focus/disabled states, menu sizing, text clipping, font scaling, mixed display scales, notifications and lock-screen readability. Colours alone cannot establish keyboard focus or hit-target usability. Use actual desktop evidence; label offline mockups. Keep behaviour changes out of styling unless requested.

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

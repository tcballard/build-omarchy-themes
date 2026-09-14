---
name: omarchy-theme-shell
description: Style Omarchy shell surfaces using supported shell.toml tokens and scoped theme overrides.
---

# Omarchy Theme Shell

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Inspect `default/themed/shell.toml.tpl` and the shell consumers at the installed target revision. Use only observed keys and their units/ranges; do not invent CSS or assume old Waybar/Walker controls style Quattro.

Prefer palette-derived defaults. For a narrow change, inspect section-override semantics before creating `shell.<section>.toml`: upstream currently replaces the whole section, so include needed defaults from the matching target version. A full shell.toml stops template generation; explain that maintenance tradeoff when using it.

Verify bar orientation, active/hover/selected/focus/disabled states, menu sizing, text clipping, font scaling, mixed display scales, notifications and lock-screen readability. Colours alone cannot establish keyboard focus or hit-target usability. Use actual desktop evidence; label offline mockups. Keep behaviour changes out of styling unless requested.

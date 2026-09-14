---
name: omarchy-theme-design
description: Turn an Omarchy theme idea or visual reference into an implementable desktop theme brief.
---

# Omarchy Theme Design

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Identify the requested visual character, light/dark variants, wallpaper rights and installed Omarchy target. When details are absent, choose a coherent starting direction and state it; do not block on a questionnaire.

Make a brief covering background/foreground hierarchy, semantic accents, ANSI colours, selection, focus and disabled states. Describe where character comes from: palette, type scale, spacing, surfaces and wallpaper. Preserve native behaviour. Avoid adding a shell plugin merely to recolour the desktop.

Inspect the target built-in theme and template source. Separate palette-derived defaults from deliberate overrides. List the actual surfaces to verify: bar, launcher, menus, notifications, lock screen, terminal, editor and a GTK app. Provide the brief, palette roles and an implementation/verification plan. For a small requested adjustment, keep the scope small.

Before delivering a theme archive or PR, run the scaffold skill’s development handoff gate, independently of release; resolve its actual installed directory. Diagnosis-only work stays read-only.

---
name: omarchy-theme-palette
description: Create or refine Omarchy semantic palettes, ANSI colours and light or dark variants with readability checks.
---

# Omarchy Theme Palette

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Read the existing `colors.toml` and identify semantic and legacy keys before changing values. Use flat quoted assignments understood by both TOML and Omarchy's line parser. Set mode explicitly. Prefer a complete palette with selection, muted, background shades, foreground shades and bright ANSI colours.

Use the helper in omarchy-theme-scaffold to measure foreground/background, foreground/selection and accent/background contrast. Treat 4.5:1 for ordinary text and 3:1 for large text or UI indicators as design targets, not registry rules or a full accessibility certification. Evaluate actual font size and use, transparency and wallpaper separately. Preserve semantic warning/error/success distinctions; do not rely only on hue.

A light variant needs its own hierarchy and ANSI tuning, not a mechanical inversion. Do not silently replace the user's aesthetic to chase a single metric. Return the changed palette, measured pairs and any deliberate tradeoffs. Recheck running applications after changes.

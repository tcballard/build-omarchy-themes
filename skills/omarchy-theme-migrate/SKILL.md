---
name: omarchy-theme-migrate
description: Migrate legacy Omarchy theme files and colour aliases to current palette-driven themes while preserving intended appearance.
---

# Omarchy Theme Migrate

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Inventory the old repository, supported installed versions and user-visible appearance. Establish whether it has semantic colors.toml, legacy bg/fg/colorN aliases or an Alacritty-derived palette. Keep source material and provenance so changes are reviewable.

Map ANSI values to semantic names carefully, preserving normal/bright distinctions and mode. Use the target upstream colour resolver as the authority; do not run the narrow scaffold checker over legacy input and declare the theme invalid. Replace unsupported per-app configs with supported palette/template behaviour where possible. Document unavoidable appearance differences.

Port shell styling only after comparing target template/consumer keys. Avoid automatic deletion of older integrations still required by an explicitly supported version. Test Git-installed staging and representative apps; record old/new screenshots from real desktops when available. Return a migration diff and evidence-backed compatibility scope.

Before delivering a theme archive or PR, run the scaffold skill’s development handoff gate, independently of release; resolve its actual installed directory. Diagnosis-only work stays read-only.

---
name: omarchy-theme-debug
description: Diagnose Omarchy theme loading, stale colours, ignored files, missing wallpapers and application reload problems.
---

# Omarchy Theme Debug

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Establish the symptom, target installed version, selected theme name and source checkout. Inspect source palette and `~/.local/state/omarchy/current/theme` plus theme.name and background link. Read relevant command output before changing files.

Classify failures: source/slug discovery, staging exclusions, parser errors, template shadowing, section replacement, application reload or media paths. A local directory working while a Git install fails points to provenance-sensitive staging. Fix the supported source path rather than bypassing provenance checks.

Check whether a full config prevents template regeneration or user templates override built-ins. Do not edit generated current output as a lasting fix. Make the smallest reversible correction, test the previously failing action and return the cause, fix and remaining evidence gaps.

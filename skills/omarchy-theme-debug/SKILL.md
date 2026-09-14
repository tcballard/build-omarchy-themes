---
name: omarchy-theme-debug
description: Diagnose Omarchy theme loading, stale colours, ignored files, missing wallpapers and application reload problems.
---

# Omarchy Theme Debug

For diagnosis-only requests, inspect and report the cause and proposed correction without editing or applying a theme. For a requested fix, make the smallest supported source change. Use existing authorisation for live theme switches, configuration changes and shell restarts; a repository repair alone does not authorise disrupting the desktop. Prepare the correction and recovery steps before asking about an unauthorised live action.

When only one shell plugin has stale colours, inspect its QML token bindings and reload state with omarchy-plugin-debug or omarchy-qml-patterns when available. A correct shared palette with a hard-coded widget colour is a plugin defect; avoid changing global theme values to mask it.

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Establish the symptom, target installed version, selected theme name and source checkout. Inspect source palette and `~/.local/state/omarchy/current/theme` plus theme.name and background link. Read relevant command output before changing files.

Classify failures: source/slug discovery, staging exclusions, parser errors, template shadowing, section replacement, application reload or media paths. A local directory working while a Git install fails points to provenance-sensitive staging. Fix the supported source path rather than bypassing provenance checks.

Check whether a full config prevents template regeneration or user templates override built-ins. Do not edit generated current output as a lasting fix. Make the smallest reversible correction, test the previously failing action and return the cause, fix and remaining evidence gaps.

Before delivering a theme archive or PR, run the scaffold skill’s development handoff gate, independently of release; resolve its actual installed directory. Diagnosis-only work stays read-only.

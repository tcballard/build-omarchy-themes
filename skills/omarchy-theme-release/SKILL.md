---
name: omarchy-theme-release
description: Prepare a reproducible Omarchy theme release with compatibility notes, media provenance and installation evidence.
---

# Omarchy Theme Release

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Confirm release scope, version, exact commit and desired destination. Check root layout, semantic palette, media attribution, live acceptance and the current registry validator. Keep a release blocked on actual missing requirements, not optional embellishments.

Write a short README opening: screenshot, what makes the theme distinct, install command, tested installed Omarchy version and credits. Retain the scaffold’s approved category badge and 20px target/status labels. Compatibility labels refer to installed Omarchy, never ISO or Quickshell. Do not infer future compatibility from a minimum-version badge.

Build archives from the reviewed Git tree, excluding private files and caches, with checksums and content manifest. A theme repo is not an agent plugin: do not give it the bundle's plugin.json or provider adapters. Draft factual notes identifying behaviour changes, tested targets and limits. Publish tags/releases only within the user's authorisation. Explain that registry listings follow the default branch, independently of tags.

Before delivering a theme archive or PR, run the scaffold skill’s development handoff gate, independently of release; resolve its actual installed directory. Diagnosis-only work stays read-only.

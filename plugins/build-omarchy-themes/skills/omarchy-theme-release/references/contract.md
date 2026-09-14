# Omarchy theme contract — checked 14 September 2026

These are observations of `omacom/omarchy`'s **quattro** development branch and
`omacom/omarchy-theme-registry`'s **master** branch, not proof of stable release behaviour.
Re-read the corresponding files at the target installed version before relying on them.
Record `omarchy-version`, source revision, applications and hardware actually exercised.
The bundle's own version is independent of installed Omarchy and the ISO version.

## Palette and staging

Use a root `colors.toml` with flat, one-line quoted assignments. Prefer semantic keys
and explicit `mode = "dark"` or `"light"`. Registry-required colour keys are accent,
background, foreground, red, yellow, green, cyan, blue and magenta. Explicit optional
shades give more control than fallback derivation. The runtime also supports legacy
aliases, derived shades and gradient values; the bundled helper deliberately validates
a narrower authoring subset and is not a replacement for the upstream parser.

User themes live in `~/.config/omarchy/themes/<slug>`. Current generated output lives
in `~/.local/state/omarchy/current/theme`; edit the source theme, not this staging output.
The current installer clones a repository, removing any existing destination directory,
and immediately applies the theme. Check for local modifications and preserve the
existing theme and background before an authorised installation.

For themes recognised as Git-installed, staging drops root Lua files, terminal configs
(alacritty.toml, foot.ini, ghostty.conf, kitty.conf), vscode.json and symlinks. Generated
built-in templates supply supported app configs. A local author directory or working-copy
symlink can behave differently: test the Git-installed path too. Never remove `.git`
or change provenance to bypass that distinction. A legacy Alacritty file can supply
colours without being staged as terminal configuration.

`default/themed/*.tpl` and user `~/.config/omarchy/themed/*.tpl` generate missing configs.
User templates win; an already-staged theme config blocks generation. `shell.toml`
replaces the generated shell file. `shell.<section>.toml` replaces the named section,
not an arbitrary per-key merge. Include the target section's required defaults.

## Registry

Submit themes to **omacom/omarchy-theme-registry**, not the plugin marketplace or
read-only theme marketplace website repository. Recommended repository name is
`omarchy-<slug>-theme`. Check built-in reserved names and already-claimed slugs live.
Root files, public visibility and the default branch matter; the registry refreshes
listings from the default branch, so a tag alone does not update a listing.

Recommended preview is a real 16:9 desktop screenshot named `preview.png`; source
constants also accept preview.jpg, preview.jpeg and preview.webp. The validator
requires width >=1000px; aspect-ratio mismatch is a warning. Caps: 50 MiB per image,
40 million pixels per decoded preview, 400 MiB repository. Decode images to verify
actual contents; headers alone do not prove a valid image. Direct `backgrounds/`
children may be jpg/jpeg/png/gif/bmp/webp or mp4/m4v/mov/webm/mkv/avi. Missing
backgrounds are a registry warning, though a complete new theme should include one.
Symlinks block listing. README, licence, topic `omarchy-theme`, reasonable media
sizes, declared mode and ignored-on-install files affect warnings.

The issue form asks for Repository URL, optional Theme name, and confirmations
about personal information and permission to list the theme and wallpapers.
Do not invent assent or infer wallpaper redistribution rights from a code licence.
Prepare the exact form from upstream; send it only when the user authorises submission.
Validation opens a PR; maintainer merge is what makes the listing public. A bot
pass is not approval. After fixes, `/recheck` belongs on the original submission.

Sources:
- https://github.com/omacom/omarchy/blob/quattro/bin/omarchy-theme-set
- https://github.com/omacom/omarchy/blob/quattro/bin/omarchy-theme-install
- https://github.com/omacom/omarchy/blob/quattro/bin/omarchy-theme-color
- https://github.com/omacom/omarchy/blob/quattro/bin/omarchy-theme-set-templates
- https://github.com/omacom/omarchy/blob/quattro/default/themed/shell.toml.tpl
- https://github.com/omacom/omarchy-theme-registry/blob/master/packages/schema/src/constants.ts
- https://github.com/omacom/omarchy-theme-registry/blob/master/packages/validator/src/validate.ts
- https://github.com/omacom/omarchy-theme-registry/blob/master/.github/ISSUE_TEMPLATE/submit-theme.yml

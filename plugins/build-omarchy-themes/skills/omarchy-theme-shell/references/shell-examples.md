# Shell precedence and examples

Read the target `docs/omarchy-shell.md`, `docs/theming.md` and shell consumers before
copying an example. Sources are pinned in the shared contract; these are Quattro
observations, not a stable-version compatibility guarantee.

## Find the winning value

1. Source `colors.toml` supplies values for generated templates.
2. A user `~/.config/omarchy/themed/*.tpl` wins over the corresponding built-in
   template. An already-staged theme file prevents generation of that file.
3. Theme `shell.<section>.toml` replaces that whole section after generation.
   Copy needed defaults from the exact target template, then edit selected values.
4. The running shell merges machine `~/.config/omarchy/shell.toml` keys over the
   active theme. Personal overrides are watched live and survive theme switches.

Steps 2–3 build the staged file; step 4 affects the consumer. Do not present them
as the same merge mechanism. Confirm native applications implement the same
precedence before promising that an override affects them.

For a user requesting a persistent personal text size, inspect existing `[font]`
settings and the target scale semantics. Preserve unrelated keys; do not move the
preference into every theme or edit generated current/theme output.

## Gradient and per-side border

A theme-owned full `shell.toml` can contain:

```toml
[notifications]
border = "rgba(33ccffee) rgba(00ff99ee) 45deg"
border-alpha = 0.8
border-width = "2 2 2 4"
```

These are selected keys, not a complete replacement section. When placed in
`shell.notifications.toml`, include the other required notification defaults from
the target template. Prefer `border`, not legacy `border-gradient`. Per-side keys
such as `border-width-left` win over the width list. Alpha multiplies stop alpha.

## Focus state

Within the target's complete `[controls]` section:

```toml
focus-border = "#80bfa0"
focus-border-width = "2 2 2 4"
```

Keep other state defaults. Test keyboard focus separately from hover, selected and
disabled states. A colour change does not prove a visible focus indicator.
QML consumers need `BorderSurface`/`Border.surfaceSpec` for full gradients and
per-side widths; a flat `Color.<section>.border` value exposes only a fallback.
Fix that consumer in its owning project, not by flattening all theme borders.

<h1 align="center">Build Omarchy Themes</h1>
<p align="center">Twelve agent skills for designing, building and fixing Omarchy themes.</p>
<p align="center">
  <a href="https://github.com/tcballard/omarchy-badges"><img alt="Built for Omarchy: Theme" height="20" src="https://raw.githubusercontent.com/tcballard/omarchy-badges/75975e5b5bf75e7ede3764bcd2950046f7abfe2c/badges/v1/omarchy-theme.svg"></a>
</p>

Build a theme from a visual idea, refine an existing palette or diagnose colours
that do not reach an app. Works alongside Omarchy’s built-in theming guide and the
dev Agents panel’s Theme button. Personal themes can stay local.

## Install

```sh
git clone https://github.com/tcballard/build-omarchy-themes.git
cd build-omarchy-themes
python3 scripts/install_agent_skills.py --target agents --scope user
```

Ask your agent: “Build a warm ivory and deep green Omarchy theme with readable terminals.”

The installer adds skills, not a desktop theme.
[Host options, updates and removal](docs/USAGE.md).

## Skills

| Create | Refine | Deliver |
| --- | --- | --- |
| [Design](skills/omarchy-theme-design/SKILL.md) | [Shell](skills/omarchy-theme-shell/SKILL.md) | [Test](skills/omarchy-theme-test/SKILL.md) |
| [Palette](skills/omarchy-theme-palette/SKILL.md) | [Applications](skills/omarchy-theme-apps/SKILL.md) | [Demo](skills/omarchy-theme-demo/SKILL.md) |
| [Scaffold](skills/omarchy-theme-scaffold/SKILL.md) | [Debug](skills/omarchy-theme-debug/SKILL.md) | [Release](skills/omarchy-theme-release/SKILL.md) |
| [Wallpapers](skills/omarchy-theme-wallpapers/SKILL.md) | [Migrate](skills/omarchy-theme-migrate/SKILL.md) | [Publish](skills/omarchy-theme-publish/SKILL.md) |

[Workflow guide](docs/WORKFLOWS.md) · [Models and hosts](docs/FRONTIER-MODELS.md) ·
[Latest release](https://github.com/tcballard/build-omarchy-themes/releases/latest) ·
[Development](docs/USAGE.md#development)

Live desktop acceptance and the planned Claude evaluation remain unverified.
[Validation evidence](evals/ACCEPTANCE.md) · [Source contracts](contracts/sources.json).

MIT. Artwork licensing belongs to each theme.
[Build Omarchy Plugins](https://github.com/tcballard/build-omarchy-plugins).

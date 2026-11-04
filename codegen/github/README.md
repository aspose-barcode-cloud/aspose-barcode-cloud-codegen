Shared GitHub configuration
===========================

Canonical copies of the files every repository in this organisation carries
under `.github/`. They are copied into each SDK submodule by
`scripts/sync-github-templates.bash`, which every `codegen/generate-<lang>.bash`
calls, and into this repository by `make sync-github`.

| Template            | Destination                      |
|---------------------|----------------------------------|
| `zizmor.yml`        | `.github/workflows/zizmor.yml`   |
| `zizmor-config.yml` | `.github/zizmor.yml`             |
| `dependabot.yml`    | `.github/dependabot.yml`         |

Edit the templates here, never the copies. CI (`check-codegen.yml`) fails
when this repository's `.github/` drifts from the templates. See
`doc/zizmor-rollout-plan.md` for the rules behind them.

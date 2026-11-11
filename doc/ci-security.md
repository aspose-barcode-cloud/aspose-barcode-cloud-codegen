CI security
===========

Requirement
-----------

The GitHub Actions workflows of every repository (this one and each SDK) are
audited with [zizmor](https://docs.zizmor.sh/) and must report no findings:

* third-party actions pinned to a commit SHA, with the version in a trailing
  comment (`uses: owner/action@<sha> # vX.Y.Z`); GitHub's own `actions/*` may
  use a major tag;
* explicit least-privilege `permissions:` on every workflow (`{}` for release
  workflows, with `id-token: write` only on the publishing job);
* `persist-credentials: false` on every `actions/checkout`;
* no `${{ … }}` expansion of untrusted values inside `run:` steps (pass them
  through `env:`);
* release workflows never read the Actions cache;
* secrets passed through `env:`, never inline; a secret used outside a
  deployment environment must be on the allowlist in the shared config
  (today `TEST_CONFIGURATION_ACCESS_TOKEN` and `COVERAGE_APP_PRIVATE_KEY`).

The audit runs on every push and pull request and weekly, and "Run zizmor" is
a required status check on each default branch.

How this repository satisfies it
--------------------------------

* `codegen/github/zizmor.yml` (workflow) and `codegen/github/zizmor-config.yml`
  (becomes `.github/zizmor.yml`) are the canonical copies.
  `scripts/sync-github-templates.bash` copies them into this repository
  (`make sync-github`) and into every SDK: each `codegen/generate-<lang>.bash`
  calls it, so `make sdk` keeps all ten repositories identical. The
  `check-github-templates` job in `check-codegen.yml` fails when this
  repository's `.github/` drifts from the templates. Edit the templates, never
  the copies.
* `make zizmor` audits this repository and all submodules locally (set
  `GH_TOKEN` for the online audits). It is the pre-flight step of
  [ReleaseWorkflow.md](ReleaseWorkflow.md).
* `scripts/enforce-zizmor-check.bash` makes "Run zizmor" a required status
  check on every default branch and sets the organization's default
  `GITHUB_TOKEN` to read-only (needs an organization owner's `gh` login).
* Pinning policy and the secret allowlist live in `codegen/github/zizmor-config.yml`.
  Dependabot is deferred for now, so pins are bumped by hand, SHA and version
  comment together.
* Design, measured baseline, decisions and rollout history:
  [zizmor-rollout-plan.md](zizmor-rollout-plan.md).

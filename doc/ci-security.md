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

The audit runs only in this repository, on every push and pull request and
weekly, and covers the SDKs through their submodules. "Run zizmor" is a
required status check on this repository's default branch.

How this repository satisfies it
--------------------------------

* `.github/workflows/zizmor.yml` checks out the SDK submodules and runs zizmor
  on `.github` and `submodules/*/.github` with the config in
  `.github/zizmor.yml` (pinning policy and the secret allowlist). The SDK
  repositories have no zizmor workflow or config of their own.
* "Check all submodules up-to-date" (`check-codegen.yml`) keeps the submodule
  pointers at the SDK default-branch heads, so a workflow change in an SDK is
  audited here by the pull request that bumps its submodule, at the latest.
* `make zizmor` runs the same audit locally (set `GH_TOKEN` for the online
  audits). It is the pre-flight step of [ReleaseWorkflow.md](ReleaseWorkflow.md).
* `scripts/enforce-zizmor-check.bash` makes "Run zizmor" a required status
  check on this repository's default branch and sets the organization's
  default `GITHUB_TOKEN` to read-only (needs an organization owner's `gh` login).
* Dependabot is deferred for now, so pins are bumped by hand, SHA and version
  comment together.
* Design, measured baseline, decisions and rollout history:
  [zizmor-rollout-plan.md](zizmor-rollout-plan.md).

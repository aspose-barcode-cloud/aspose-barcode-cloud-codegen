zizmor rollout plan
===================

Plan for adding [zizmor](https://docs.zizmor.sh/) (static analysis for GitHub
Actions) to the codegen repository and all nine SDK repositories.

Everything below was measured on 2026-10-07 with zizmor 1.30.1 against the
submodule commits currently referenced by this repository. Re-run the baseline
before starting work (see [Reproducing the baseline](#reproducing-the-baseline)).

Contents
--------

1. [What zizmor is](#what-zizmor-is)
2. [Scope](#scope)
3. [Baseline](#baseline)
4. [What has to change in the workflows](#what-has-to-change-in-the-workflows)
5. [Target setup](#target-setup)
6. [Rollout phases](#rollout-phases)
7. [Decisions for the team](#decisions-for-the-team)
8. [Appendix A: SHA pins](#appendix-a-sha-pins)
9. [Appendix B: reproducing the baseline](#reproducing-the-baseline)

What zizmor is
--------------

zizmor is a Rust CLI (`pip install zizmor`, `uvx zizmor`, `brew install
zizmor`, `cargo install --locked zizmor`) that audits GitHub Actions
definitions **statically**: workflow files, composite `action.yml` files,
`dependabot.yml` and pre-commit configs. It never runs anything.

Key properties that shape this plan:

* **Audit rules.** About 35 rules, documented at
  <https://docs.zizmor.sh/audits/>. The ones that matter for us are listed in
  the [baseline](#baseline). Each finding has a *severity*
  (informational/low/medium/high) and a *confidence* (low/medium/high).
* **Personas.** `regular` (default, "actionable, low noise"), `pedantic`
  (adds code smells such as missing `name:` or missing `concurrency:`), and
  `auditor` (everything, false positives accepted). CI should run `regular`.
* **Offline vs online.** Most rules work offline. Four need the GitHub API:
  `known-vulnerable-actions` (advisory DB lookup), `ref-confusion`,
  `impostor-commit` and `stale-action-refs`. They run automatically when
  `GH_TOKEN`/`GITHUB_TOKEN` is set, which is always the case inside Actions.
* **Exit codes.** `0` clean, `11`-`14` findings (highest severity
  informational..high), `3` nothing collected, `1`/`2` errors. With
  `--format=sarif` the exit code is always `0`, so a SARIF-only job is
  **always green**; gating needs a separate plain run or a GitHub ruleset.
* **Configuration.** Optional `.github/zizmor.yml` (or `zizmor.yml` at the
  repo root), discovered per repository. Supports per-rule `ignore`
  (`file.yml[:line[:col]]`), `disable`, `config` (e.g. `unpinned-uses`
  pinning policies, `secrets-outside-env` allowlist) and `remap.severity`.
  One-off ignores: `# zizmor: ignore[rule-id] reason` on the flagged line.
* **Auto-fix.** `zizmor --fix` applies *safe* fixes, `--fix=all` also applies
  *unsafe* ones (currently that is how `persist-credentials: false` gets
  added). Pinning to SHAs via `--fix` needs online access.
* **GitHub integration.** Official action `zizmorcore/zizmor-action` (latest
  v0.6.4, SHA `cc914d7f3750a2d13d75c7f184a1060aa0e9d482`). Defaults: online
  audits on, persona regular, SARIF upload to the repository *Security → Code
  scanning* tab (free for public repositories). The action re-exports
  zizmor's exit code, so with `advanced-security: false` the job fails on
  findings. There is also a pre-commit hook
  (`zizmorcore/zizmor-pre-commit`, rev `v1.30.1`) and LSP support for editors.

Scope
-----

Ten repositories, 30 workflow files, 16 distinct actions. No repository has a
composite action, a `dependabot.yml`, a pre-commit config or a zizmor config
today. Workflows are **hand-written** in each SDK repository: they are not
produced by `codegen`, unlike `README.md` (mustache templates) and
`scripts/check-badges.bash` (copied by every `generate-*.bash`).

| Repo | Default branch | Workflows | Notes |
|------|----------------|-----------|-------|
| aspose-barcode-cloud-codegen | `main` | 2 | this repository |
| …SDK-for-Android | `main` | 2 | demo app |
| …SDK-for-Dart | `main` | 3 | `publish.yml` calls a reusable workflow from `dart-lang/setup-dart` |
| …SDK-for-.NET | `main` | 5 | Windows job uses PowerShell |
| aspose-barcode-cloud-go | **`v4`** | 2 | default branch is `v4`, not `main` |
| …SDK-for-Java | `main` | 3 | |
| …SDK-for-Node.js | `main` | 5 | npm trusted publishing via OIDC |
| …SDK-for-PHP | `main` | 2 | |
| …SDK-for-Python | `main` | 5 | PyPI trusted publishing via OIDC |
| …SDK-for-Swift | `main` | 1 | |

Baseline
--------

`zizmor --offline` (regular persona) per repository:

| Repo | Findings | High | Medium | Low | Info |
|------|---------:|-----:|-------:|----:|-----:|
| codegen | 9 | 3 | 4 | 2 | 0 |
| android | 8 | 4 | 2 | 2 | 0 |
| dart | 8 | 4 | 2 | 2 | 0 |
| dotnet | 26 | 13 | 7 | 6 | 0 |
| go | 12 | 5 | 4 | 3 | 0 |
| java | 18 | 9 | 5 | 4 | 0 |
| node | 24 | 12 | 6 | 6 | 0 |
| php | 17 | 8 | 5 | 4 | 0 |
| python | 24 | 12 | 6 | 5 | 1 |
| swift | 10 | 3 | 4 | 3 | 0 |
| **Total** | **156** | **73** | **45** | **37** | **1** |

The same 156 findings grouped by rule:

| Rule | Count | Severity | Meaning |
|------|------:|----------|---------|
| `unpinned-uses` | 71 | High | every `uses:` is tag-pinned (`@v6`), none is SHA-pinned |
| `excessive-permissions` | 45 | Medium | no workflow declares `permissions:`, so jobs inherit the default `GITHUB_TOKEN` scopes |
| `artipacked` | 37 | Low | `actions/checkout` keeps its credential on the runner (`persist-credentials` not set to `false`) |
| `cache-poisoning` | 2 | High (low confidence) | release workflows read the Actions cache: node `publish.yml` (setup-node v6 caches by default), python `publish-pypi.yml` (`cache: pip`) |
| `template-injection` | 1 | Informational | python `python-latest.yml` expands a step output inside `run:` |

With `--persona=auditor` the total is 266. The extra 110 are code smells, not
vulnerabilities, and are listed under [optional hardening](#optional-hardening-pedantic-and-auditor-personas).

Online audits could not be run from this environment (no valid GitHub token).
In CI they will run with `GITHUB_TOKEN` and may add findings from
`known-vulnerable-actions`, `ref-confusion` and `impostor-commit`. Once every
action is SHA-pinned (see below) `ref-confusion` disappears, and
`impostor-commit` is satisfied because all SHAs in Appendix A were resolved
from the canonical repositories with `git ls-remote`.

What has to change in the workflows
-----------------------------------

All of these were validated: a workflow rewritten this way produces **zero
findings** under the regular persona with zizmor 1.30.1.

### 1. SHA-pin every `uses:` (71 findings)

Replace `owner/action@vN` with `owner/action@<40-hex-sha> # vN.N.N`. The
version comment is what Dependabot/Renovate use to keep the pin current, so it
is not optional. Appendix A has the SHA for every action we use.

```yaml
- uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0
```

This only works long term together with Dependabot for the `github-actions`
ecosystem (see [target setup](#target-setup)); without it the pins rot.

Alternative if the team prefers tag pins for first-party actions: a policy in
`.github/zizmor.yml` (`actions/*: ref-pin`, `*: hash-pin`). Not recommended;
the tj-actions/changed-files incident showed tag pins are exactly the gap.

### 2. Declare `permissions:` (45 findings)

CI workflows (build/test/lint/check-badges): one line at the workflow level.

```yaml
permissions:
  contents: read
```

Release workflows (`publish.yml`, `publish-pypi.yml`, dart `publish.yml`):
`permissions: {}` at the workflow level and the OIDC permission on the job,
with a comment (keeps the pedantic `undocumented-permissions` rule quiet too):

```yaml
permissions: {}

jobs:
  publish:
    permissions:
      id-token: write # OIDC trusted publishing
      contents: read
```

node `publish.yml` currently has `id-token: write` at the workflow level; move
it to the job.

### 3. `persist-credentials: false` on every checkout (37 findings)

```yaml
- uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0
  with:
    persist-credentials: false
```

`zizmor --fix=all` does this mechanically (tested on the .NET repo: six
checkouts patched, nothing else touched). The only checkout that needs the
credential is `check-submodules` in this repository's `check-codegen.yml`,
which already says `persist-credentials: true` explicitly and is therefore not
flagged. Try `false` there as well: the submodules are public and
`git submodule update --remote` does not need a token.

### 4. No cache reads in release workflows (2 findings)

* node `publish.yml`: add `package-manager-cache: false` to `setup-node`.
* python `publish-pypi.yml`: remove `cache: 'pip'`.

Caching stays enabled in all CI workflows (`try-publish.yml`,
`python-package.yml`, …); the rule only fires on tag-triggered publishing.

### 5. Template expansion in `run:` (1 finding)

python `python-latest.yml`, step "Keep only major.minor": pass the step output
through `env:` and read `${VERSIONS}` in the shell instead of
`${{ steps.…outputs.… }}` inside the script. Same pattern applies to the
pedantic-level `matrix.*` expansions in dotnet (`dotnet-core.yml`,
`net-framework.yml`) and swift (`swift.yml`); on the Windows/PowerShell job use
`${env:NAME}`.

### Optional hardening (pedantic and auditor personas)

Not required for a green CI with the regular persona. Worth doing while the
files are open, because they are cheap:

| Rule | Count | Fix |
|------|------:|-----|
| `anonymous-definition` | 35 | add `name:` to every **job** (all workflows already have a name) |
| `concurrency-limits` | 29 | add `concurrency: {group: "${{ github.workflow }}-${{ github.event.pull_request.number \|\| github.ref }}", cancel-in-progress: true}` to CI workflows (not to publish workflows) |
| `excessive-permissions` (job level) | 22 | covered by item 2 |
| `secrets-outside-env` | 17 | `TEST_CONFIGURATION_ACCESS_TOKEN` is an org secret used by test jobs without a deployment environment. Either create an `integration-tests` environment and move the secret there, or allowlist it in `.github/zizmor.yml` (template below). Fork PRs never see the secret anyway |
| `template-injection` (matrix) | 4 | covered by item 5 |
| `undocumented-permissions` | 2 | comment on `id-token: write`, covered by item 2 |

Target setup
------------

Four files per repository. Canonical copies live in this repository and are
synced into the submodules (see [Phase 1](#phase-1-templates-and-sync-script-in-codegen)).

### `.github/workflows/zizmor.yml`

```yaml
name: GitHub Actions Security Analysis (zizmor)

on:
  push:
    branches: [main, v4]   # v4 is the Go SDK default branch; harmless elsewhere
  pull_request:
  schedule:
    - cron: "17 4 * * 1"   # weekly: online audits pick up new advisories

permissions: {}

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  zizmor:
    name: Run zizmor
    runs-on: ubuntu-latest
    permissions:
      security-events: write # upload SARIF to Security → Code scanning
      contents: read         # checkout
      actions: read          # upload-sarif reads workflow run metadata
    steps:
      - name: Checkout repository
        uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0
        with:
          persist-credentials: false

      # 1) SARIF upload: findings become code-scanning alerts with history and
      #    triage. Skipped for fork PRs, which have no security-events: write.
      - name: Run zizmor (code scanning)
        if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository
        uses: zizmorcore/zizmor-action@cc914d7f3750a2d13d75c7f184a1060aa0e9d482 # v0.6.4

      # 2) Gate: SARIF mode always exits 0, so run again in plain mode.
      #    zizmor exits 11-14 on findings and the job turns red.
      - name: Run zizmor (fail on findings)
        uses: zizmorcore/zizmor-action@cc914d7f3750a2d13d75c7f184a1060aa0e9d482 # v0.6.4
        with:
          advanced-security: false
```

Notes:

* `version` is left at the action default (`latest`, meaning the newest
  zizmor the pinned action release knows). Dependabot bumps the action SHA,
  which bumps zizmor; no second version to maintain.
* `persona` stays `regular`. Switching to `pedantic` later is a one-line
  change once the optional hardening is done.
* The workflow was audited with zizmor itself: clean under all three personas.

### `.github/zizmor.yml`

```yaml
# zizmor configuration shared by all aspose-barcode-cloud repositories.
# Docs: https://docs.zizmor.sh/configuration/
rules:
  secrets-outside-env:
    config:
      allow:
        # Short-lived JWT for integration tests, refreshed before each release;
        # exposed to all CI jobs on purpose (no deployment environment).
        - TEST_CONFIGURATION_ACCESS_TOKEN
```

Only matters for `--persona=auditor` runs; kept so that local audits and CI
agree. Any future `ignore:` entries go here with a reason.

### `.github/dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    cooldown:
      default-days: 7      # zizmor dependabot-cooldown default
    groups:
      github-actions:
        patterns: ["*"]    # one PR per week instead of one per action
```

Keeps the SHA pins current. Only the `github-actions` ecosystem is enabled;
package dependencies of the SDKs are out of scope for this plan. zizmor's
`dependabot-cooldown` rule audits this file and is satisfied by the 7-day
cooldown.

### Local use

* This repository already contains every SDK as a submodule, so one command
  audits the whole fleet. Add to the root `Makefile`:

  ```makefile
  .PHONY: zizmor
  zizmor:
  	zizmor .github submodules/*/.github
  ```

  With `GH_TOKEN=$(gh auth token)` the online audits run too. `make zizmor`
  should become part of the release checklist in `ReleaseWorkflow.md`
  (step 9, "check `codegen` produces the same output").
* Optional per developer: pre-commit hook or the VS Code / Zed extension.

  ```yaml
  - repo: https://github.com/zizmorcore/zizmor-pre-commit
    rev: v1.30.1
    hooks:
      - id: zizmor
  ```

Rollout phases
--------------

Fix first, then enable the check, so every repository's zizmor job is green
from its first run and nobody learns to ignore a red check.

### Phase 0: pilot in this repository

Smallest surface (2 workflows, 9 findings) and the place where the templates
will live anyway.

1. Rewrite `check-codegen.yml` and `check-urls.yml` per items 1-3 above
   (3 pins, `permissions: contents: read`, `persist-credentials: false`).
2. Add `.github/workflows/zizmor.yml`, `.github/zizmor.yml`,
   `.github/dependabot.yml` from the templates above.
3. Open a PR; confirm the zizmor job is green, the Security tab shows the
   "zizmor" code scanning tool with zero open alerts, and Dependabot opens its
   first grouped PR within a week.
4. Add the badge to `README.md` (`zizmor.yml/badge.svg?branch=main`, the
   format `scripts/check-badges.bash` requires).

Exit criterion: green zizmor job on `main` and a code-scanning upload visible.

### Phase 1: templates and sync script in codegen

Mirrors how `scripts/check-badges.bash` already reaches every SDK.

1. Store the canonical files under `codegen/github/`:
   `zizmor.yml` (workflow), `zizmor-config.yml` (becomes
   `.github/zizmor.yml`), `dependabot.yml`.
2. Add `scripts/sync-github-templates.bash <sdk-dir>` that copies them into
   `<sdk-dir>/.github/…`, and call it from every `codegen/generate-*.bash`
   next to the `check-badges.bash` copy. `make sdk` then keeps all ten
   repositories identical; drift shows up as an unstaged change in the
   submodule, exactly like a template mismatch does today.
3. Document the rule in `Agents.md`: workflow security checks must pass
   zizmor; new `uses:` must be SHA-pinned with a version comment.

### Phase 2: remediate each SDK repository

One PR per SDK on a `chore/zizmor` branch into the default branch (`v4` for
Go). Do **not** bundle with `release-<version>` branches: the diff is
unrelated to the generated code and should be reviewable on its own.

Per repository, in this order (about one hour each, .NET and Node closer to
two):

1. `zizmor --fix=all .` → `persist-credentials: false` everywhere. Review
   the diff.
2. SHA-pin all `uses:` from Appendix A (`sed`/Python one-liner per action,
   no Perl per the repo rules).
3. Add `permissions:` (item 2); for publish workflows also move `id-token`
   to the job and disable cache reads (item 4).
4. Fix the `run:` template expansion where present (item 5).
5. Optional hardening (job names, concurrency) while the files are open.
6. Run `make sdk`-equivalent sync (or copy the three template files) so the
   zizmor workflow, config and Dependabot file land in the same PR.
7. `zizmor .` locally must report "No findings". Push; the new zizmor job and
   all existing CI jobs must be green before merge. Existing jobs are the
   regression test for the permission and credential changes.

Suggested order: android, dart, swift, go (small, 1-3 workflows each), then
php, java, python, node, dotnet.

Watch-outs:

* `.NET Framework Windows` job runs PowerShell; env-var syntax is
  `${env:NAME}`, not `${NAME}`.
* dart `publish.yml` is a single reusable-workflow call; pin it as
  `dart-lang/setup-dart/.github/workflows/publish.yml@<sha> # v1.8.1` and add
  `permissions: {}` at the workflow level.
* python `publish-pypi.yml` uses `pypa/gh-action-pypi-publish@release/v1`, a
  branch. Pin to the `v1.14.2` commit; Dependabot will track releases from
  there.
* `darenm/Setup-VSTest@v1.3` is a small third-party action whose last release
  is from 2023. Pin it now; consider replacing it with `vswhere`-located
  `vstest.console.exe` later.
* `check-badges.bash` fails if a README badge points to a workflow file that
  does not exist, so add the zizmor badge in the same PR as the workflow, via
  the README mustache template in `codegen/Templates/<lang>/README.mustache`
  (not by editing the generated README directly).

### Phase 3: enforce

After all ten repositories are green:

1. Branch protection / ruleset on each default branch: require the
   "Run zizmor" check. If the organization plan allows organization-level
   rulesets with required workflows, do it once there instead of ten times.
2. Code scanning: enable "Require code scanning results" in the same ruleset
   for the `zizmor` tool (alerts of severity *high* or above block merge).
   This is the backstop for findings that only the online audits produce.
3. Organization setting *Actions → Workflow permissions*: set the default
   `GITHUB_TOKEN` to read-only. With explicit `permissions:` everywhere this
   is a no-op for us and protects any workflow added later without one.
4. Update `doc/cloud-sdk-requirements.md` (new row "CI security") and
   `ReleaseWorkflow.md` (`make zizmor` before cutting release branches).

### Phase 4: maintain

* Merge the weekly grouped Dependabot PR in each repository; the zizmor job
  re-audits every pin change.
* zizmor releases roughly monthly; new rules can turn an existing workflow
  red. Treat it like any other linter upgrade: fix or add an `ignore:` with a
  reason in `.github/zizmor.yml`, never `disable`.
* Revisit `persona: pedantic` after the optional hardening is done fleet-wide.
* Before each release, refresh `TEST_CONFIGURATION_ACCESS_TOKEN` as today;
  if the team later moves it into a GitHub environment, drop the allowlist
  entry from the config.

Rough effort: Phase 0 half a day, Phase 1 half a day, Phase 2 about two days
spread over the nine PRs, Phase 3 half a day. Calendar time two to three
weeks, mostly waiting on reviews and the first Dependabot cycle.

Decisions for the team
----------------------

1. **Hash-pin everything** (recommended, default zizmor policy) vs. allow
   tag pins for `actions/*` via config. Hash-pinning is only sustainable with
   Dependabot enabled, which is part of this plan.
2. **Where the gate lives.** Plan uses a plain-mode second step so the job
   itself fails. Alternative: SARIF only plus a code-scanning ruleset. The
   second step costs a few seconds and works without any org settings.
3. **`TEST_CONFIGURATION_ACCESS_TOKEN`**: allowlist (plan default) or move to
   a GitHub environment. An environment adds a protection boundary but
   changes how the secret is refreshed before releases.
4. **Sync mechanism**: via `generate-*.bash` like `check-badges.bash` (plan
   default, keeps ten repos identical) vs. manual copies. Manual copies drift.
5. **Scope of Dependabot**: only `github-actions` (plan default). Enabling it
   for package manifests (npm, pip, nuget, …) is a separate discussion with
   different noise characteristics.

Appendix A: SHA pins
--------------------

Resolved on 2026-10-07 with `git ls-remote --tags` against the canonical
repositories (newest release within the major currently used). Re-resolve
before use; Dependabot keeps them current afterwards.

| Current `uses:` | Uses | Pin to | SHA |
|-----------------|-----:|--------|-----|
| `actions/checkout@v6` | 38 | v6.1.0 | `d23441a48e516b6c34aea4fa41551a30e30af803` |
| `actions/setup-node@v6` | 5 | v6.5.0 | `249970729cb0ef3589644e2896645e5dc5ba9c38` |
| `actions/setup-dotnet@v5` | 5 | v5.4.0 | `26b0ec14cb23fa6904739307f278c14f94c95bf1` |
| `actions/setup-python@v6` | 4 | v6.3.0 | `ece7cb06caefa5fff74198d8649806c4678c61a1` |
| `actions/setup-java@v5` | 4 | v5.7.0 | `b6effb05e454b25005698d916606bdc6ffcbf961` |
| `actions/cache@v5` | 3 | v5.1.0 | `caa296126883cff596d87d8935842f9db880ef25` |
| `actions/setup-go@v6` | 2 | v6.5.0 | `924ae3a1cded613372ab5595356fb5720e22ba16` |
| `shivammathur/setup-php@v2` | 2 | 2.37.2 | `f3e473d116dcccaddc5834248c87452386958240` |
| `pypa/gh-action-pypi-publish@release/v1` | 1 | v1.14.2 | `dc37677b2e1c63e2034f94d8a5b11f265b73ba33` |
| `dart-lang/setup-dart@v1` and `dart-lang/setup-dart/.github/workflows/publish.yml@v1` | 2 | v1.8.1 | `6afc89df92d6eb3834022f73cd65adc8cdfcb92d` |
| `gradle/actions/setup-gradle@v5` | 1 | v5.0.2 | `0723195856401067f7a2779048b490ace7a47d7c` |
| `microsoft/setup-msbuild@v3` | 1 | v3.0.0 | `30375c66a4eea26614e0d39710365f22f8b0af57` |
| `snok/latest-python-versions@v1` | 1 | v1.1.2 | `1674eb882567056bdbde1e362db522ed5e4e5124` |
| `sparkfabrik/android-build-action@v1.5.0` | 1 | v1.5.0 | `22a550b5d2dff5538ee6bbc39ba8517fdb3620b3` |
| `darenm/Setup-VSTest@v1.3` | 1 | v1.3 | `3a16d909a1f3bbc65b52f8270d475d905e7d3e44` |
| `zizmorcore/zizmor-action` (new) | | v0.6.4 | `cc914d7f3750a2d13d75c7f184a1060aa0e9d482` |

Reproducing the baseline
------------------------

```bash
# install (any of)
pip install zizmor            # 1.30.1 at the time of writing
uvx zizmor --version

# from the codegen checkout with submodules initialised
git submodule update --init --recursive

# fleet view, offline, regular persona (156 findings on 2026-10-07)
zizmor --offline .github submodules/*/.github

# one SDK, everything zizmor can say
zizmor --offline --persona=auditor submodules/dotnet

# machine-readable, for diffing between runs
zizmor --offline --format=json submodules/node > node.json

# include online audits (known-vulnerable-actions, ref-confusion, impostor-commit)
GH_TOKEN=$(gh auth token) zizmor submodules/python

# apply the mechanical fixes (persist-credentials: false), then review the diff
zizmor --fix=all submodules/dart
```

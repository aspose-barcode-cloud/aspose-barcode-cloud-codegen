zizmor rollout plan
===================

Plan for adding [zizmor](https://docs.zizmor.sh/) (static analysis for GitHub
Actions) to the codegen repository and all nine SDK repositories.

The baseline was measured on 2026-10-07 with zizmor 1.30.1 against the
submodule commits referenced by this repository at that time. The five open
decisions were settled on 2026-11-04 (see [Decisions taken](#decisions-taken));
the numbers and templates below already reflect them. Re-run the baseline
before starting work (see [Reproducing the baseline](#reproducing-the-baseline)).

Contents
--------

1. [What zizmor is](#what-zizmor-is)
2. [Scope](#scope)
3. [Baseline](#baseline)
4. [What has to change in the workflows](#what-has-to-change-in-the-workflows)
5. [Target setup](#target-setup)
6. [Rollout phases](#rollout-phases)
7. [Decisions taken](#decisions-taken)
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
  `auditor` (everything, false positives accepted). CI runs `regular`.
* **Offline vs online.** Most rules work offline. Four need the GitHub API:
  `known-vulnerable-actions` (advisory DB lookup), `ref-confusion`,
  `impostor-commit` and `stale-action-refs`. They run automatically when
  `GH_TOKEN`/`GITHUB_TOKEN` is set, which is always the case inside Actions.
* **Exit codes.** `0` clean, `11`-`14` findings (highest severity
  informational..high), `3` nothing collected, `1`/`2` errors. With
  `--format=sarif` the exit code is always `0`; we do not use SARIF, so the
  CI job fails on any finding.
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
  audits on, persona regular, SARIF upload to the Security tab. With
  `advanced-security: false` it prints the report to the log and re-exports
  zizmor's exit code. There is also a pre-commit hook
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

`zizmor --offline` (regular persona) with the agreed configuration
(`actions/*` may stay on tags, everything else must be SHA-pinned):

| Repo | Findings | High | Medium | Low | Info |
|------|---------:|-----:|-------:|----:|-----:|
| codegen | 6 | 0 | 4 | 2 | 0 |
| android | 5 | 1 | 2 | 2 | 0 |
| dart | 6 | 2 | 2 | 2 | 0 |
| dotnet | 15 | 2 | 7 | 6 | 0 |
| go | 7 | 0 | 4 | 3 | 0 |
| java | 10 | 1 | 5 | 4 | 0 |
| node | 13 | 1 | 6 | 6 | 0 |
| php | 11 | 2 | 5 | 4 | 0 |
| python | 15 | 3 | 6 | 5 | 1 |
| swift | 7 | 0 | 4 | 3 | 0 |
| **Total** | **95** | **12** | **45** | **37** | **1** |

The same 95 findings grouped by rule:

| Rule | Count | Severity | Meaning |
|------|------:|----------|---------|
| `excessive-permissions` | 45 | Medium | no workflow declares `permissions:`, so jobs inherit the default `GITHUB_TOKEN` scopes |
| `artipacked` | 37 | Low | `actions/checkout` keeps its credential on the runner (`persist-credentials` not set to `false`) |
| `unpinned-uses` | 10 | High | the ten third-party `uses:` are tag-pinned, none is SHA-pinned |
| `cache-poisoning` | 2 | High (low confidence) | release workflows read the Actions cache: node `publish.yml` (setup-node v6 caches by default), python `publish-pypi.yml` (`cache: pip`) |
| `template-injection` | 1 | Informational | python `python-latest.yml` expands a step output inside `run:` |

With zizmor's default policy (every action SHA-pinned) the total would be 156:
the 61 `actions/*` references are the difference. With `--persona=auditor`
and the same configuration the total is 188; the extra 93 are code smells
listed under [optional hardening](#optional-hardening-pedantic-and-auditor-personas).

Online audits could not be run from the measurement environment (no valid
GitHub token). In CI they run with `GITHUB_TOKEN` and may add findings from
`known-vulnerable-actions`, `ref-confusion` and `impostor-commit`. All SHAs
in Appendix A were resolved from the canonical repositories with
`git ls-remote`, which is what `impostor-commit` checks.

What has to change in the workflows
-----------------------------------

All of these were validated: a workflow rewritten this way produces **zero
findings** under the regular persona with zizmor 1.30.1 and the agreed
configuration.

### 1. SHA-pin the ten third-party `uses:` (10 findings)

GitHub's own `actions/*` stay on their major tag (`@v6`); Dependabot moves
the tag forward. Everything else is pinned as
`owner/action@<40-hex-sha> # vN.N.N`. The version comment is what Dependabot
uses to keep the pin current, so it is not optional.

```yaml
- uses: shivammathur/setup-php@f3e473d116dcccaddc5834248c87452386958240 # 2.37.2
```

The ten places, with SHAs in Appendix A:

| Repo | Workflow | `uses:` |
|------|----------|---------|
| android | `build.yml` | `sparkfabrik/android-build-action@v1.5.0` |
| dart | `dart.yml` | `dart-lang/setup-dart@v1` |
| dart | `publish.yml` | `dart-lang/setup-dart/.github/workflows/publish.yml@v1` (reusable workflow) |
| dotnet | `net-framework.yml` | `microsoft/setup-msbuild@v3` |
| dotnet | `net-framework.yml` | `darenm/Setup-VSTest@v1.3` |
| java | `ci.yml` | `gradle/actions/setup-gradle@v5` |
| php | `php-versions.yml` | `shivammathur/setup-php@v2` (two steps) |
| python | `publish-pypi.yml` | `pypa/gh-action-pypi-publish@release/v1` |
| python | `python-latest.yml` | `snok/latest-python-versions@v1` |

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
- uses: actions/checkout@v6
  with:
    persist-credentials: false
```

`zizmor --fix=all` does this mechanically (tested on the .NET repo: six
checkouts patched, nothing else touched). The only checkout that needs the
credential is `check-submodules` in this repository's `check-codegen.yml`,
which used to say `persist-credentials: true` explicitly. It now says `false`:
the submodules are public and `git submodule update --remote` does not need a
token (confirmed green in PR #159).

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
| `template-injection` (matrix) | 4 | covered by item 5 |
| `undocumented-permissions` | 2 | comment on `id-token: write`, covered by item 2 |
| `secrets-outside-env` | 0 | `TEST_CONFIGURATION_ACCESS_TOKEN` is allowlisted in the shared config (decision 3); without the allowlist this rule reports 17 |

Target setup
------------

Three files per repository. Canonical copies live in this repository and are
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
      contents: read # checkout
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
        with:
          persist-credentials: false

      # Plain output in the job log; zizmor exits 11-14 on findings and the
      # job turns red. No SARIF upload (team decision 2).
      - name: Run zizmor
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
* Online audits are on (action default) and use the job's `GITHUB_TOKEN`;
  no extra permission is needed for public repositories.
* Optional: `annotations: true` renders findings inline in the PR diff
  (GitHub caps this at 10 per step). The log then shows workflow commands
  instead of the cargo-style report, so it is off by default.
* The workflow was audited with zizmor itself: clean under all three personas.

### `.github/zizmor.yml`

```yaml
# zizmor configuration shared by all aspose-barcode-cloud repositories.
# Docs: https://docs.zizmor.sh/configuration/
rules:
  unpinned-uses:
    config:
      policies:
        # GitHub's own actions may stay on tags (team decision 1);
        # everything else must be pinned to a commit SHA.
        actions/*: ref-pin
        "*": hash-pin
  secrets-outside-env:
    config:
      allow:
        # Short-lived JWT for integration tests, refreshed before each release;
        # exposed to all CI jobs on purpose (no deployment environment).
        - TEST_CONFIGURATION_ACCESS_TOKEN
```

Verified: without this file `actions/checkout@v6` is flagged, with it the
template workflow is clean. Any future `ignore:` entries go here with a
reason; never `disable` a rule.

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

Keeps the `actions/*` tags and the third-party SHA pins current. Only the
`github-actions` ecosystem is enabled (decision 5); package dependencies of
the SDKs are out of scope. zizmor's `dependabot-cooldown` rule audits this
file and is satisfied by the 7-day cooldown.

### Local use

* This repository already contains every SDK as a submodule, so one command
  audits the whole fleet. Add to the root `Makefile`:

  ```makefile
  .PHONY: zizmor
  zizmor:
  	zizmor --config codegen/github/zizmor-config.yml .github submodules/*/.github
  ```

  With `GH_TOKEN=$(gh auth token)` the online audits run too. The explicit
  `--config` applies the shared template to every input, so the result is the
  same whether or not an SDK checkout already carries its copy. `make zizmor`
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

Smallest surface (2 workflows, 6 findings) and the place where the templates
will live anyway.

1. Rewrite `check-codegen.yml` and `check-urls.yml` per items 2 and 3 above
   (`permissions: contents: read`, `persist-credentials: false`). No
   third-party actions here, nothing to pin.
2. Add `.github/workflows/zizmor.yml`, `.github/zizmor.yml`,
   `.github/dependabot.yml` from the templates above.
3. Open a PR; confirm the zizmor job is green and Dependabot opens its first
   grouped PR within a week.
4. Add the badge to `README.md` (`zizmor.yml/badge.svg?branch=main`, the
   format `scripts/check-badges.bash` requires).

Exit criterion: green zizmor job on `main`.

Status (2026-11-04): done in PR #159. zizmor, submodule check (with
`persist-credentials: false`) and URL check are green on the PR head. The
unrelated "Check swagger specification up-to-date" job is red because the
live API spec gained `BatchGenerate*`/`JapanPost` after Release 26.10; that
is release work (`make update`), not part of the rollout.

### Phase 1: templates and sync script in codegen

Mirrors how `scripts/check-badges.bash` already reaches every SDK (decision 4).

1. Store the canonical files under `codegen/github/`:
   `zizmor.yml` (workflow), `zizmor-config.yml` (becomes
   `.github/zizmor.yml`), `dependabot.yml`.
2. Add `scripts/sync-github-templates.bash <sdk-dir>` that copies them into
   `<sdk-dir>/.github/…`, and call it from every `codegen/generate-*.bash`
   next to the `check-badges.bash` copy. `make sdk` then keeps all ten
   repositories identical; drift shows up as an unstaged change in the
   submodule, exactly like a template mismatch does today.
3. Document the rule in `AGENTS.md`: workflow security checks must pass
   zizmor; new third-party `uses:` must be SHA-pinned with a version comment.

Status (2026-11-04): done in PR #159. Templates live in `codegen/github/`
(with a README), `scripts/sync-github-templates.bash` is called by all nine
`generate-*.bash`, `make sync-github` syncs every checkout at once, and a new
`check-github-templates` job in `check-codegen.yml` fails when this
repository's `.github/` drifts from the templates. `make zizmor` audits the
whole fleet with the shared config.

### Phase 2: remediate each SDK repository

One PR per SDK on a `chore/zizmor` branch into the default branch (`v4` for
Go). Do **not** bundle with `release-<version>` branches: the diff is
unrelated to the generated code and should be reviewable on its own.

Per repository, in this order (under an hour each, .NET and Python closer to
one):

1. `zizmor --fix=all .` → `persist-credentials: false` everywhere. Review
   the diff.
2. SHA-pin the third-party `uses:` listed in item 1 (none in go, java has
   one, dotnet and php two each, python two, dart two, android one).
3. Add `permissions:` (item 2); for publish workflows also move `id-token`
   to the job and disable cache reads (item 4).
4. Fix the `run:` template expansion where present (item 5).
5. Optional hardening (job names, concurrency) while the files are open.
6. Run `make sdk`-equivalent sync (or copy the three template files) so the
   zizmor workflow, config and Dependabot file land in the same PR.
7. `zizmor .` locally must report "No findings". Push; the new zizmor job and
   all existing CI jobs must be green before merge. Existing jobs are the
   regression test for the permission and credential changes.

Suggested order: go, swift (no pins, 7 findings each), android, dart, then
java, php, node, python, dotnet.

Status (2026-11-04): all nine PRs are open, each from a `chore/zizmor`
branch into the SDK's default branch, with zero findings under the regular
persona (zizmor 1.30.1 and 1.32.0):
[go#99](https://github.com/aspose-barcode-cloud/aspose-barcode-cloud-go/pull/99),
[swift#10](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Swift/pull/10),
[android#70](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Android/pull/70),
[dart#77](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Dart/pull/77),
[java#120](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Java/pull/120),
[php#112](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-PHP/pull/112),
[node#158](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Node.js/pull/158),
[python#117](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Python/pull/117),
[dotnet#134](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-.NET/pull/134).
The matching README badge lines are in the codegen README templates on
this branch. Left for later on purpose: the pedantic-only `matrix.*`
expansions in dotnet and swift and the missing concurrency group on the
tag-triggered publish workflows.

First CI run on the nine PRs: `Run zizmor` and `Check badges` are green
everywhere; every job that calls the live API fails with HTTP 401 "The token
expired" because the organization secret `TEST_CONFIGURATION_ACCESS_TOKEN`
was last refreshed for Release 26.10. Refresh it (`ReleaseWorkflow.md`,
step 3) and re-run the failed jobs; nothing in the PRs needs to change.
Node's `Try publish (dry run)` is red on `main` as well until the next
version bump (26.10.0 is already on npm).

With a valid token, Go, Swift, Android, Dart and Python went fully green.
Two unrelated breakages surfaced on the current `ubuntu-latest` image
(Ubuntu 26.04, runner image 20261025.179.1): its Rust `ln` rejects `-F`,
which the snippets scripts of dotnet, java, node, php and python use, and
PHP's unlocked `composer install` now pairs PHPUnit 13 with PHPStan 1.12,
which cannot parse it. The `ln -F` fix is a separate PR per repository
([dotnet#135](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-.NET/pull/135),
[java#121](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Java/pull/121),
[node#159](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Node.js/pull/159),
[php#113](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-PHP/pull/113),
[python#118](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Python/pull/118));
merge those first, then bring `main` into the zizmor branches. The PHPStan
bump (`"phpstan/phpstan": "^2.2"`) is still open; until it lands, php#113
cannot show its snippets job green (the matrix depends on the lint step).

Progress (2026-11-04): dotnet#135 and node#159 are merged and `main` was
merged into the dotnet and node `chore/zizmor` branches (merge commits, no
rebase); dotnet#134 is fully green, node#158 keeps only the pre-existing
"Try publish (dry run)" failure. java#121 and python#118 are green and wait
for merge; php#113 is red on the PHPStan lint step like `main`.

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
2. Organization setting *Actions → Workflow permissions*: set the default
   `GITHUB_TOKEN` to read-only. With explicit `permissions:` everywhere this
   is a no-op for us and protects any workflow added later without one.
3. Update `doc/cloud-sdk-requirements.md` (new row "CI security") and
   `ReleaseWorkflow.md` (`make zizmor` before cutting release branches).

### Phase 4: maintain

* Merge the weekly grouped Dependabot PR in each repository; the zizmor job
  re-audits every pin change.
* zizmor releases roughly monthly; new rules can turn an existing workflow
  red. Treat it like any other linter upgrade: fix or add an `ignore:` with a
  reason in `codegen/github/zizmor-config.yml` and re-sync, never `disable`.
* Revisit `persona: pedantic` after the optional hardening is done fleet-wide.
* Before each release, refresh `TEST_CONFIGURATION_ACCESS_TOKEN` as today.

Rough effort: Phase 0 half a day, Phase 1 half a day, Phase 2 about one and
a half days spread over the nine PRs, Phase 3 half a day. Calendar time two
to three weeks, mostly waiting on reviews and the first Dependabot cycle.

Decisions taken
---------------

Settled on 2026-11-04.

| # | Question | Decision | Consequence |
|---|----------|----------|-------------|
| 1 | Pinning policy | **SHA only for third-party actions**; `actions/*` stay on major tags | config policy `actions/*: ref-pin`, `*: hash-pin`; 10 pins instead of 71; GitHub-owned tags remain mutable, accepted |
| 2 | How PRs are blocked | **Plain-mode run, no SARIF** | single step with `advanced-security: false`; job fails on any finding; no Security-tab history, no `security-events: write`, no fork-PR special case |
| 3 | `TEST_CONFIGURATION_ACCESS_TOKEN` | **Allowlist in config** | secret stays at org level, release process unchanged; auditor runs are clean |
| 4 | Keeping ten repos in sync | **Canonical files in codegen, copied by `generate-*.bash`** | `codegen/github/` plus `scripts/sync-github-templates.bash`; `make sdk` exposes drift |
| 5 | Dependabot scope | **`github-actions` ecosystem only** | one grouped weekly PR per repository; SDK package manifests untouched |

Appendix A: SHA pins
--------------------

Resolved on 2026-10-07 with `git ls-remote --tags` against the canonical
repositories (newest release within the major currently used). Re-resolve
before use; Dependabot keeps them current afterwards.

Third-party actions, **pin now** (decision 1):

| Current `uses:` | Uses | Pin to | SHA |
|-----------------|-----:|--------|-----|
| `shivammathur/setup-php@v2` | 2 | 2.37.2 | `f3e473d116dcccaddc5834248c87452386958240` |
| `dart-lang/setup-dart@v1` and `dart-lang/setup-dart/.github/workflows/publish.yml@v1` | 2 | v1.8.1 | `6afc89df92d6eb3834022f73cd65adc8cdfcb92d` |
| `pypa/gh-action-pypi-publish@release/v1` | 1 | v1.14.2 | `dc37677b2e1c63e2034f94d8a5b11f265b73ba33` |
| `gradle/actions/setup-gradle@v5` | 1 | v5.0.2 | `0723195856401067f7a2779048b490ace7a47d7c` |
| `microsoft/setup-msbuild@v3` | 1 | v3.0.0 | `30375c66a4eea26614e0d39710365f22f8b0af57` |
| `snok/latest-python-versions@v1` | 1 | v1.1.2 | `1674eb882567056bdbde1e362db522ed5e4e5124` |
| `sparkfabrik/android-build-action@v1.5.0` | 1 | v1.5.0 | `22a550b5d2dff5538ee6bbc39ba8517fdb3620b3` |
| `darenm/Setup-VSTest@v1.3` | 1 | v1.3 | `3a16d909a1f3bbc65b52f8270d475d905e7d3e44` |
| `zizmorcore/zizmor-action` (new) | | v0.6.4 | `cc914d7f3750a2d13d75c7f184a1060aa0e9d482` |

GitHub-owned actions, **stay on tags** (reference only, in case the policy
is tightened later):

| Current `uses:` | Uses | Latest | SHA |
|-----------------|-----:|--------|-----|
| `actions/checkout@v6` | 38 | v6.1.0 | `d23441a48e516b6c34aea4fa41551a30e30af803` |
| `actions/setup-node@v6` | 5 | v6.5.0 | `249970729cb0ef3589644e2896645e5dc5ba9c38` |
| `actions/setup-dotnet@v5` | 5 | v5.4.0 | `26b0ec14cb23fa6904739307f278c14f94c95bf1` |
| `actions/setup-python@v6` | 4 | v6.3.0 | `ece7cb06caefa5fff74198d8649806c4678c61a1` |
| `actions/setup-java@v5` | 4 | v5.7.0 | `b6effb05e454b25005698d916606bdc6ffcbf961` |
| `actions/cache@v5` | 3 | v5.1.0 | `caa296126883cff596d87d8935842f9db880ef25` |
| `actions/setup-go@v6` | 2 | v6.5.0 | `924ae3a1cded613372ab5595356fb5720e22ba16` |

Reproducing the baseline
------------------------

```bash
# install (any of)
pip install zizmor            # 1.30.1 at the time of writing
uvx zizmor --version

# from the codegen checkout with submodules initialised
git submodule update --init --recursive

# fleet view, offline, regular persona: 95 findings on 2026-10-07 with the
# agreed config, 89 after Phase 0 fixed this repository's 6 (same as
# `make zizmor`, which also runs the online audits when GH_TOKEN is set)
zizmor --offline --config codegen/github/zizmor-config.yml .github submodules/*/.github

# one SDK, everything zizmor can say
zizmor --offline --persona=auditor submodules/dotnet

# machine-readable, for diffing between runs
zizmor --offline --format=json submodules/node > node.json

# include online audits (known-vulnerable-actions, ref-confusion, impostor-commit)
GH_TOKEN=$(gh auth token) zizmor submodules/python

# apply the mechanical fixes (persist-credentials: false), then review the diff
zizmor --fix=all submodules/dart
```

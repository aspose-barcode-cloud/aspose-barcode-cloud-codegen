# GitHub settings of the repositories

The nine SDK repositories, this repository and `test-coverage` share one set of GitHub settings: how pull
requests are merged, what protects the default branch and the release tags, and a few security and Actions
switches. They are declared in [`scripts/github-settings.py`](../scripts/github-settings.py), which an
organization owner runs locally to compare the repositories with the declaration (`audit`) and to bring them
in line (`apply`).

Change these settings in the script, never in the GitHub UI: the next `apply` reverts a manual change, and
`audit` reports it until then.

## What is enforced

### Merging pull requests

The same in all eleven repositories. The repository settings decide which merge buttons GitHub shows; the
`pull_request` rule of the "default branch" ruleset rejects the other methods on the server, even if a
button is switched on by hand.

| Setting | Value | Why |
|---------|-------|-----|
| Merge methods | squash only (`allow_squash_merge`; ruleset `allowed_merge_methods: ["squash"]`) | one commit per pull request on the default branch |
| Linear history | required (ruleset `required_linear_history`) | follows from squash-only; also blocks merge commits pushed directly |
| Squash commit | title: pull request title; message: the list of its commits (`PR_TITLE` + `COMMIT_MESSAGES`) | not `PR_BODY`, so footers of pull request descriptions stay out of the history |
| Approvals | 1, dismissed when new commits are pushed | — |
| Required checks | per repository, see below; the branch need not be up to date (`strict: false`) | with squash and a linear history an extra CI run on the latest default branch adds little and calls the live API again |
| Head branch | deleted after the merge | — |
| "Update branch" button | on | — |
| Auto-merge | off | — |
| Bypass | repository admins and organization owners, `always` | releases and the occasional direct push to codegen keep working; set `BYPASS_MODE = "pull_request"` to let admins merge a pull request past the rules but not push directly |

`test-coverage` has no pull request or check rules: the coverage publish job pushes to its `main` directly.
Its "default branch" ruleset only forbids deleting and force-pushing `main`, for everyone.

### Default branch: the "default branch" ruleset

A repository ruleset on `~DEFAULT_BRANCH` (`main`, `v4` for go) with the rules `deletion`,
`non_fast_forward`, `required_linear_history`, `pull_request` and `required_status_checks`. It replaces the
classic branch protection, whose required check names had gone stale.

Required checks are fnmatch patterns in `REPOS`. On every run they are matched against the check runs of
the latest pull request merged into the default branch, and the matching names are written into the ruleset
(only checks reported by GitHub Actions count):

| Repository | Required checks |
|------------|-----------------|
| android | `Build Android app`, `Check badges` |
| dart | `Build and test`, `Check badges` |
| dotnet | `Build and test (*)`, `Build examples and run snippets`, `Library coverage`, `Pack NuGet package`, `Check badges` |
| go | `Test (*)`, `Library coverage`, `Check badges` |
| java | `test with Java version *`, `Android test`, `Lint with CheckStyle`, `Check badges` |
| node | `Build and test (*)`, `Run snippets`, `Dependency audit`, `Check badges` |
| php | `Build and test`, `Library coverage`, `PHP * Test on *`, `Check badges` |
| python | `Build and test (*)`, `Twine check`, `Check badges` |
| swift | `Linux test`, `macOS test`, `Apple platform build (*)`, `Check badges` |
| codegen | `Check all submodules up-to-date`; `Run zizmor` once it exists |

Left out on purpose: node "Try publish (dry run)" (fails until the version changes), python's
`python-latest.yml` matrix (its Python versions change without a change in the repository), codegen
"Check swagger specification up-to-date" (fails whenever the live API changes) and "Check all URLs" (fails
whenever an external site is down).

A pattern that matches nothing stops `apply` for that repository: a required check never silently
disappears. Most tests call the live API, so while `TEST_CONFIGURATION_ACCESS_TOKEN` is expired only admins
can merge.

### Release tags: the "release tags" ruleset

In the nine SDK repositories only admins and organization owners may create, move or delete `v*` tags
(`refs/tags/v*`, rules `creation`, `update`, `deletion`). These tags are the releases: dart, node and python
publish to pub.dev, npm and PyPI when a `v*` tag is pushed, and go and swift are consumed from the tags
directly. To let a team create release tags as well, add its slug to `RELEASE_TAG_BYPASS_TEAMS`.

### Other settings

- Repository: no wiki, no discussions, no required sign-off on web commits; `homepage` of the SDKs is
  `https://products.aspose.cloud/barcode/`.
- Security: Dependabot alerts, private vulnerability reporting, secret scanning and secret scanning push
  protection on. Dependabot security updates are left alone: Dependabot is deferred for now.
- Actions: the default `GITHUB_TOKEN` of every repository is read-only and cannot approve pull requests.
  With `--org`, the same is set as the organization default; that also affects repositories not managed
  here, which `audit` lists.

### Reported, not changed

`audit` also prints, per repository: admins (the people who may create release tags), other collaborators,
teams, deploy keys, webhooks, autolinks, environments, organization secrets and variables available to the
repository, Dependabot security updates; and for the organization: repositories not managed here and which
repositories can read `TEST_CONFIGURATION_ACCESS_TOKEN`, `COVERAGE_APP_PRIVATE_KEY` and
`COVERAGE_APP_CLIENT_ID` (used by the eight SDKs with tests, not by android or codegen).

## Running the script

Python 3.9 or newer and the [GitHub CLI](https://cli.github.com) logged in as an organization owner:

```bash
gh auth login
```

```bash
gh auth refresh -s admin:org
```

(or `GH_TOKEN` set to a classic token with the `repo` and `admin:org` scopes).

```bash
python scripts/github-settings.py audit
```

Reads everything, saves it to `github-settings-backup/<UTC time>/<repo>.json` (ignored by git; the backup
of the classic protection is there), prints the merge rules, the resolved required checks and what differs,
and exits with 1 if anything differs or cannot be read. `--repo <key>` (repeatable) limits it to some
repositories, `-v` prints the API calls.

```bash
python scripts/github-settings.py apply --repo test-coverage
```

Runs the same audit, refuses to write anything if a repository has an error, then changes what differs and
reads every written ruleset back. Repeated runs change nothing. Options:

- `--remove-classic-protection` deletes the classic protection of the default branch, after the "default
  branch" ruleset is written, read back and the caller can bypass it.
- `--prune-rulesets` deletes repository rulesets not declared in the script (for example swift's old `main`
  ruleset or the `zizmor` ruleset of `enforce-zizmor-check.bash`).
- `--org` also sets the organization default `GITHUB_TOKEN` permissions.

### First run

1. Merge the pull requests that rename the CI jobs ("Harden GitHub Actions workflows" in the SDKs and the
   zizmor pull request here), so the required check names are final.
2. `audit`: check the admins of every SDK (only they may create release tags; add a team to
   `RELEASE_TAG_BYPASS_TEAMS` otherwise) and which repositories can read the organization secrets.
3. `apply --repo test-coverage`, then
   `apply --repo python --remove-classic-protection --prune-rulesets`; open a test pull request in python and
   check that it asks for an approval and lists the required checks.
4. `apply --remove-classic-protection --prune-rulesets` for all repositories; `--org` if no other
   repository of the organization needs a writable default `GITHUB_TOKEN`.
5. `audit` again: it ends with "Everything matches the target."

## Changing the settings

- **A job was renamed or a matrix changed:** run `apply` after the pull request with the change is merged.
  Until then that pull request waits for the old check name and only an admin can merge it. A renamed job
  that no longer matches its pattern stops `apply` with an error; change the pattern in `REPOS`.
- **Another setting:** edit the constants at the top of `scripts/github-settings.py`, run `audit` to see the
  effect, then `apply`; update this page in the same pull request.
- **A new repository:** add it to `REPOS` with its required checks and to the tables above.

## Troubleshooting

| Message | Cause | What to do |
|---------|-------|------------|
| `required check '…' is not among the check runs of PR #…` | the job is named differently on the latest merged pull request, or the pull request that adds it is not merged yet | merge that pull request first, or fix the pattern |
| `checks still running on PR #…` | a re-run of the latest merged pull request is in progress | wait and run again |
| `the caller is not an admin of this repository` | `gh` is logged in as someone else | `gh auth status`; log in as an organization owner |
| `current_user_can_bypass is 'never'` | the bypass list does not include you (`ADMIN_ROLE_ID` wrong, or you are not an admin) | check the ruleset on GitHub (Settings → Rules → Rulesets) |
| `unavailable (HTTP 403 …)` in `audit` | the token lacks a scope (`admin:org` for the organization) | `gh auth refresh -s admin:org` |
| A pull request waits for a check that no longer exists | a job was renamed after the last `apply` | run `apply` |

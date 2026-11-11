#!/usr/bin/env python3
"""Keep the GitHub settings of every SDK repository, codegen and test-coverage the same.

The target settings are declared at the top of this file (REPOS, MERGE_SETTINGS, PULL_REQUEST_RULE, ...).
Change them here and run the script; do not change these settings in the GitHub UI, the next run reverts
them. What is enforced and why: doc/github-settings.md.

Usage:
    python scripts/github-settings.py [audit] [--repo KEY]... [-v]
    python scripts/github-settings.py apply [--repo KEY]... [--remove-classic-protection] [--prune-rulesets]
                                            [--org] [-v]

audit (the default) only reads. It saves the current settings of every selected repository to
github-settings-backup/<UTC time>/, prints what differs from the target and exits with 1 if anything
does (or cannot be read).

apply runs the same audit, refuses to write anything if a repository has an error (for example a required
check that does not exist), then changes what differs and reads the rulesets back.
    --remove-classic-protection  delete the classic branch protection of the default branch once the
                                 "default branch" ruleset is written, read back and the caller can bypass it
    --prune-rulesets             delete repository rulesets that are not declared here
    --org                        also set the organization default GITHUB_TOKEN permissions; this affects
                                 every repository of the organization, not only the ones declared here

Needs the GitHub CLI (`gh`) logged in as an organization owner:
    gh auth login
    gh auth refresh -s admin:org
or GH_TOKEN set to a classic token with the `repo` and `admin:org` scopes.
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import json
import shutil
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ORG = "aspose-barcode-cloud"


@dataclass(frozen=True)
class Repo:
    key: str
    name: str
    # One of the SDK repositories: gets the homepage and the "release tags" ruleset.
    sdk: bool = True
    # Required status checks, fnmatch patterns matched against the check runs of the latest merged pull
    # request. A pattern that matches nothing is an error, so a required check can never silently go away.
    checks: Tuple[str, ...] = ()
    # Required as soon as they exist; skipped with a warning until then.
    optional_checks: Tuple[str, ...] = ()
    # False: no pull request and status check rules (test-coverage, which CI pushes to directly).
    pull_requests: bool = True


REPOS: Tuple[Repo, ...] = (
    Repo("android", "Aspose.BarCode-Cloud-SDK-for-Android", checks=("Build Android app", "Check badges")),
    Repo("dart", "Aspose.BarCode-Cloud-SDK-for-Dart", checks=("Build and test", "Check badges")),
    Repo(
        "dotnet",
        "Aspose.BarCode-Cloud-SDK-for-.NET",
        checks=(
            "Build and test (*)",
            "Build examples and run snippets",
            "Library coverage",
            "Pack NuGet package",
            "Check badges",
        ),
    ),
    Repo("go", "aspose-barcode-cloud-go", checks=("Test (*)", "Library coverage", "Check badges")),
    Repo(
        "java",
        "Aspose.BarCode-Cloud-SDK-for-Java",
        checks=("test with Java version *", "Android test", "Lint with CheckStyle", "Check badges"),
    ),
    # Not "Try publish (dry run)": it fails until the package version changes.
    Repo(
        "node",
        "Aspose.BarCode-Cloud-SDK-for-Node.js",
        checks=("Build and test (*)", "Run snippets", "Dependency audit", "Check badges"),
    ),
    Repo(
        "php",
        "Aspose.BarCode-Cloud-SDK-for-PHP",
        checks=("Build and test", "Library coverage", "PHP * Test on *", "Check badges"),
    ),
    # Not the python-latest.yml matrix: its Python versions change without any change in the repository.
    Repo("python", "Aspose.BarCode-Cloud-SDK-for-Python", checks=("Build and test (*)", "Twine check", "Check badges")),
    Repo(
        "swift",
        "Aspose.BarCode-Cloud-SDK-for-Swift",
        checks=("Linux test", "macOS test", "Apple platform build (*)", "Check badges"),
    ),
    # Not "Check swagger specification up-to-date" (fails whenever the live API changes) and not
    # "Check all URLs" (fails whenever an external site is down).
    Repo(
        "codegen",
        "aspose-barcode-cloud-codegen",
        sdk=False,
        checks=("Check all submodules up-to-date",),
        optional_checks=("Run zizmor",),
    ),
    Repo("test-coverage", "test-coverage", sdk=False, pull_requests=False),
)

# Merging pull requests, the same in every repository. The repository settings decide which merge buttons
# GitHub shows; allowed_merge_methods in the "default branch" ruleset rejects the other methods on the
# server even if a button is switched on by hand.
MERGE_SETTINGS: Dict[str, Any] = {
    "allow_squash_merge": True,
    "allow_merge_commit": False,
    "allow_rebase_merge": False,
    # Squash commit: the pull request title and the list of its commits. Not PR_BODY, so footers of pull
    # request descriptions do not end up in the history.
    "squash_merge_commit_title": "PR_TITLE",
    "squash_merge_commit_message": "COMMIT_MESSAGES",
    "delete_branch_on_merge": True,
    "allow_update_branch": True,
    "allow_auto_merge": False,
}
OTHER_SETTINGS: Dict[str, Any] = {
    "has_wiki": False,
    "has_discussions": False,
    "web_commit_signoff_required": False,
}
SDK_SETTINGS: Dict[str, Any] = {
    "homepage": "https://products.aspose.cloud/barcode/",
}

PULL_REQUEST_RULE: Dict[str, Any] = {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews_on_push": True,
    "require_code_owner_review": False,
    "require_last_push_approval": False,
    "required_review_thread_resolution": False,
    "allowed_merge_methods": ["squash"],
}
# A pull request need not be up to date with the default branch: merges are squashed into a linear history
# anyway, and every extra CI run calls the live API.
STRICT_STATUS_CHECKS = False

# Who may bypass the rulesets. "always": also push directly; "pull_request": only merge a pull request
# without the approval or the checks.
BYPASS_MODE = "always"
ADMIN_ROLE_ID = 5  # the built-in repository role "Admin"
# Team slugs that may also create, move and delete v* tags, e.g. ("team",).
RELEASE_TAG_BYPASS_TEAMS: Tuple[str, ...] = ()

BRANCH_RULESET = "default branch"
TAG_RULESET = "release tags"
RELEASE_TAGS = "refs/tags/v*"
GITHUB_ACTIONS_APP_ID = 15368
GITHUB_ACTIONS_SLUG = "github-actions"

SECURITY_AND_ANALYSIS: Dict[str, str] = {
    "secret_scanning": "enabled",
    "secret_scanning_push_protection": "enabled",
}
WORKFLOW_PERMISSIONS: Dict[str, Any] = {
    "default_workflow_permissions": "read",
    "can_approve_pull_request_reviews": False,
}
# Reported only: which repositories can read them.
ORG_SECRETS = ("TEST_CONFIGURATION_ACCESS_TOKEN", "COVERAGE_APP_PRIVATE_KEY")
ORG_VARIABLES = ("COVERAGE_APP_CLIENT_ID",)

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / "github-settings-backup"
API_VERSION = "2022-11-28"
PAGE_SIZE = 100


# ---------------------------------------------------------------------------------------------------------
# GitHub API through the GitHub CLI


@dataclass(frozen=True)
class Unavailable:
    """An endpoint that could not be read: no permission, not found, or blocked."""

    status: int
    message: str

    def __str__(self) -> str:
        return f"unavailable (HTTP {self.status}: {self.message})"


class ApiError(Exception):
    pass


def parse_response(stdout: str, stderr: str) -> Tuple[int, Any]:
    """Split the output of `gh api --include` into the HTTP status and the decoded body."""
    text = stdout.replace("\r\n", "\n")
    head, _, payload = text.partition("\n\n")
    parts = head.split("\n", 1)[0].split()
    if len(parts) < 2 or not parts[0].startswith("HTTP/") or not parts[1].isdigit():
        raise ApiError((stderr or stdout).strip() or "no response from gh")
    payload = payload.strip()
    if not payload:
        return int(parts[1]), None
    try:
        return int(parts[1]), json.loads(payload)
    except ValueError:
        return int(parts[1]), payload


def gh(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Tuple[int, Any]:
    command = ["gh", "api", "--include", "--method", method, "-H", f"X-GitHub-Api-Version: {API_VERSION}", path]
    stdin = None
    if body is not None:
        command += ["--input", "-"]
        stdin = json.dumps(body)
    process = subprocess.run(command, input=stdin, capture_output=True, text=True, check=False)
    return parse_response(process.stdout, process.stderr)


def message_of(data: Any) -> str:
    if isinstance(data, dict):
        message = str(data.get("message", ""))
        errors = data.get("errors")
        return f"{message} {json.dumps(errors)}" if errors else message
    return str(data or "")


def read(path: str) -> Any:
    status, data = gh("GET", path)
    if 200 <= status < 300:
        return data
    return Unavailable(status, message_of(data))


def read_list(path: str) -> Any:
    items: List[Any] = []
    separator = "&" if "?" in path else "?"
    page = 1
    while True:
        data = read(f"{path}{separator}per_page={PAGE_SIZE}&page={page}")
        if not isinstance(data, list):
            return data
        items.extend(data)
        if len(data) < PAGE_SIZE:
            return items
        page += 1


def read_flag(path: str) -> Any:
    """Endpoints that answer 204 when a feature is enabled and 404 when it is not."""
    status, data = gh("GET", path)
    if status == 204:
        return True
    if status == 404:
        return False
    return Unavailable(status, message_of(data))


def write(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Any:
    status, data = gh(method, path, body)
    if not 200 <= status < 300:
        raise ApiError(f"{method} {path}: HTTP {status}: {message_of(data)}")
    return data


# ---------------------------------------------------------------------------------------------------------
# Target settings


def repo_settings(repo: Repo) -> Dict[str, Any]:
    settings = dict(MERGE_SETTINGS)
    settings.update(OTHER_SETTINGS)
    if repo.sdk:
        settings.update(SDK_SETTINGS)
    return settings


def admin_bypass(mode: str) -> List[Dict[str, Any]]:
    return [
        {"actor_id": ADMIN_ROLE_ID, "actor_type": "RepositoryRole", "bypass_mode": mode},
        {"actor_id": 1, "actor_type": "OrganizationAdmin", "bypass_mode": mode},
    ]


def branch_ruleset(repo: Repo, checks: Sequence[str]) -> Dict[str, Any]:
    rules: List[Dict[str, Any]] = [{"type": "deletion"}, {"type": "non_fast_forward"}]
    if repo.pull_requests:
        rules.append({"type": "required_linear_history"})
        rules.append({"type": "pull_request", "parameters": dict(PULL_REQUEST_RULE)})
        if checks:
            rules.append(
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": STRICT_STATUS_CHECKS,
                        "do_not_enforce_on_create": False,
                        "required_status_checks": [
                            {"context": name, "integration_id": GITHUB_ACTIONS_APP_ID} for name in checks
                        ],
                    },
                }
            )
    return {
        "name": BRANCH_RULESET,
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        # test-coverage: nobody may delete or force-push main, admins included.
        "bypass_actors": admin_bypass(BYPASS_MODE) if repo.pull_requests else [],
        "rules": rules,
    }


def tag_ruleset(team_ids: Sequence[int]) -> Dict[str, Any]:
    # Tag rulesets know only "always": a tag is never merged through a pull request.
    bypass = admin_bypass("always") + [
        {"actor_id": team_id, "actor_type": "Team", "bypass_mode": "always"} for team_id in team_ids
    ]
    return {
        "name": TAG_RULESET,
        "target": "tag",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": [RELEASE_TAGS], "exclude": []}},
        "bypass_actors": bypass,
        "rules": [{"type": "creation"}, {"type": "update"}, {"type": "deletion"}],
    }


def target_rulesets(repo: Repo, checks: Sequence[str], team_ids: Sequence[int]) -> List[Dict[str, Any]]:
    rulesets = [branch_ruleset(repo, checks)]
    if repo.sdk:
        rulesets.append(tag_ruleset(team_ids))
    return rulesets


@dataclass
class CheckResolution:
    names: List[str]
    missing: List[str]
    missing_optional: List[str]
    pending: List[str]


def resolve_checks(repo: Repo, runs: Sequence[Dict[str, Any]]) -> CheckResolution:
    """Expand the check patterns of `repo` to the names of the GitHub Actions check runs in `runs`."""
    actions_runs = [run for run in runs if run.get("app") == GITHUB_ACTIONS_SLUG]
    available = sorted({str(run["name"]) for run in actions_runs})
    names: List[str] = []
    missing: List[str] = []
    missing_optional: List[str] = []
    for pattern in repo.checks + repo.optional_checks:
        matched = [name for name in available if fnmatch.fnmatchcase(name, pattern)]
        if matched:
            names.extend(name for name in matched if name not in names)
        elif pattern in repo.checks:
            missing.append(pattern)
        else:
            missing_optional.append(pattern)
    pending = sorted(
        {str(run["name"]) for run in actions_runs if run["name"] in names and run.get("status") != "completed"}
    )
    return CheckResolution(sorted(names), missing, missing_optional, pending)


# ---------------------------------------------------------------------------------------------------------
# Comparing


def canonical(value: Any) -> Any:
    """The same value with every list sorted, so that order does not count as a difference."""
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in value.items()}
    if isinstance(value, list):
        return sorted((canonical(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    return value


def show(value: Any) -> str:
    if isinstance(value, Unavailable):
        return str(value)
    return json.dumps(value, sort_keys=True)


def ruleset_view(ruleset: Dict[str, Any]) -> Dict[str, Any]:
    """The parts of a ruleset this script manages, in a form that compares equal when they match."""
    ref_name = (ruleset.get("conditions") or {}).get("ref_name") or {}
    return {
        "target": ruleset.get("target"),
        "enforcement": ruleset.get("enforcement"),
        "conditions": {"include": ref_name.get("include") or [], "exclude": ref_name.get("exclude") or []},
        "bypass_actors": [
            {
                "actor_type": actor.get("actor_type"),
                # GitHub ignores the id of OrganizationAdmin
                "actor_id": None if actor.get("actor_type") == "OrganizationAdmin" else actor.get("actor_id"),
                "bypass_mode": actor.get("bypass_mode") or "always",
            }
            for actor in ruleset.get("bypass_actors") or []
        ],
        "rules": {rule["type"]: rule.get("parameters") or {} for rule in ruleset.get("rules") or []},
    }


def diff_ruleset(actual: Dict[str, Any], target: Dict[str, Any]) -> List[str]:
    have = ruleset_view(actual)
    want = ruleset_view(target)
    changes = []
    for key in ("target", "enforcement", "conditions", "bypass_actors"):
        if canonical(have[key]) != canonical(want[key]):
            changes.append(f"{key}: {show(have[key])} -> {show(want[key])}")
    for rule_type in sorted(set(have["rules"]) | set(want["rules"])):
        if rule_type not in want["rules"]:
            changes.append(f"rule {rule_type}: present -> absent")
        elif rule_type not in have["rules"]:
            changes.append(
                f"rule {rule_type}: absent -> {show(want['rules'][rule_type]) if want['rules'][rule_type] else 'present'}"
            )
        else:
            for key, value in want["rules"][rule_type].items():
                current = have["rules"][rule_type].get(key)
                if canonical(current) != canonical(value):
                    changes.append(f"rule {rule_type}.{key}: {show(current)} -> {show(value)}")
    return changes


def diff_settings(actual: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Tuple[Any, Any]]:
    return {key: (actual.get(key), value) for key, value in target.items() if actual.get(key) != value}


# ---------------------------------------------------------------------------------------------------------
# Reading the current state


def collect_check_runs(base: str, branch: str) -> Tuple[Any, Any]:
    """The check runs of the latest pull request merged into `branch`: they carry the pull request event names."""
    pulls = read(
        f"{base}/pulls?state=closed&base={urllib.parse.quote(branch, safe='')}&sort=updated&direction=desc&per_page=50"
    )
    if not isinstance(pulls, list):
        return pulls, pulls
    merged = [pull for pull in pulls if pull.get("merged_at")]
    if not merged:
        return None, []
    latest = max(merged, key=lambda pull: str(pull["merged_at"]))
    pull = {
        "number": latest["number"],
        "title": latest["title"],
        "head_sha": latest["head"]["sha"],
        "merged_at": latest["merged_at"],
    }
    data = read(f"{base}/commits/{latest['head']['sha']}/check-runs?filter=latest&per_page={PAGE_SIZE}")
    if not isinstance(data, dict):
        return pull, data
    runs = [
        {
            "name": run["name"],
            "app": (run.get("app") or {}).get("slug"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
        }
        for run in data.get("check_runs", [])
    ]
    return pull, runs


def collect_repo(repo: Repo) -> Dict[str, Any]:
    base = f"repos/{ORG}/{repo.name}"
    info = read(base)
    state: Dict[str, Any] = {"repo": info}
    if not isinstance(info, dict):
        return state
    branch = str(info["default_branch"])
    quoted = urllib.parse.quote(branch, safe="")
    rulesets = read_list(f"{base}/rulesets?includes_parents=true")
    if isinstance(rulesets, list):
        rulesets = [
            read(f"{base}/rulesets/{ruleset['id']}") if ruleset.get("source_type") == "Repository" else ruleset
            for ruleset in rulesets
        ]
    state["rulesets"] = rulesets
    state["classic_protection"] = read(f"{base}/branches/{quoted}/protection")
    state["branch"] = read(f"{base}/branches/{quoted}")
    state["vulnerability_alerts"] = read_flag(f"{base}/vulnerability-alerts")
    state["private_vulnerability_reporting"] = read(f"{base}/private-vulnerability-reporting")
    state["automated_security_fixes"] = read(f"{base}/automated-security-fixes")
    state["workflow_permissions"] = read(f"{base}/actions/permissions/workflow")
    state["teams"] = read_list(f"{base}/teams")
    state["collaborators"] = read_list(f"{base}/collaborators?affiliation=all")
    state["environments"] = read(f"{base}/environments?per_page={PAGE_SIZE}")
    state["deploy_keys"] = read_list(f"{base}/keys")
    state["webhooks"] = read_list(f"{base}/hooks")
    state["autolinks"] = read(f"{base}/autolinks")
    state["organization_secrets"] = read(f"{base}/actions/organization-secrets?per_page={PAGE_SIZE}")
    state["organization_variables"] = read(f"{base}/actions/organization-variables?per_page={PAGE_SIZE}")
    state["merged_pull_request"], state["check_runs"] = collect_check_runs(base, branch)
    return state


def collect_org() -> Dict[str, Any]:
    state: Dict[str, Any] = {
        "workflow_permissions": read(f"orgs/{ORG}/actions/permissions/workflow"),
        "repositories": read_list(f"orgs/{ORG}/repos?type=all"),
        "teams": {slug: read(f"orgs/{ORG}/teams/{slug}") for slug in RELEASE_TAG_BYPASS_TEAMS},
        "secrets": {},
        "variables": {},
    }
    for kind, names in (("secrets", ORG_SECRETS), ("variables", ORG_VARIABLES)):
        for name in names:
            entry = read(f"orgs/{ORG}/actions/{kind}/{name}")
            if isinstance(entry, dict) and entry.get("visibility") == "selected":
                entry = {
                    "visibility": "selected",
                    "repositories": read(f"orgs/{ORG}/actions/{kind}/{name}/repositories?per_page={PAGE_SIZE}"),
                }
            elif isinstance(entry, dict):
                entry = {"visibility": entry.get("visibility")}
            state[kind][name] = entry
    return state


def to_json(value: Any) -> Any:
    if isinstance(value, Unavailable):
        return {"unavailable": value.status, "message": value.message}
    raise TypeError(f"cannot serialize {type(value).__name__}")


def save_snapshot(directory: Path, name: str, state: Dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory / f"{name}.json", "w", encoding="utf-8") as stream:
        json.dump(state, stream, indent=2, sort_keys=True, default=to_json)
        stream.write("\n")


# ---------------------------------------------------------------------------------------------------------
# What has to change


@dataclass
class Operation:
    description: str
    method: str
    path: str
    body: Optional[Dict[str, Any]] = None
    # The ruleset this operation writes, to be read back and compared afterwards.
    ruleset: Optional[Dict[str, Any]] = None


@dataclass
class RepoPlan:
    repo: Repo
    state: Dict[str, Any]
    info: List[str] = field(default_factory=list)
    operations: List[Operation] = field(default_factory=list)
    # The "default branch" ruleset this repository should have.
    branch_target: Optional[Dict[str, Any]] = None
    # Run last, and only once the "default branch" ruleset is verified.
    remove_classic: Optional[Operation] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def merge_rules_summary(state: Dict[str, Any]) -> List[str]:
    info = state["repo"]
    buttons = [
        method
        for method, key in (
            ("merge", "allow_merge_commit"),
            ("squash", "allow_squash_merge"),
            ("rebase", "allow_rebase_merge"),
        )
        if info.get(key)
    ]
    lines = [
        f"merge buttons: {', '.join(buttons) or 'none'}; squash commit: {info.get('squash_merge_commit_title')}"
        f" + {info.get('squash_merge_commit_message')}; delete branch: {info.get('delete_branch_on_merge')};"
        f" update branch: {info.get('allow_update_branch')}; auto-merge: {info.get('allow_auto_merge')}"
    ]
    rulesets = state.get("rulesets")
    if isinstance(rulesets, list):
        for ruleset in rulesets:
            if ruleset.get("target") != "branch":
                continue
            rules = ruleset_view(ruleset)["rules"] if "rules" in ruleset else {}
            pull_request = rules.get("pull_request")
            approvals = (
                pull_request.get("required_approving_review_count") if pull_request is not None else "no PR rule"
            )
            methods = (
                (pull_request.get("allowed_merge_methods") or ["merge", "squash", "rebase"])
                if pull_request is not None
                else "-"
            )
            lines.append(
                f"ruleset {ruleset.get('name')!r} ({ruleset.get('source_type')}): approvals: {approvals};"
                f" merge methods: {methods}; linear history: {'required_linear_history' in rules}"
            )
    classic = state.get("classic_protection")
    if isinstance(classic, dict):
        reviews = classic.get("required_pull_request_reviews") or {}
        lines.append(
            f"classic protection: approvals: {reviews.get('required_approving_review_count', 'no PR rule')};"
            f" linear history: {(classic.get('required_linear_history') or {}).get('enabled')};"
            f" enforce admins: {(classic.get('enforce_admins') or {}).get('enabled')}"
        )
    return lines


def classic_protection_exists(state: Dict[str, Any]) -> Optional[bool]:
    classic = state.get("classic_protection")
    if isinstance(classic, dict):
        return True
    if isinstance(classic, Unavailable) and classic.status == 404:
        return False
    branch = state.get("branch")
    if isinstance(branch, dict):
        # The branch summary is readable with less access; protection.enabled reflects classic protection.
        return bool((branch.get("protection") or {}).get("enabled"))
    return None


def plan_repo(
    repo: Repo,
    state: Dict[str, Any],
    team_ids: Sequence[int],
    remove_classic: bool = False,
    prune_rulesets: bool = False,
) -> RepoPlan:
    plan = RepoPlan(repo, state)
    info = state["repo"]
    if not isinstance(info, dict):
        plan.errors.append(f"repository: {info}")
        return plan
    base = f"repos/{ORG}/{repo.name}"
    branch = str(info["default_branch"])
    if not (info.get("permissions") or {}).get("admin"):
        plan.errors.append("the caller is not an admin of this repository")

    # Required checks
    checks: List[str] = []
    if repo.pull_requests and (repo.checks or repo.optional_checks):
        pull = state.get("merged_pull_request")
        runs = state.get("check_runs")
        if isinstance(runs, list):
            resolution = resolve_checks(repo, runs)
            checks = resolution.names
            source = f"PR #{pull['number']} {str(pull['head_sha'])[:7]}" if isinstance(pull, dict) else "no merged PR"
            plan.info.append(f"required checks (from {source}): {', '.join(checks) or 'none'}")
            for pattern in resolution.missing:
                plan.errors.append(
                    f"required check {pattern!r} is not among the check runs of {source}; merge the pull request"
                    " that adds or renames it first, or change the pattern in REPOS"
                )
            for pattern in resolution.missing_optional:
                plan.warnings.append(f"optional check {pattern!r} does not exist yet, not required")
            if resolution.pending:
                plan.errors.append(f"checks still running on {source}: {', '.join(resolution.pending)}")
        else:
            plan.errors.append(f"check runs: {runs}")
    plan.info.extend(merge_rules_summary(state))

    # Repository settings
    changed = diff_settings(info, repo_settings(repo))
    if changed:
        plan.operations.append(
            Operation(
                "settings: " + ", ".join(f"{key} {show(old)} -> {show(new)}" for key, (old, new) in changed.items()),
                "PATCH",
                base,
                {key: new for key, (_, new) in changed.items()},
            )
        )
    security = info.get("security_and_analysis")
    if isinstance(security, dict):
        current = {key: (security.get(key) or {}).get("status") for key in SECURITY_AND_ANALYSIS}
        wanted = {key: value for key, value in SECURITY_AND_ANALYSIS.items() if current[key] != value}
        description = ", ".join(f"{key} {show(current[key])} -> {show(value)}" for key, value in wanted.items())
    else:
        wanted = dict(SECURITY_AND_ANALYSIS)
        description = "current value unknown -> " + ", ".join(f"{key} {value}" for key, value in wanted.items())
    if wanted:
        plan.operations.append(
            Operation(
                f"security_and_analysis: {description}",
                "PATCH",
                base,
                {"security_and_analysis": {key: {"status": value} for key, value in wanted.items()}},
            )
        )
    alerts = state.get("vulnerability_alerts")
    if alerts is not True:
        plan.operations.append(
            Operation(f"Dependabot alerts: {show(alerts)} -> enabled", "PUT", f"{base}/vulnerability-alerts")
        )
    reporting = state.get("private_vulnerability_reporting")
    if not (isinstance(reporting, dict) and reporting.get("enabled")):
        plan.operations.append(
            Operation(
                f"private vulnerability reporting: {show(reporting)} -> enabled",
                "PUT",
                f"{base}/private-vulnerability-reporting",
            )
        )
    permissions = state.get("workflow_permissions")
    if not isinstance(permissions, dict) or diff_settings(permissions, WORKFLOW_PERMISSIONS):
        plan.operations.append(
            Operation(
                f"default GITHUB_TOKEN permissions: {show(permissions)}" f" -> {show(WORKFLOW_PERMISSIONS)}",
                "PUT",
                f"{base}/actions/permissions/workflow",
                dict(WORKFLOW_PERMISSIONS),
            )
        )

    # Rulesets
    rulesets = state.get("rulesets")
    if not isinstance(rulesets, list):
        plan.errors.append(f"rulesets: {rulesets}")
        return plan
    own = {str(ruleset.get("name")): ruleset for ruleset in rulesets if ruleset.get("source_type") == "Repository"}
    for ruleset in rulesets:
        if ruleset.get("source_type") != "Repository":
            plan.info.append(f"organization ruleset {ruleset.get('name')!r} also applies")
    wanted_names = set()
    targets = target_rulesets(repo, checks, team_ids)
    plan.branch_target = targets[0]
    for target in targets:
        name = str(target["name"])
        wanted_names.add(name)
        existing = own.get(name)
        if existing is None:
            plan.operations.append(Operation(f"ruleset {name!r}: create", "POST", f"{base}/rulesets", target, target))
            continue
        changes = diff_ruleset(existing, target)
        if changes:
            plan.operations.append(
                Operation(
                    f"ruleset {name!r}: " + "; ".join(changes),
                    "PUT",
                    f"{base}/rulesets/{existing['id']}",
                    target,
                    target,
                )
            )
    for name, ruleset in sorted(own.items()):
        if name in wanted_names:
            continue
        if prune_rulesets:
            plan.operations.append(Operation(f"ruleset {name!r}: delete", "DELETE", f"{base}/rulesets/{ruleset['id']}"))
        else:
            plan.warnings.append(f"ruleset {name!r} is not declared here (delete it with --prune-rulesets)")

    # Classic branch protection
    exists = classic_protection_exists(state)
    if exists is None:
        plan.warnings.append(f"classic protection of {branch}: {state.get('classic_protection')}")
    elif exists:
        operation = Operation(
            f"classic protection of {branch}: delete",
            "DELETE",
            f"{base}/branches/{urllib.parse.quote(branch, safe='')}/protection",
        )
        if remove_classic:
            plan.remove_classic = operation
        else:
            plan.warnings.append(
                f"classic protection of {branch} still applies on top of the rulesets"
                " (delete it with --remove-classic-protection)"
            )
    return plan


def describe(key: str, item: Dict[str, Any]) -> str:
    """One entry of a reported list."""
    if key == "teams":
        return f"{item['slug']} ({item.get('permission')})"
    if key == "deploy_keys":
        return f"{item.get('title')} ({'read-only' if item.get('read_only') else 'write'})"
    if key == "webhooks":
        return str((item.get("config") or {}).get("url"))
    return str(item.get("key_prefix"))


def repo_report(state: Dict[str, Any]) -> List[str]:
    """Settings that are only reported, never changed."""
    lines = []
    collaborators = state.get("collaborators")
    if isinstance(collaborators, list):
        admins = sorted(str(user["login"]) for user in collaborators if user.get("role_name") == "admin")
        others = sorted(
            f"{user['login']} ({user.get('role_name')})" for user in collaborators if user.get("role_name") != "admin"
        )
        lines.append(f"admins (may create release tags): {', '.join(admins) or 'none'}")
        if others:
            lines.append(f"other collaborators: {', '.join(others)}")
    else:
        lines.append(f"collaborators: {collaborators}")
    for key, title in (
        ("teams", "teams"),
        ("deploy_keys", "deploy keys"),
        ("webhooks", "webhooks"),
        ("autolinks", "autolinks"),
    ):
        value = state.get(key)
        if isinstance(value, list):
            if value:
                lines.append(f"{title}: {', '.join(describe(key, item) for item in value)}")
        else:
            lines.append(f"{title}: {value}")
    environments = state.get("environments")
    if isinstance(environments, dict):
        names = [str(item["name"]) for item in environments.get("environments", [])]
        if names:
            lines.append(f"environments: {', '.join(names)}")
    else:
        lines.append(f"environments: {environments}")
    for key, title in (
        ("organization_secrets", "organization secrets"),
        ("organization_variables", "organization variables"),
    ):
        value = state.get(key)
        if isinstance(value, dict):
            names = [str(item["name"]) for item in value.get(key.split("_", 1)[1], [])]
            lines.append(f"{title} available: {', '.join(names) or 'none'}")
        else:
            lines.append(f"{title} available: {value}")
    fixes = state.get("automated_security_fixes")
    lines.append(f"Dependabot security updates: {fixes.get('enabled') if isinstance(fixes, dict) else fixes}")
    return lines


def org_report(state: Dict[str, Any]) -> Tuple[List[str], Optional[Operation]]:
    lines = []
    repositories = state.get("repositories")
    if isinstance(repositories, list):
        declared = {repo.name for repo in REPOS}
        others = sorted(
            str(item["name"]) for item in repositories if item["name"] not in declared and not item.get("archived")
        )
        lines.append(f"other repositories of the organization (not managed here): {', '.join(others) or 'none'}")
    else:
        lines.append(f"repositories of the organization: {repositories}")
    for kind in ("secrets", "variables"):
        for name, entry in state[kind].items():
            if isinstance(entry, dict) and isinstance(entry.get("repositories"), dict):
                repositories = entry["repositories"].get("repositories", [])
                lines.append(
                    f"{name}: selected: {', '.join(sorted(str(item['name']) for item in repositories)) or 'none'}"
                )
            elif isinstance(entry, dict) and "repositories" in entry:
                lines.append(f"{name}: selected: {entry['repositories']}")
            elif isinstance(entry, dict):
                lines.append(f"{name}: visible to {entry.get('visibility')} repositories")
            else:
                lines.append(f"{name}: {entry}")
    permissions = state.get("workflow_permissions")
    operation = None
    if not isinstance(permissions, dict) or diff_settings(permissions, WORKFLOW_PERMISSIONS):
        operation = Operation(
            f"organization default GITHUB_TOKEN permissions: " f"{show(permissions)} -> {show(WORKFLOW_PERMISSIONS)}",
            "PUT",
            f"orgs/{ORG}/actions/permissions/workflow",
            dict(WORKFLOW_PERMISSIONS),
        )
    return lines, operation


def team_ids_of(org_state: Dict[str, Any]) -> Tuple[List[int], List[str]]:
    ids: List[int] = []
    errors: List[str] = []
    for slug, team in org_state["teams"].items():
        if isinstance(team, dict):
            ids.append(int(team["id"]))
        else:
            errors.append(f"team {slug!r} from RELEASE_TAG_BYPASS_TEAMS: {team}")
    return ids, errors


# ---------------------------------------------------------------------------------------------------------
# Applying


def fetch(path: str) -> Any:
    """Read something that must be readable while applying."""
    return write("GET", path)


def expected_bypass(target: Dict[str, Any]) -> Optional[str]:
    """What current_user_can_bypass must say for an admin, or None if nobody may bypass the ruleset."""
    actors = target["bypass_actors"]
    if not actors:
        return None
    return "always" if actors[0]["bypass_mode"] == "always" else "pull_requests_only"


def ruleset_problems(actual: Dict[str, Any], target: Dict[str, Any]) -> List[str]:
    problems = diff_ruleset(actual, target)
    expected = expected_bypass(target)
    if expected is not None and actual.get("current_user_can_bypass") != expected:
        problems.append(
            f"current_user_can_bypass is {actual.get('current_user_can_bypass')!r}, expected {expected!r}"
            " (check ADMIN_ROLE_ID and that you are an admin)"
        )
    return problems


def verify_ruleset(repo: Repo, written: Any, target: Dict[str, Any]) -> None:
    """Read a ruleset back after writing it and check that it is what was asked for."""
    if not isinstance(written, dict) or "id" not in written:
        raise ApiError(f"ruleset {target['name']!r}: the response has no ruleset id")
    actual = fetch(f"repos/{ORG}/{repo.name}/rulesets/{written['id']}")
    problems = ruleset_problems(actual, target)
    if problems:
        raise ApiError(f"ruleset {target['name']!r} reads back different: {'; '.join(problems)}")


def branch_ruleset_verified(plan: RepoPlan) -> bool:
    """True if the "default branch" ruleset exists, matches the target and an admin may bypass it."""
    base = f"repos/{ORG}/{plan.repo.name}"
    if plan.branch_target is None:
        return False
    for ruleset in fetch(f"{base}/rulesets?includes_parents=false&per_page={PAGE_SIZE}") or []:
        if ruleset.get("name") == BRANCH_RULESET:
            return not ruleset_problems(fetch(f"{base}/rulesets/{ruleset['id']}"), plan.branch_target)
    return False


def apply_plan(plan: RepoPlan, verbose: bool) -> None:
    for operation in plan.operations:
        print(f"  {operation.method} {operation.path}  # {operation.description}")
        if verbose and operation.body is not None:
            print("    " + json.dumps(operation.body, sort_keys=True))
        result = write(operation.method, operation.path, operation.body)
        if operation.ruleset is not None:
            verify_ruleset(plan.repo, result, operation.ruleset)
    if plan.remove_classic is not None:
        if not branch_ruleset_verified(plan):
            raise ApiError(f"{plan.repo.key}: the {BRANCH_RULESET!r} ruleset is not verified, classic protection kept")
        print(f"  {plan.remove_classic.method} {plan.remove_classic.path}  # {plan.remove_classic.description}")
        write(plan.remove_classic.method, plan.remove_classic.path)


# ---------------------------------------------------------------------------------------------------------


def print_plan(plan: RepoPlan, verbose: bool) -> None:
    info = plan.state["repo"]
    branch = info.get("default_branch") if isinstance(info, dict) else "?"
    print(f"\n== {plan.repo.key} ({ORG}/{plan.repo.name}, default branch {branch})")
    for line in plan.info + repo_report(plan.state):
        print(f"  {line}")
    operations = plan.operations + ([plan.remove_classic] if plan.remove_classic else [])
    if operations:
        print("  changes:")
        for operation in operations:
            print(f"    - {operation.description}")
            if verbose:
                print(
                    f"      {operation.method} {operation.path}"
                    + (f" {show(operation.body)}" if operation.body else "")
                )
    else:
        print("  changes: none")
    for warning in plan.warnings:
        print(f"  warning: {warning}")
    for error in plan.errors:
        print(f"  ERROR: {error}")


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", 1)[0])
    parser.add_argument("command", nargs="?", choices=("audit", "apply"), default="audit")
    parser.add_argument(
        "--repo", action="append", choices=[repo.key for repo in REPOS], help="only this repository (repeatable)"
    )
    parser.add_argument("--remove-classic-protection", action="store_true", help="delete classic branch protection")
    parser.add_argument("--prune-rulesets", action="store_true", help="delete repository rulesets not declared here")
    parser.add_argument(
        "--org", action="store_true", help="also apply the organization default GITHUB_TOKEN permissions"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="print the API calls and their bodies")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if shutil.which("gh") is None:
        print("The GitHub CLI (gh) is required: https://cli.github.com", file=sys.stderr)
        return 2
    repos = [repo for repo in REPOS if not args.repo or repo.key in args.repo]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = BACKUP_DIR / stamp

    org_state = collect_org()
    save_snapshot(snapshot_dir, "organization", org_state)
    team_ids, team_errors = team_ids_of(org_state)

    plans = []
    for repo in repos:
        state = collect_repo(repo)
        save_snapshot(snapshot_dir, repo.key, state)
        plan = plan_repo(repo, state, team_ids, args.remove_classic_protection, args.prune_rulesets)
        if repo.sdk:
            plan.errors.extend(team_errors)
        plans.append(plan)
        print_plan(plan, args.verbose)

    org_lines, org_operation = org_report(org_state)
    print(f"\n== organization {ORG}")
    for line in org_lines:
        print(f"  {line}")
    if org_operation is not None:
        print(f"  change{'' if args.org else ' (only with --org)'}: {org_operation.description}")
    print(f"\nSnapshot of the current settings: {snapshot_dir}")

    errors = [plan.repo.key for plan in plans if plan.errors]
    pending = [plan.repo.key for plan in plans if plan.operations or plan.remove_classic]
    if args.command == "audit":
        if errors or pending:
            print(f"Differs from the target: {', '.join(pending) or 'none'}; errors: {', '.join(errors) or 'none'}")
            return 1
        print("Everything matches the target.")
        return 0

    if errors:
        print(f"Nothing applied: fix the errors above or leave out with --repo: {', '.join(errors)}", file=sys.stderr)
        return 2
    try:
        for plan in plans:
            if plan.operations or plan.remove_classic:
                print(f"\n== applying {plan.repo.key}")
                apply_plan(plan, args.verbose)
        if args.org and org_operation is not None:
            print(f"\n== applying organization {ORG}")
            print(f"  {org_operation.method} {org_operation.path}  # {org_operation.description}")
            write(org_operation.method, org_operation.path, org_operation.body)
    except ApiError as error:
        print(f"\nStopped: {error}", file=sys.stderr)
        print("Changes made before this point stay; fix the cause and run apply again.", file=sys.stderr)
        return 2
    print("\nDone. Run `python scripts/github-settings.py audit` to confirm that nothing differs any more.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

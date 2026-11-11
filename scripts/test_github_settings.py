"""Offline tests of scripts/github-settings.py: no network, no `gh`.

Run: python -m unittest discover -s scripts -p "test_github_settings.py"
"""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock


def load() -> ModuleType:
    path = Path(__file__).resolve().parent / "github-settings.py"
    spec = importlib.util.spec_from_file_location("github_settings", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["github_settings"] = module
    spec.loader.exec_module(module)
    return module


gs = load()

DOTNET = next(repo for repo in gs.REPOS if repo.key == "dotnet")
CODEGEN = next(repo for repo in gs.REPOS if repo.key == "codegen")
TEST_COVERAGE = next(repo for repo in gs.REPOS if repo.key == "test-coverage")

DOTNET_RUNS = [
    {"name": name, "app": "github-actions", "status": "completed", "conclusion": "success"}
    for name in (
        "Build and test (10.0.x, net10.0)",
        "Build and test (8.0.x, net8.0)",
        "Build and test (v4.6.2, net462)",
        "Build examples and run snippets",
        "Check badges",
        "Library coverage",
        "Pack NuGet package",
        "Publish coverage",
    )
] + [{"name": "Build and test (other app)", "app": "some-other-app", "status": "completed", "conclusion": "success"}]


def as_read_back(ruleset: Dict[str, Any], ruleset_id: int = 7) -> Dict[str, Any]:
    """A ruleset as GitHub returns it: extra fields, other list order, OrganizationAdmin id, rule defaults."""
    actual = copy.deepcopy(ruleset)
    actual.update({"id": ruleset_id, "source_type": "Repository", "current_user_can_bypass": "always"})
    actual["bypass_actors"] = list(reversed(actual["bypass_actors"]))
    for actor in actual["bypass_actors"]:
        if actor["actor_type"] == "OrganizationAdmin":
            actor["actor_id"] = None
    actual["rules"] = list(reversed(actual["rules"]))
    for rule in actual["rules"]:
        if rule["type"] == "update":
            rule["parameters"] = {"update_allows_fetch_and_merge": False}
        if rule["type"] == "pull_request":
            rule["parameters"]["required_reviewers"] = []
        if rule["type"] == "required_status_checks":
            rule["parameters"]["required_status_checks"].reverse()
    return actual


def matching_state(repo: Any, runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """A repository whose settings already match the target."""
    info: Dict[str, Any] = {"default_branch": "main", "permissions": {"admin": True}}
    info.update(gs.repo_settings(repo))
    info["security_and_analysis"] = {key: {"status": value} for key, value in gs.SECURITY_AND_ANALYSIS.items()}
    checks = gs.resolve_checks(repo, runs).names
    rulesets = [as_read_back(target, index) for index, target in enumerate(gs.target_rulesets(repo, checks, []))]
    return {
        "repo": info,
        "rulesets": rulesets,
        "classic_protection": gs.Unavailable(404, "Branch not protected"),
        "branch": {"protection": {"enabled": False}},
        "vulnerability_alerts": True,
        "private_vulnerability_reporting": {"enabled": True},
        "workflow_permissions": dict(gs.WORKFLOW_PERMISSIONS),
        "merged_pull_request": {"number": 5, "title": "t", "head_sha": "abcdef0123", "merged_at": "2026-11-11"},
        "check_runs": runs,
    }


class ParseResponseTest(unittest.TestCase):
    def test_json_body(self) -> None:
        stdout = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"a": 1}'
        self.assertEqual(gs.parse_response(stdout, ""), (200, {"a": 1}))

    def test_no_content(self) -> None:
        self.assertEqual(gs.parse_response("HTTP/2.0 204 No Content\nServer: github.com\n\n", ""), (204, None))

    def test_error_body(self) -> None:
        status, data = gs.parse_response('HTTP/1.1 404 Not Found\n\n{"message": "Not Found"}', "gh: Not Found")
        self.assertEqual((status, gs.message_of(data)), (404, "Not Found"))

    def test_no_http_response(self) -> None:
        with self.assertRaises(gs.ApiError):
            gs.parse_response("", "gh: not logged in")


class ResolveChecksTest(unittest.TestCase):
    def test_patterns_expand_to_actions_check_names(self) -> None:
        resolution = gs.resolve_checks(DOTNET, DOTNET_RUNS)
        self.assertEqual(
            resolution.names,
            [
                "Build and test (10.0.x, net10.0)",
                "Build and test (8.0.x, net8.0)",
                "Build and test (v4.6.2, net462)",
                "Build examples and run snippets",
                "Check badges",
                "Library coverage",
                "Pack NuGet package",
            ],
        )
        self.assertEqual((resolution.missing, resolution.missing_optional, resolution.pending), ([], [], []))

    def test_missing_required_and_optional(self) -> None:
        runs = [{"name": "check-submodules", "app": "github-actions", "status": "completed"}]
        resolution = gs.resolve_checks(CODEGEN, runs)
        self.assertEqual(resolution.names, [])
        self.assertEqual(resolution.missing, ["Check all submodules up-to-date"])
        self.assertEqual(resolution.missing_optional, ["Run zizmor"])

    def test_pending(self) -> None:
        runs = copy.deepcopy(DOTNET_RUNS)
        runs[0]["status"] = "in_progress"
        self.assertEqual(gs.resolve_checks(DOTNET, runs).pending, ["Build and test (10.0.x, net10.0)"])


class TargetRulesetTest(unittest.TestCase):
    def test_sdk_branch_ruleset(self) -> None:
        ruleset = gs.branch_ruleset(DOTNET, ["Check badges"])
        rules = {rule["type"]: rule.get("parameters") for rule in ruleset["rules"]}
        self.assertEqual(
            set(rules),
            {"deletion", "non_fast_forward", "required_linear_history", "pull_request", "required_status_checks"},
        )
        self.assertEqual(rules["pull_request"]["allowed_merge_methods"], ["squash"])
        self.assertEqual(rules["pull_request"]["required_approving_review_count"], 1)
        self.assertEqual(
            rules["required_status_checks"]["required_status_checks"],
            [{"context": "Check badges", "integration_id": gs.GITHUB_ACTIONS_APP_ID}],
        )
        self.assertEqual(ruleset["conditions"]["ref_name"]["include"], ["~DEFAULT_BRANCH"])
        self.assertEqual({actor["bypass_mode"] for actor in ruleset["bypass_actors"]}, {gs.BYPASS_MODE})

    def test_no_status_check_rule_without_checks(self) -> None:
        types = [rule["type"] for rule in gs.branch_ruleset(DOTNET, [])["rules"]]
        self.assertNotIn("required_status_checks", types)

    def test_test_coverage_only_blocks_deletion_and_force_push(self) -> None:
        ruleset = gs.branch_ruleset(TEST_COVERAGE, [])
        self.assertEqual([rule["type"] for rule in ruleset["rules"]], ["deletion", "non_fast_forward"])
        self.assertEqual(ruleset["bypass_actors"], [])
        self.assertEqual(len(gs.target_rulesets(TEST_COVERAGE, [], [])), 1)

    def test_tag_ruleset_always_bypass_and_teams(self) -> None:
        original = getattr(gs, "BYPASS_MODE")
        setattr(gs, "BYPASS_MODE", "pull_request")
        try:
            ruleset = gs.tag_ruleset([42])
            branch = gs.branch_ruleset(DOTNET, [])
        finally:
            setattr(gs, "BYPASS_MODE", original)
        self.assertEqual({actor["bypass_mode"] for actor in ruleset["bypass_actors"]}, {"always"})
        self.assertIn({"actor_id": 42, "actor_type": "Team", "bypass_mode": "always"}, ruleset["bypass_actors"])
        self.assertEqual(ruleset["conditions"]["ref_name"]["include"], ["refs/tags/v*"])
        self.assertEqual([rule["type"] for rule in ruleset["rules"]], ["creation", "update", "deletion"])
        self.assertEqual({actor["bypass_mode"] for actor in branch["bypass_actors"]}, {"pull_request"})


class DiffRulesetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.target = gs.branch_ruleset(DOTNET, ["Check badges", "Library coverage"])

    def test_read_back_matches(self) -> None:
        self.assertEqual(gs.diff_ruleset(as_read_back(self.target), self.target), [])
        tag = gs.tag_ruleset([])
        self.assertEqual(gs.diff_ruleset(as_read_back(tag), tag), [])

    def test_changed_parameter(self) -> None:
        actual = as_read_back(self.target)
        for rule in actual["rules"]:
            if rule["type"] == "pull_request":
                rule["parameters"]["required_approving_review_count"] = 0
                del rule["parameters"]["allowed_merge_methods"]
        self.assertEqual(
            gs.diff_ruleset(actual, self.target),
            [
                "rule pull_request.required_approving_review_count: 0 -> 1",
                'rule pull_request.allowed_merge_methods: null -> ["squash"]',
            ],
        )

    def test_extra_and_missing_rules(self) -> None:
        actual = as_read_back(self.target)
        actual["rules"] = [rule for rule in actual["rules"] if rule["type"] != "required_linear_history"]
        actual["rules"].append({"type": "creation"})
        self.assertEqual(
            gs.diff_ruleset(actual, self.target),
            ["rule creation: present -> absent", "rule required_linear_history: absent -> present"],
        )

    def test_bypass_problem(self) -> None:
        actual = as_read_back(self.target)
        actual["current_user_can_bypass"] = "never"
        problems = gs.ruleset_problems(actual, self.target)
        self.assertEqual(len(problems), 1)
        self.assertIn("current_user_can_bypass", problems[0])
        self.assertEqual(
            gs.ruleset_problems(
                as_read_back(gs.branch_ruleset(TEST_COVERAGE, [])), gs.branch_ruleset(TEST_COVERAGE, [])
            ),
            [],
        )


class PlanRepoTest(unittest.TestCase):
    def test_nothing_to_do_when_everything_matches(self) -> None:
        plan = gs.plan_repo(DOTNET, matching_state(DOTNET, DOTNET_RUNS), [])
        self.assertEqual([operation.description for operation in plan.operations], [])
        self.assertEqual((plan.warnings, plan.errors, plan.remove_classic), ([], [], None))
        self.assertIn("approvals: 1", "\n".join(plan.info))

    def test_drift(self) -> None:
        state = matching_state(DOTNET, DOTNET_RUNS)
        state["repo"]["allow_merge_commit"] = True
        state["repo"]["homepage"] = None
        state["vulnerability_alerts"] = False
        state["workflow_permissions"] = gs.Unavailable(403, "blocked")
        state["rulesets"] = [
            {"id": 3, "name": "main", "source_type": "Repository", "target": "branch", "rules": []},
            state["rulesets"][1],
        ]
        plan = gs.plan_repo(DOTNET, state, [])
        operations = {operation.description.split(":")[0]: operation for operation in plan.operations}
        self.assertEqual(
            operations["settings"].body,
            {"allow_merge_commit": False, "homepage": "https://products.aspose.cloud/barcode/"},
        )
        self.assertEqual(operations["Dependabot alerts"].method, "PUT")
        self.assertEqual(operations["default GITHUB_TOKEN permissions"].body, gs.WORKFLOW_PERMISSIONS)
        self.assertEqual(operations["ruleset 'default branch'"].method, "POST")
        self.assertNotIn("ruleset 'release tags'", operations)
        self.assertEqual(plan.warnings, ["ruleset 'main' is not declared here (delete it with --prune-rulesets)"])

    def test_prune_and_classic_protection(self) -> None:
        state = matching_state(DOTNET, DOTNET_RUNS)
        state["rulesets"].append({"id": 3, "name": "zizmor", "source_type": "Repository", "target": "branch"})
        state["classic_protection"] = {"required_status_checks": {"contexts": ["build"]}}
        plan = gs.plan_repo(DOTNET, state, [], remove_classic=True, prune_rulesets=True)
        self.assertEqual(
            [(operation.method, operation.path) for operation in plan.operations],
            [("DELETE", "repos/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-.NET/rulesets/3")],
        )
        self.assertIsNotNone(plan.remove_classic)
        self.assertEqual(
            plan.remove_classic.path,
            "repos/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-.NET/branches/main/protection",
        )

    def test_changed_check_rewrites_ruleset(self) -> None:
        state = matching_state(DOTNET, DOTNET_RUNS)
        state["check_runs"] = DOTNET_RUNS + [
            {"name": "Build and test (11.0.x, net11.0)", "app": "github-actions", "status": "completed"}
        ]
        plan = gs.plan_repo(DOTNET, state, [])
        self.assertEqual([operation.method for operation in plan.operations], ["PUT"])
        self.assertIn("Build and test (11.0.x, net11.0)", plan.operations[0].description)

    def test_errors(self) -> None:
        state = matching_state(CODEGEN, [{"name": "check-submodules", "app": "github-actions", "status": "completed"}])
        state["repo"]["permissions"] = {"admin": False}
        plan = gs.plan_repo(CODEGEN, state, [])
        self.assertEqual(len(plan.errors), 2)
        self.assertIn("not an admin", plan.errors[0])
        self.assertIn("'Check all submodules up-to-date'", plan.errors[1])
        self.assertEqual(plan.warnings, ["optional check 'Run zizmor' does not exist yet, not required"])

    def test_classic_protection_from_branch_summary(self) -> None:
        state = matching_state(DOTNET, DOTNET_RUNS)
        state["classic_protection"] = gs.Unavailable(403, "blocked")
        state["branch"] = {"protection": {"enabled": True}}
        plan = gs.plan_repo(DOTNET, state, [])
        self.assertEqual(len(plan.warnings), 1)
        self.assertIn("--remove-classic-protection", plan.warnings[0])


class FakeGitHub:
    """Just enough of the GitHub REST API for one repository to run `apply` end to end."""

    def __init__(self, repo: Any, runs: List[Dict[str, Any]]) -> None:
        self.base = f"repos/{gs.ORG}/{repo.name}"
        self.repo: Dict[str, Any] = {
            "default_branch": "main",
            "permissions": {"admin": True},
            "allow_squash_merge": True,
            "allow_merge_commit": True,
            "allow_rebase_merge": True,
            "security_and_analysis": None,
        }
        self.rulesets: Dict[int, Dict[str, Any]] = {
            3: {
                "id": 3,
                "name": "main",
                "target": "branch",
                "source_type": "Repository",
                "rules": [{"type": "deletion"}],
            }
        }
        self.classic: Optional[Dict[str, Any]] = {"required_status_checks": {"contexts": ["build-and-test"]}}
        self.flags = {"vulnerability-alerts": False}
        self.reporting = {"enabled": False}
        self.workflow: Dict[str, Any] = {
            "default_workflow_permissions": "write",
            "can_approve_pull_request_reviews": True,
        }
        self.runs = runs
        self.calls: List[Tuple[str, str]] = []

    def stored(self, ruleset: Dict[str, Any], ruleset_id: int) -> Dict[str, Any]:
        result = as_read_back(ruleset, ruleset_id)
        result["current_user_can_bypass"] = "always" if ruleset.get("bypass_actors") else "never"
        return result

    def __call__(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Tuple[int, Any]:
        url = urllib.parse.urlsplit(path)
        route = url.path
        query = urllib.parse.parse_qs(url.query)
        if method != "GET":
            self.calls.append((method, route))
        if not route.startswith(self.base):
            return 403, {"message": "blocked"}
        tail = route[len(self.base) :]
        if tail == "" and method == "GET":
            return 200, copy.deepcopy(self.repo)
        if tail == "" and method == "PATCH":
            assert body is not None
            for key, value in body.items():
                if key == "security_and_analysis":
                    self.repo[key] = {**(self.repo[key] or {}), **value}
                else:
                    self.repo[key] = value
            return 200, copy.deepcopy(self.repo)
        if tail == "/rulesets" and method == "GET":
            if query.get("page", ["1"]) != ["1"]:
                return 200, []
            return 200, [
                {"id": key, "name": value["name"], "source_type": "Repository"} for key, value in self.rulesets.items()
            ]
        if tail == "/rulesets" and method == "POST":
            assert body is not None
            ruleset_id = max(self.rulesets) + 1
            self.rulesets[ruleset_id] = self.stored(body, ruleset_id)
            return 201, self.rulesets[ruleset_id]
        if tail.startswith("/rulesets/"):
            ruleset_id = int(tail.rsplit("/", 1)[1])
            if method == "GET":
                return 200, copy.deepcopy(self.rulesets[ruleset_id])
            if method == "PUT":
                assert body is not None
                self.rulesets[ruleset_id] = self.stored(body, ruleset_id)
                return 200, self.rulesets[ruleset_id]
            if method == "DELETE":
                del self.rulesets[ruleset_id]
                return 204, None
        if tail == "/branches/main/protection":
            if method == "DELETE":
                self.classic = None
                return 204, None
            return (200, self.classic) if self.classic else (404, {"message": "Branch not protected"})
        if tail == "/branches/main":
            return 200, {"protection": {"enabled": self.classic is not None}}
        if tail == "/vulnerability-alerts":
            if method == "PUT":
                self.flags["vulnerability-alerts"] = True
            return (204, None) if self.flags["vulnerability-alerts"] else (404, {"message": "Not Found"})
        if tail == "/private-vulnerability-reporting":
            if method == "PUT":
                self.reporting = {"enabled": True}
                return 204, None
            return 200, self.reporting
        if tail == "/actions/permissions/workflow":
            if method == "PUT":
                assert body is not None
                self.workflow = dict(body)
                return 204, None
            return 200, self.workflow
        if tail.startswith("/pulls"):
            return 200, [{"number": 9, "title": "t", "merged_at": "2026-11-11T00:00:00Z", "head": {"sha": "abc"}}]
        if tail == "/commits/abc/check-runs":
            return 200, {
                "check_runs": [
                    {"name": run["name"], "app": {"slug": run["app"]}, "status": run["status"], "conclusion": "success"}
                    for run in self.runs
                ]
            }
        return 403, {"message": "blocked"}


class ApplyEndToEndTest(unittest.TestCase):
    def run_main(self, fake: FakeGitHub, *args: str) -> int:
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(gs, "gh", fake))
            stack.enter_context(mock.patch.object(gs, "BACKUP_DIR", Path(directory)))
            stack.enter_context(mock.patch.object(gs.shutil, "which", return_value="/usr/bin/gh"))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            result: int = gs.main(list(args))
            return result

    def test_apply_then_audit_is_clean(self) -> None:
        fake = FakeGitHub(DOTNET, DOTNET_RUNS)
        self.assertEqual(self.run_main(fake, "audit", "--repo", "dotnet"), 1)
        self.assertEqual(fake.calls, [])

        result = self.run_main(fake, "apply", "--repo", "dotnet", "--remove-classic-protection", "--prune-rulesets")
        self.assertEqual(result, 0)
        self.assertIsNone(fake.classic)
        self.assertEqual(
            sorted(ruleset["name"] for ruleset in fake.rulesets.values()), ["default branch", "release tags"]
        )
        self.assertEqual(fake.calls[-1], ("DELETE", f"{fake.base}/branches/main/protection"))
        self.assertEqual(fake.repo["allow_merge_commit"], False)
        self.assertEqual(fake.workflow, gs.WORKFLOW_PERMISSIONS)

        fake.calls.clear()
        self.assertEqual(self.run_main(fake, "audit", "--repo", "dotnet"), 0)
        self.assertEqual(self.run_main(fake, "apply", "--repo", "dotnet", "--prune-rulesets"), 0)
        self.assertEqual(fake.calls, [])

    def test_apply_refuses_on_missing_check(self) -> None:
        fake = FakeGitHub(DOTNET, [run for run in DOTNET_RUNS if run["name"] != "Library coverage"])
        self.assertEqual(self.run_main(fake, "apply", "--repo", "dotnet", "--remove-classic-protection"), 2)
        self.assertEqual(fake.calls, [])
        self.assertIsNotNone(fake.classic)

    def test_classic_protection_kept_when_bypass_fails(self) -> None:
        fake = FakeGitHub(DOTNET, DOTNET_RUNS)
        original = fake.stored

        def no_bypass(ruleset: Dict[str, Any], ruleset_id: int) -> Dict[str, Any]:
            result = original(ruleset, ruleset_id)
            result["current_user_can_bypass"] = "never"
            return result

        setattr(fake, "stored", no_bypass)
        self.assertEqual(self.run_main(fake, "apply", "--repo", "dotnet", "--remove-classic-protection"), 2)
        self.assertIsNotNone(fake.classic)


if __name__ == "__main__":
    unittest.main()

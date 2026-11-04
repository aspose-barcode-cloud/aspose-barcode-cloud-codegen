#!/bin/bash
#
# Phase 3 of doc/zizmor-rollout-plan.md: make the "Run zizmor" check required
# on the default branch of every repository and set the organization's
# default GITHUB_TOKEN permissions to read-only.
#
# Needs the GitHub CLI (`gh`) logged in as an organization owner. Run it after
# the zizmor pull requests are merged, so the check exists on every default
# branch. Idempotent: an existing ruleset named "zizmor" is updated in place.
# If the organization plan allows organization rulesets, one ruleset there
# (same rule, target "all repositories") can replace the per-repository ones.
#
# Usage:
#   ./scripts/enforce-zizmor-check.bash            # apply
#   ./scripts/enforce-zizmor-check.bash --dry-run  # print the gh calls only
set -euo pipefail

org="aspose-barcode-cloud"
repos=(
    aspose-barcode-cloud-codegen
    aspose-barcode-cloud-go
    Aspose.BarCode-Cloud-SDK-for-Android
    Aspose.BarCode-Cloud-SDK-for-Dart
    Aspose.BarCode-Cloud-SDK-for-.NET
    Aspose.BarCode-Cloud-SDK-for-Java
    Aspose.BarCode-Cloud-SDK-for-Node.js
    Aspose.BarCode-Cloud-SDK-for-PHP
    Aspose.BarCode-Cloud-SDK-for-Python
    Aspose.BarCode-Cloud-SDK-for-Swift
)
ruleset_name="zizmor"
check_name="Run zizmor"      # job name in codegen/github/zizmor.yml
github_actions_app_id=15368  # only checks reported by GitHub Actions count

dry_run=0
if [ "${1:-}" = "--dry-run" ]; then
    dry_run=1
elif [ $# -ne 0 ]; then
    >&2 echo "Usage: $0 [--dry-run]"
    exit 1
fi

# One ruleset per repository on its default branch ("~DEFAULT_BRANCH" is
# `main` everywhere except go, where it is `v4`): a pull request or push must
# carry a passing "Run zizmor" check. Repository admins keep an "always"
# bypass so the direct release pushes to the default branch (ReleaseWorkflow.md)
# are not blocked; the zizmor workflow still runs on every push and the README
# badge shows the result.
ruleset_json=$(cat <<EOF
{
  "name": "${ruleset_name}",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] }
  },
  "bypass_actors": [
    { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always" }
  ],
  "rules": [
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": false,
        "do_not_enforce_on_create": true,
        "required_status_checks": [
          { "context": "${check_name}", "integration_id": ${github_actions_app_id} }
        ]
      }
    }
  ]
}
EOF
)

run() {
    if [ "${dry_run}" = 1 ]; then
        echo "+ gh $*"
    else
        gh "$@"
    fi
}

for repo in "${repos[@]}"; do
    existing=$(gh api "repos/${org}/${repo}/rulesets" \
        --jq ".[] | select(.name == \"${ruleset_name}\") | .id" 2>/dev/null || true)
    if [ -n "${existing}" ]; then
        echo "${repo}: updating ruleset ${existing}"
        echo "${ruleset_json}" | run api --method PUT "repos/${org}/${repo}/rulesets/${existing}" --input -
    else
        echo "${repo}: creating ruleset"
        echo "${ruleset_json}" | run api --method POST "repos/${org}/${repo}/rulesets" --input -
    fi
done

# Organization default for GITHUB_TOKEN: read-only. Every workflow in these
# repositories declares its permissions explicitly, so this only guards
# workflows added later without a `permissions:` block.
echo "${org}: default GITHUB_TOKEN permissions -> read-only"
run api --method PUT "orgs/${org}/actions/permissions/workflow" \
    -f default_workflow_permissions=read \
    -F can_approve_pull_request_reviews=false

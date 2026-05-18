#!/bin/bash
set -euo pipefail

submodule_args=(--init --recursive)
if [ "$#" -gt 0 ]; then
    submodule_args+=("$@")
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [ -n "${SWIFT_SUBMODULE_DEPLOY_KEY:-}" ]; then
    ssh_dir="$HOME/.ssh"
    key_file="$ssh_dir/aspose_barcode_cloud_swift_submodule"

    mkdir -p "$ssh_dir"
    chmod 700 "$ssh_dir"
    printf '%s\n' "$SWIFT_SUBMODULE_DEPLOY_KEY" > "$key_file"
    chmod 600 "$key_file"
    ssh-keyscan github.com >> "$ssh_dir/known_hosts" 2>/dev/null

    git config submodule.submodules/swift.url git@github.com:aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Swift.git
    export GIT_SSH_COMMAND="ssh -i $key_file -o IdentitiesOnly=yes -o UserKnownHostsFile=$ssh_dir/known_hosts"
fi

git submodule update "${submodule_args[@]}"

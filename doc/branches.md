SDK repository branches
=======================

Each SDK submodule is a standalone GitHub repository under the `aspose-barcode-cloud` org with its own
default (mainline) branch. The default branch is `main` for every SDK **except `go`, whose default is
`v4`** — go's `main` is a deprecated 24.9-era branch, so base go work and open go pull requests against
`v4`, not `main`.

| SDK | Repository | Default (base) branch |
|-----|------------|-----------------------|
| android | [`Aspose.BarCode-Cloud-SDK-for-Android`](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Android) | `main` |
| dart | [`Aspose.BarCode-Cloud-SDK-for-Dart`](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Dart) | `main` |
| dotnet | [`Aspose.BarCode-Cloud-SDK-for-.NET`](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-.NET) | `main` |
| go | [`aspose-barcode-cloud-go`](https://github.com/aspose-barcode-cloud/aspose-barcode-cloud-go) | `v4` |
| java | [`Aspose.BarCode-Cloud-SDK-for-Java`](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Java) | `main` |
| node | [`Aspose.BarCode-Cloud-SDK-for-Node.js`](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Node.js) | `main` |
| php | [`Aspose.BarCode-Cloud-SDK-for-PHP`](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-PHP) | `main` |
| python | [`Aspose.BarCode-Cloud-SDK-for-Python`](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Python) | `main` |
| swift | [`Aspose.BarCode-Cloud-SDK-for-Swift`](https://github.com/aspose-barcode-cloud/Aspose.BarCode-Cloud-SDK-for-Swift) | `main` |

Merging pull requests
---------------------

The same in every SDK repository, this repository and `test-coverage`, enforced by
[`scripts/github-settings.py`](../scripts/github-settings.py) (see [github-settings.md](github-settings.md)):

* squash merge only, with a linear history; the squash commit takes the pull request title;
* one approval, dismissed by new commits, and the repository's required checks;
* the head branch is deleted after the merge;
* repository admins and organization owners may bypass these rules;
* only they may create, move or delete `v*` tags, which publish the releases.

Release branches
----------------

Release work lands on a `release-<major>.<minor>` branch (e.g.
`release-26.7`) cut from the default branch. If the release has a non-zero
patch component, include it in the branch name (e.g. `release-26.7.1`).

Open the release branch as a **draft** pull request back into the SDK's
default branch. Use the SDK's full package version in the title, for example
`Release 26.7.0`.

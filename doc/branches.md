SDK repository branches
=======================

Each SDK submodule is a standalone GitHub repository under the `aspose-barcode-cloud` org with its own
default (mainline) branch. The default branch is `main` for every SDK **except `go`, whose default is
`v4`** — go's `main` is a deprecated 24.9-era branch, so base go work and open go pull requests against
`v4`, not `main`.

| SDK | Repository | Default (base) branch |
|-----|------------|-----------------------|
| android | `aspose-barcode-cloud-android` | `main` |
| dart | `aspose-barcode-cloud-dart` | `main` |
| dotnet | `aspose-barcode-cloud-dotnet` | `main` |
| go | `aspose-barcode-cloud-go` | `v4` |
| java | `aspose-barcode-cloud-java` | `main` |
| node | `aspose-barcode-cloud-node` | `main` |
| php | `aspose-barcode-cloud-php` | `main` |
| python | `aspose-barcode-cloud-python` | `main` |
| swift | `Aspose.BarCode-Cloud-SDK-for-Swift` | `main` |

Release work lands on a `release-<version>` branch (e.g. `release-26.7`) cut from the default branch, and
is opened as a **draft** pull request titled `Release <version>` back into that SDK's default branch.

Versioning
==========

The release pipeline uses **calendar versioning** (`YY.M.P`) as the canonical input:
year, month, and an optional patch. Each language SDK then transforms that input
into the format its package ecosystem expects.

The transform lives in [`scripts/new-version.py`](../scripts/new-version.py); the
release entry point [`scripts/start-release.bash`](../scripts/start-release.bash)
calls it with the current year and month.

Per-language formats
--------------------

Patch defaults to `0`. Examples below assume input `(26, 4, 0)` and a second row
for `(26, 4, 1)` where the patch matters.

| SDK     | Config field       | Format            | Example for (26, 4, 0) | Example for (26, 4, 1) | Registry convention |
|---------|--------------------|-------------------|------------------------|------------------------|---------------------|
| .NET    | `packageVersion`   | `YY.M.P`          | `26.4.0`               | `26.4.1`               | NuGet — loose SemVer-ish |
| Android | `artifactVersion`  | `YY.M.P`          | `26.4.0`               | `26.4.1`               | Maven coordinates — no enforced range syntax |
| Dart    | `pubVersion`       | `4.YY.M[+P]`      | `4.26.4`               | `4.26.4+1`             | pub.dev — strict SemVer 2.0.0 |
| Go      | `packageVersion`   | `4.YYMM.P`        | `4.2604.0`             | `4.2604.1`             | Go modules — strict SemVer; major in import path for major ≥ 2 |
| Java    | `artifactVersion`  | `YY.M.P`          | `26.4.0`               | `26.4.1`               | Maven Central — loose-ish |
| Node    | `npmVersion`       | `YY.M.P`          | `26.4.0`               | `26.4.1`               | npm — strict SemVer 2.0.0 |
| PHP     | `artifactVersion`  | `YY.M.P`          | `26.4.0`               | `26.4.1`               | Packagist — strict SemVer-ish |
| Python  | `packageVersion`   | `YY.M.P`          | `26.4.0`               | `26.4.1`               | PyPI — [PEP 440](https://peps.python.org/pep-0440/) |
| Swift   | `packageVersion`   | `YY.M.P`          | `26.4.0`               | `26.4.1`               | SwiftPM — strict [SemVer 2.0.0](https://semver.org/) |

Why some SDKs get a synthetic `4.` major
-----------------------------------------

The Aspose.BarCode Cloud HTTP API is at version 4. Some package registries enforce
strict SemVer and refuse to publish "breaking" major-version bumps without
ceremony, so for those ecosystems we keep the registry-visible major locked at
`4` and put the calendar coordinates into the lower positions:

* **Go** (`4.YYMM.P`) — Go modules treat the major version as load-bearing.
  Any major ≥ 2 must be reflected in the import path (e.g. `…/v4`). Bumping the
  major every year would force every consumer to rewrite their imports. We bake
  `4.` in and squash year+month into the minor (`YYMM`).
* **Dart** (`4.YY.M[+P]`) — pub.dev enforces SemVer 2.0.0; a `4.x.x` line gives
  consumers a stable major. The patch component piggybacks on SemVer build
  metadata (`+1`, `+2`, …) so it stays an in-range upgrade.

The remaining SDKs (.NET, Android, Java, Node, PHP, Python, Swift) ship the raw
calendar version `YY.M.P` into the registry's `MAJOR.MINOR.PATCH` slots.

Why the raw-calendar SDKs work even with strict SemVer tooling
--------------------------------------------------------------

Treating the year as the major works mechanically — every January is a "major"
bump, which is exactly the signal SemVer tools encode when the major number
changes. Consumers using range syntax (`^26.4.0`, `from: "26.4.0"`, `~> 26.4`)
get bug fixes and minor updates within the current year for free, but **must
explicitly bump their constraint at the year boundary** to receive the next
year's releases. That is consistent across the seven raw-calendar SDKs.

Swift specifics
---------------

Swift Package Manager uses **SemVer 2.0.0** exclusively for version
requirements (see
[apple/swift-package-manager — PackageDescription](https://docs.swift.org/package-manager/PackageDescription/PackageDescription.html#package-dependency-requirement)):

* Format: `MAJOR.MINOR.PATCH`, optional `-prerelease` and `+buildmetadata`.
* Versions are resolved from **git tags**. SwiftPM strips a leading `v` from
  tag names, so both `v26.4.0` and `26.4.0` resolve to the same version.
* `.package(url: …, from: "26.4.0")` means `>= 26.4.0, < 27.0.0` — same-major
  upgrades only.
* This repo uses **`vYY.M.P`** as the tag form (e.g. `v26.4.0`) to match the
  other SDKs, and the Swift README documents that consumers drop the `v` when
  writing `from:`.

Implication for Swift consumers: a `from: "26.4.0"` constraint will keep
receiving `26.4.x` and `26.5.x` updates throughout 2026, but **will not pull
`27.x` automatically** when the year rolls over. This matches the behaviour of
the other raw-calendar SDKs above.

Release flow
------------

`scripts/start-release.bash`:

1. Reads current year (`YY`) and month (`M`); patch defaults to `0`.
2. Calls `scripts/new-version.py YY M` which rewrites every `config-*.json`
   using the per-language transform above.
3. The per-language `make <sdk>` target regenerates the submodule from the
   updated config.

To override patch, call `new-version.py` directly: `python scripts/new-version.py 26 4 1`.

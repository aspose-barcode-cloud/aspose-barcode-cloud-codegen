# Test coverage requirements

Every generated SDK must satisfy two coverage bars. `submodules/android` is exempt from both — it is a
demo application that consumes the published Java SDK, so it has no API surface of its own to cover.

1. **API endpoint coverage — at least 80%.** At least 80% of the API operations defined in
   `spec/aspose-barcode-cloud.json` must be exercised by a test (no fewer than 8 of the 9 at the current
   surface). Every SDK currently covers all 9 operations (100%).
2. **Line code coverage — at least 80%, enforced by a per-SDK CI gate.** Each SDK's own CI fails the build
   when line coverage of the SDK library code drops below 80%. The bar is reached with deterministic
   **offline** tests over the generated model / enum / serialization / core code (mirroring java's
   `GeneratedModelCoverageTest` and `SdkCoreCoverageTest`) on top of the live API tests, which run in CI via
   the `TEST_CONFIGURATION_ACCESS_TOKEN` secret.

Regenerating or changing an SDK must not drop either metric below 80%.

## `make cover` — the same contract in every SDK

Every SDK has a `make cover` target that:

1. runs the test suite under the SDK's native coverage tool, measuring the library code only, and leaves
   the native report under `coverage/`;
2. passes that report to the shared [`scripts/coverage.py`](../scripts/coverage.py), which
   - prints one line: `Line coverage: 84.69% (1040/1228 lines, threshold: 80%)`,
   - writes `coverage/coverage-badge.json` (shields.io endpoint badge document) and
     `coverage/coverage-summary.json` (format, report path, percent, covered/total lines, threshold),
   - exits with code 1 when coverage is below the threshold;
3. reads the threshold from `COVERAGE_THRESHOLD` (default `80`), e.g. `COVERAGE_THRESHOLD=90 make cover`.

`scripts/coverage.py` and `scripts/publish-coverage.py` live in this repository. Together with `LICENSE`
and `scripts/check-badges.bash` they are copied into every SDK by `scripts/copy-common-files.bash <sdk-dir>`
(into `Scripts/` for swift), which each `codegen/generate-<sdk>.bash` calls. `generate-android.bash`
passes `--no-coverage`, so android gets only `LICENSE` and `check-badges.bash`. Change them here and
regenerate; do not edit the SDK copies.

| SDK | Measured code | Native tool → report | `scripts/coverage.py` format | CI job running `make cover` |
|-----|---------------|----------------------|------------------------------|-----------------------------|
| dart | `lib/` | `dart test --coverage` → `coverage/lcov.info` | `lcov` | `dart.yml` / `build` |
| dotnet | `[Aspose.BarCode.Cloud.Sdk]*` | coverlet → `coverage/coverage.net<ver>.cobertura.xml` | `cobertura` | `dotnet-core.yml` / `coverage` |
| go | `./barcode/...` | `go test -coverprofile` → `coverage/coverage.out` | `go` | `go.yml` / `coverage` |
| java | `src/main` | JaCoCo → `coverage/jacoco.xml` (copy of `target/site/jacoco/jacoco.xml`) | `jacoco` | `ci.yml` / `test` (via `make test`) |
| node | `src/**/*.ts` | jest → `coverage/lcov.info` | `lcov` | `node.js.yml` / `build` (via `make github-ci`) |
| php | `src/` | PHPUnit `--coverage-cobertura` → `coverage/cobertura.xml` | `cobertura` | `php-versions.yml` / `coverage` |
| python | `aspose_barcode_cloud` | pytest-cov → `coverage/coverage.xml` | `cobertura` | `python-package.yml` / `build` (via `make test`) |
| swift | `Sources/` | `swift test --enable-code-coverage` + `llvm-cov export -format=lcov` → `coverage/lcov.info` | `lcov --include /Sources/` | `swift.yml` / `linux-test` |

Some SDKs keep their tool's own 80% check as well (JaCoCo `check` in `pom.xml`, jest `coverageThreshold`,
pytest-cov `fail_under` in `.coveragerc`). Those are fixed at 80; `COVERAGE_THRESHOLD` only moves the
shared gate.

Live API tests need `TEST_CONFIGURATION_ACCESS_TOKEN` (or the SDK's configuration file). Without it they
fail, and so does `make cover` — run it with credentials, or read the percentage it prints anyway.

## Coverage reports and badges: the `test-coverage` repository

Coverage results of all SDKs are collected in one public repository,
[`aspose-barcode-cloud/test-coverage`](https://github.com/aspose-barcode-cloud/test-coverage).
The SDK repositories themselves are never written by CI: their workflows run with
`permissions: contents: read`.

How the README badge is built from these files, when it changes, and what to do when it shows an error or an
old value: [coverage badges](coverage-badges.md).

Layout of `test-coverage`, one folder per SDK (`dart`, `dotnet`, `go`, `java`, `node`, `php`, `python`,
`swift`):

| File | Content |
|------|---------|
| `<sdk>/coverage-badge.json` | shields.io endpoint badge document, e.g. `{"schemaVersion": 1, "label": "coverage", "message": "84.7%", "color": "green"}` (≥90 brightgreen, ≥80 green, ≥70 yellowgreen, ≥60 yellow, ≥50 orange, else red) |
| `<sdk>/summary.json` | percent, covered/total lines, threshold, SDK repository and commit, workflow run URL, date |
| `<sdk>/<native report>` | the report from the table above (`lcov.info`, `coverage.xml`, `cobertura.xml`, `jacoco.xml`, `coverage.out`) |

Every publish is one commit on `main` of that repository, so its history is the coverage trend of each
SDK.

### How a result gets there

1. The CI job that runs `make cover` uploads `coverage/coverage-badge.json`,
   `coverage/coverage-summary.json` and the native report as a workflow artifact named `coverage`.
   This job has no write credentials at all.
2. A separate `publish-coverage` job runs **only on push to the SDK's default branch** (`main`, `v4` for
   go) and only when the `COVERAGE_APP_CLIENT_ID` variable is set, so it is skipped on pull requests and on
   repositories where the app is not configured. It downloads the artifact, obtains a token for the
   `test-coverage` repository with `actions/create-github-app-token` (limited to that repository and to
   `contents: write`), and runs `python scripts/publish-coverage.py <sdk>`.
3. `scripts/publish-coverage.py` clones `test-coverage`, replaces the `<sdk>/` folder, commits as the
   app's bot user and pushes. If another SDK pushed at the same moment, it starts over from the new tip
   (up to three attempts). The token is passed to git through the environment, never through the remote
   URL or the command line.
4. The SDK README shows the badge through shields.io:

   ```markdown
   [![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/aspose-barcode-cloud/test-coverage/main/python/coverage-badge.json)](https://github.com/aspose-barcode-cloud/test-coverage)
   ```

   GitHub and shields.io cache the file for a few minutes, so a new value shows up shortly after the
   publish. Until the first publish of an SDK, its badge shows an error instead of a percentage.

The badge line is part of the README templates in `codegen/Templates/<lang>/README*.mustache`, so
regenerating an SDK keeps it. `scripts/check-badges.bash` only validates workflow status badges
(`.../<workflow>.yml/badge.svg?branch=...`) and ignores shields.io endpoint badges.

### One-time setup (organization admin)

1. Create the public repository `aspose-barcode-cloud/test-coverage` (initialize it with a README;
   the SDK folders are created by the first publishes).
2. Create a GitHub App owned by the organization (Organization settings → Developer settings → GitHub
   Apps → New GitHub App):
   - any name, e.g. `aspose-barcode-cloud-coverage`; the slug becomes the commit author
     (`<slug>[bot]`);
   - uncheck **Webhook → Active**;
   - Repository permissions: **Contents: Read and write** only;
   - "Where can this GitHub App be installed?": **Only on this account**.
3. On the app's page (General → About) note the **Client ID** (`Iv23li…`, not the numeric App ID) and
   generate a **private key** (a `.pem` file is downloaded).
4. Install the app on the organization, **Only select repositories → `test-coverage`**.
5. In Organization settings → Secrets and variables → Actions, create
   - the **variable** `COVERAGE_APP_CLIENT_ID` = the Client ID,
   - the **secret** `COVERAGE_APP_PRIVATE_KEY` = the contents of the `.pem` file,

   both with repository access limited to the eight SDK repositories.

The publish job is skipped until `COVERAGE_APP_CLIENT_ID` exists, so the SDK changes can be merged before this
setup is done; the badges simply stay empty until the next push to each default branch after it.

To revoke CI's write access later, uninstall the app or delete the secret; nothing in the SDK
repositories changes.

### Adding a new SDK

1. Give the SDK a `make cover` target that leaves one of the report formats above under `coverage/` and
   ends with `$(PYTHON) scripts/coverage.py <format> coverage/<report>`, where
   `PYTHON ?= $(shell command -v python 2>/dev/null || echo python3)`.
2. Call `../scripts/copy-common-files.bash "$targetDir"` from its `codegen/generate-<sdk>.bash`; it
   copies `scripts/coverage.py`, `scripts/publish-coverage.py`, `scripts/check-badges.bash` and `LICENSE`.
3. In its workflow: `permissions: contents: read` at the top, an `actions/upload-artifact` step after
   `make cover` (artifact `coverage`, the three files), and a `publish-coverage` job as in the other SDKs,
   with the SDK name as the script argument.
4. Add the badge line to the SDK's README template with the SDK name in the URL, regenerate, and check that
   the submodule has no unstaged changes. Add the badge to the README of `test-coverage` too.

### Alternative: Codecov

If PR comments or coverage history with a UI are wanted later, every report above can be uploaded to
Codecov with `codecov/codecov-action` instead of (or in addition to) publishing to `test-coverage`. It
needs the Codecov GitHub App installed on the `aspose-barcode-cloud` organization and a `CODECOV_TOKEN`
secret; the badge image is then `codecov.io/gh/aspose-barcode-cloud/<repo>/branch/<default-branch>/graph/badge.svg`.

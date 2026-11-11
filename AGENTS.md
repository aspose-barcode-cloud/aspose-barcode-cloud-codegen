# Aspose.BarCode Cloud SDK and Codegen repository

This repository contains the OpenAPI-generated SDKs for the Aspose.BarCode Cloud service and the scripts that
generate them.

- All SDKs are git submodules located in the `submodules` directory.
- The OpenAPI specification of the service API is `spec/aspose-barcode-cloud.json`.
- Custom mustache templates are in the `codegen/Templates` directory. The original templates for all languages
  are in the [openapi-generator repository][upstream-templates].
- SDK generation scripts are in the `codegen` directory. Post-processing steps are in each submodule's `Makefile`.

[upstream-templates]: https://github.com/OpenAPITools/openapi-generator/tree/master/modules/openapi-generator/src/main/resources/

## Code generation pipeline

```text
spec/aspose-barcode-cloud.json            (OpenAPI spec)
  + codegen/config-<lang>.json            (per-language config: versions, package names, URLs)
  + codegen/Templates/<lang>/*.mustache   (customized templates)
  → codegen/Tools/openapi-generator-cli.jar
  → codegen/.generated/<lang>/            (temp output)
  → submodules/<lang>/                    (final SDK code)
  → make after-gen                        (run inside the submodule)
```

Each `make <lang>` runs `codegen/generate-<lang>.bash`. Keys of `codegen/config-<lang>.json` become
`{{varName}}` variables in the mustache templates.

| Template dir                 | Config file                   | Submodule             | Generator (`-g`)  |
|------------------------------|-------------------------------|-----------------------|-------------------|
| `codegen/Templates/android/` | `codegen/config-android.json` | `submodules/android/` | `android`         |
| `codegen/Templates/csharp/`  | `codegen/config-dotnet.json`  | `submodules/dotnet/`  | `csharp`          |
| `codegen/Templates/dart/`    | `codegen/config-dart.json`    | `submodules/dart/`    | `dart`            |
| `codegen/Templates/go/`      | `codegen/config-go.json`      | `submodules/go/`      | `go`              |
| `codegen/Templates/java/`    | `codegen/config-java.json`    | `submodules/java/`    | `java`            |
| `codegen/Templates/nodejs/`  | `codegen/config-node.json`    | `submodules/node/`    | `typescript-node` |
| `codegen/Templates/php/`     | `codegen/config-php.json`     | `submodules/php/`     | `php`             |
| `codegen/Templates/python/`  | `codegen/config-python.json`  | `submodules/python/`  | `python`          |
| `codegen/Templates/swift/`   | `codegen/config-swift.json`   | `submodules/swift/`   | `swift6`          |

Template dir names don't always match submodule names (`csharp` → `dotnet`, `nodejs` → `node`).

## Key commands

Root repo:

```bash
make sdk       # Generate all SDKs
make <lang>    # Generate one SDK: android, dart, dotnet, go, java, node, php, python, swift
make update    # Fetch the latest API spec
make format    # Format Python scripts with Black (line-length=120)
make mypy      # Type check Python scripts
```

Inside `submodules/<lang>/` (except `android`, which is a demo app without these targets):

```bash
make test       # Run SDK tests
make after-gen  # Post-generation steps: formatting, example insertion into docs, etc. (varies by SDK)
```

## Post-generation processing

- Java and PHP API files are split into per-request classes by `codegen/Tools/split-java-file.py` and
  `codegen/Tools/split-php-file.py`.
- Every `codegen/generate-<lang>.bash` except android runs `make after-gen` in the submodule, which formats
  code and inserts examples into docs (`scripts/insert-example*.bash` in each submodule).

## SDK repository branches

Each SDK submodule is a standalone GitHub repo with its own default branch — `main` for all SDKs
**except `go`, whose default is `v4`**. Release work ships on a `release-<version>` branch as a draft
pull request into that default branch. See [`doc/branches.md`](doc/branches.md) for the full per-SDK
repository/branch table and details.

## Common requirements for making changes in SDK code

- Don't commit or push by yourself. You may pull and stage changes in git.
- On Windows, run all scripts in WSL.

1. After making changes, run the tests with `make test` (or a similar target in the `Makefile`) in the SDK
   submodule.
2. Port your SDK code changes to the mustache templates. If the template for the changed code is not in
   `codegen/Templates` yet, download it from the openapi-generator repository into the matching
   `codegen/Templates/<lang>/` directory and edit the local copy.
3. Ensure the generated code is the same as your new code:
   1. Stage your changes in the SDK submodule.
   2. Run `make <lang>` in the root repo (see the [Key commands](#key-commands)).
   3. After the generation script finishes, ensure there are no unstaged changes in the SDK submodule.
   4. If the generated code differs from your code, fix the templates and repeat.
4. Once the generated code matches, the task is done.

## CI security checks (zizmor)

This repository runs [zizmor](https://docs.zizmor.sh/) on its own GitHub Actions workflows and on those of
every SDK submodule (`.github/workflows/zizmor.yml`, config in `.github/zizmor.yml`); the job fails on any
finding. The SDK repositories have no zizmor workflow or config of their own, so a workflow change in an
SDK must pass this audit once its submodule is bumped here.

- Pin third-party actions to a commit SHA with a version comment: `uses: owner/action@<sha> # vX.Y.Z`.
  GitHub's own `actions/*` may use a major tag. Dependabot is not enabled yet, so bump pins by hand
  (new SHA and new version comment together).
- Declare `permissions:` explicitly and set `persist-credentials: false` on `actions/checkout`.
- Run `make zizmor` before pushing workflow changes. See [`doc/zizmor-rollout-plan.md`](doc/zizmor-rollout-plan.md).

## Scripting requirements

- Never use Perl — neither standalone Perl scripts nor inline one-liners (e.g. `perl -pe` in shell scripts or
  Makefiles). Use Python instead.

## Files shared by all SDKs

`LICENSE`, `scripts/check-badges.bash`, `scripts/coverage.py` and `scripts/publish-coverage.py` are copied
into every SDK by [`scripts/copy-common-files.bash`](scripts/copy-common-files.bash) `<sdk-dir>`, which each
`codegen/generate-<sdk>.bash` calls; `--no-coverage` leaves out the two coverage scripts for android, which
is exempt from the coverage requirements. Edit them here, never the copies in the submodules. To share
another file with all SDKs, add it to that script.

## Test coverage requirements

Every generated SDK must satisfy two coverage bars — **API endpoint coverage ≥ 80%** and **line code
coverage ≥ 80%** (the latter enforced by a per-SDK CI gate). `submodules/android` is exempt (it is a demo
app, not an SDK). Regenerating or changing an SDK must not drop either metric below 80%. Every SDK
measures line coverage with `make cover`, which ends in the shared `scripts/coverage.py` gate and
produces the README coverage badge. See
[`doc/test-coverage-requirements.md`](doc/test-coverage-requirements.md) for the full requirements and
[`doc/coverage-badges.md`](doc/coverage-badges.md) for how the coverage badges work.

## Releases and versioning

See [`doc/ReleaseWorkflow.md`](doc/ReleaseWorkflow.md) for the release steps and toolchain requirements, and
[`doc/versioning.md`](doc/versioning.md) for per-SDK version formats (set by `scripts/new-version.py`).

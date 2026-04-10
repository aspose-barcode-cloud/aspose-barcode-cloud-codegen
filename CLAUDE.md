# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Does

Generates SDKs for Aspose.BarCode Cloud REST API across 8 languages using OpenAPI Generator. Each SDK lives in a git submodule under `submodules/`. Templates and configs in `codegen/` control what gets generated.

## Code Generation Pipeline

```
spec/aspose-barcode-cloud.json          (OpenAPI 3.0 spec)
  + codegen/config-<lang>.json          (per-language config: versions, package names, URLs)
  + codegen/Templates/<lang>/*.mustache (customized mustache templates)
  → codegen/Tools/openapi-generator-cli.jar
  → codegen/.generated/<lang>/          (temp output)
  → submodules/<lang>/                  (final SDK code)
  → make after-gen                      (formatting, linting, example insertion)
```

Template variable reference: config JSON keys become `{{varName}}` in mustache templates. Original upstream templates are at https://github.com/OpenAPITools/openapi-generator/tree/master/modules/openapi-generator/src/main/resources/

## Key Commands

```bash
make sdk              # Generate ALL SDKs
make <lang>           # Generate one SDK: android, dart, dotnet, go, java, node, php, python
make update           # Fetch latest API spec from Aspose Cloud
make format           # Format Python scripts with Black (line-length=120)
```

Inside each `submodules/<lang>/`:
```bash
make test             # Run SDK tests
make after-gen        # Post-generation: format, lint, insert examples, add deprecation warnings
```

## Workflow for Changing SDK Code

Per `Agents.md` — this is the required workflow:

1. Make changes in the SDK submodule (`submodules/<lang>/`)
2. Run `make test` in the submodule to verify
3. Update the corresponding mustache template in `codegen/Templates/<lang>/`
4. Stage your submodule changes, then run `make <lang>` from the repo root
5. Verify there are no unstaged changes in the submodule (generated code must match your changes)
6. Fix templates if generated code diverges
7. Do NOT commit or push — only stage changes

## Directory Mapping

| Template dir                 | Config file                   | Submodule             | Generator name  |
|------------------------------|-------------------------------|-----------------------|-----------------|
| `codegen/Templates/android/` | `codegen/config-android.json` | `submodules/android/` | android         |
| `codegen/Templates/csharp/`  | `codegen/config-dotnet.json`  | `submodules/dotnet/`  | csharp-netcore  |
| `codegen/Templates/dart/`    | `codegen/config-dart.json`    | `submodules/dart/`    | dart            |
| `codegen/Templates/go/`      | `codegen/config-go.json`      | `submodules/go/`      | go              |
| `codegen/Templates/java/`    | `codegen/config-java.json`    | `submodules/java/`    | java            |
| `codegen/Templates/nodejs/`  | `codegen/config-node.json`    | `submodules/node/`    | typescript-node |
| `codegen/Templates/php/`     | `codegen/config-php.json`     | `submodules/php/`     | php             |
| `codegen/Templates/python/`  | `codegen/config-python.json`  | `submodules/python/`  | python          |

Note: template dir names don't always match submodule names (e.g., `csharp` vs `dotnet`, `nodejs` vs `node`).

## Post-Generation Processing

Large API files get split into per-request classes using Python helpers in `codegen/Tools/`:
- `split-java-file.py`, `split-cs-file.py`, `split-php-file.py`

Each language's `after-gen` runs: auto-formatting, example insertion (`scripts/insert-example.bash`), deprecation warning injection, and documentation formatting.

## Release Process

1. `./scripts/start-release.bash` — creates release branches, bumps versions in all `config-*.json`
2. `make sdk` — regenerate all SDKs
3. Push PRs, review, merge to main
4. Tag releases as `vYY.MM`, publish to package registries

Version format: `YY.MM.patch` (Go uses `4.YYMM.patch`, Dart uses `4.YY.MM`). Version updates are handled by `scripts/new-version.py`.

## Requirements

Java runtime (for openapi-generator-cli.jar), Python 3 (for scripts, Black formatter), Bash (WSL on Windows). Each SDK needs its own toolchain for `make test` / `make after-gen`.

Code formatting
===============

Requirement
-----------

> Follows code formatting conventions of target language.

(Cloud SDK Requirements → Code quality.)

How this repository satisfies it
--------------------------------

Every SDK generator except the Android demo app ends by running
`make after-gen` inside the SDK submodule:

```bash
pushd "$targetDir" && make after-gen && popd >/dev/null
```

`after-gen`'s `format` step runs the language's canonical formatter over the
**whole tree** — generated source *and* hand-written tests:

| SDK    | `make format` runs |
|--------|--------------------|
| Dart   | `dart format .` |
| Swift  | `swiftformat .` |
| Python | `black --line-length=120 … tests/ scripts/ snippets/ …` |
| .NET   | `dotnet format` |
| Go     | `scripts/format.sh` (`gofmt`) |
| Java   | `scripts/format.bash` |
| Node   | `npm run format` (Prettier) |
| PHP    | php-cs-fixer |

For these SDKs, `make after-gen` formats everything, so freshly generated code
is in the formatter's canonical form. Android is excluded because this
repository generates a demo app for it rather than an SDK package.

Hand-written tests and generation
----------------------------------

Test files are **hand-written**, not generated — regeneration never overwrites
them. But the `format` step above *does* reformat them. So tests must be
committed formatter-clean; otherwise the next `make <sdk>` re-dirties them and
leaves spurious unstaged changes.

Check a tree without modifying it, e.g. for Swift:

```bash
cd submodules/swift && swiftformat --lint .
# 0/N files require formatting  → clean
```

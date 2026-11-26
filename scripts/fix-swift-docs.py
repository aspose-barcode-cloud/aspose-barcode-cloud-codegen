"""Document Swift enum cases and use valid enum values in generated examples."""

import json
import re
import sys
from pathlib import Path

BACK_LINKS = (
    "[[Back to Model list]](../README.md#documentation-for-models) "
    "[[Back to API list]](../README.md#documentation-for-api-endpoints) "
    "[[Back to README]](../README.md)"
)


def update_docs(spec_file: Path, models_dir: Path, docs_dir: Path) -> None:
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    schemas = spec.get("definitions", spec.get("components", {}).get("schemas", {}))
    defaults = {}

    for source in sorted(models_dir.glob("*.swift")):
        content = source.read_text(encoding="utf-8")
        enum = re.search(r"^public enum (\w+): String,", content, re.MULTILINE)
        if enum is None:
            continue
        name = enum.group(1)
        cases = [
            (case, raw)
            for case, raw in re.findall(r'^\s+case (\w+) = ("(?:\\.|[^"\\])*")$', content, re.MULTILINE)
            if json.loads(raw) != "unknown_default_open_api"
        ]
        if not cases:
            continue

        defaults[name] = name + "." + cases[0][0]
        lines = ["# " + name, ""]
        description = " ".join(schemas.get(name, {}).get("description", "").split())
        if description:
            lines.extend([description, ""])
        lines.extend(["## Allowable values", ""])
        for index, (case, raw) in enumerate(cases):
            bold = "**" if index == 0 else ""
            lines.append(f"* {bold}{name}.{case}{bold} (`{raw}`)")
        lines.extend(["", BACK_LINKS, "", "", ""])
        (docs_dir / (name + ".md")).write_text("\n".join(lines), encoding="utf-8")

    if defaults:
        # The generator emits Enum() even inside examples of nested request models.
        pattern = re.compile(r"\b(" + "|".join(re.escape(name) for name in defaults) + r")\(\)")
        for doc in sorted(docs_dir.glob("*.md")):
            original = doc.read_text(encoding="utf-8")
            updated = pattern.sub(lambda match: defaults[match.group(1)], original)
            if updated != original:
                doc.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    update_docs(*(Path(argument) for argument in sys.argv[1:]))

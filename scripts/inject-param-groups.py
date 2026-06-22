#!/usr/bin/env python3
"""Inject parameter-group metadata into the Generate (GET) operation of the spec.

The barcode ``generate`` GET operation declares ~30 flat query parameters, so the
generated SDK method takes ~30 arguments. This script tags each query parameter
that belongs to one of the ``*Params`` groups (BarcodeImageParams, QrParams,
Pdf417Params, Code128Params) -- the same grouping the ``GenerateParams`` body
model already uses -- so the per-language ``api.mustache`` templates can emit a
method that accepts the four grouped objects instead of the flat list, while
still serialising the values into the unchanged flat query string.

The mapping is derived from the spec itself (the properties of the four
``*Params`` sub-schemas), so it stays correct as the API evolves. ``data`` and
``dataType`` are intentionally left ungrouped. The script is idempotent.

Vendor extensions are legal per the OpenAPI Specification, section
"Specification Extensions": https://spec.openapis.org/oas/v3.0.4.html#specification-extensions
"""
import argparse
import json
import re
import typing
from pathlib import Path

GENERATE_PATH: typing.Final = "/barcode/generate/{barcodeType}"
GROUP_CONTAINER_SCHEMA: typing.Final = "GenerateParams"
GROUP_TYPE_SUFFIX: typing.Final = "Params"
_CAMEL_BOUNDARY: typing.Final = re.compile(r"(?<!^)(?=[A-Z])")


def camel_to_snake(name: str) -> str:
    return _CAMEL_BOUNDARY.sub("_", name).lower()


def camel_to_pascal(name: str) -> str:
    return name[:1].upper() + name[1:]


def resolve_type(schema: typing.Dict[str, typing.Any]) -> str:
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if "allOf" in schema and schema["allOf"] and "$ref" in schema["allOf"][0]:
        return schema["allOf"][0]["$ref"].split("/")[-1]
    if "type" in schema:
        return schema["type"]
    return ""


def build_field_to_group(
    schemas: typing.Dict[str, typing.Any],
) -> typing.Tuple[
    typing.Dict[str, typing.Dict[str, str]], typing.List[typing.Dict[str, str]]
]:
    """Return (field name -> group) and the ordered list of groups.

    A group is any ``GenerateParams`` property whose type name ends with
    ``Params`` (this excludes ``barcodeType`` and ``encodeData``).
    """
    container = schemas[GROUP_CONTAINER_SCHEMA]["properties"]
    groups: typing.List[typing.Dict[str, str]] = []
    field_to_group: typing.Dict[str, typing.Dict[str, str]] = {}
    for prop_name, prop_schema in container.items():
        type_name = resolve_type(prop_schema)
        if not type_name.endswith(GROUP_TYPE_SUFFIX):
            continue
        group = {
            "camel": prop_name,
            "snake": camel_to_snake(prop_name),
            "pascal": camel_to_pascal(prop_name),
            "type": type_name,
        }
        groups.append(group)
        for field_name in schemas[type_name]["properties"]:
            field_to_group[field_name] = group
    return field_to_group, groups


def inject(spec: typing.Dict[str, typing.Any]) -> int:
    """Tag the Generate GET query params in place; return the number tagged."""
    schemas = spec["components"]["schemas"]
    field_to_group, groups = build_field_to_group(schemas)

    operation = spec["paths"][GENERATE_PATH]["get"]
    operation["x-param-groups"] = groups
    operation["x-has-param-groups"] = True

    tagged = 0
    for parameter in operation["parameters"]:
        if parameter["in"] != "query":
            continue
        name = parameter["name"]
        if name not in field_to_group:
            continue
        group = field_to_group[name]
        parameter["x-param-group-snake"] = group["snake"]
        parameter["x-param-group-camel"] = group["camel"]
        parameter["x-param-group-pascal"] = group["pascal"]
        parameter["x-param-group-type"] = group["type"]
        tagged += 1
    return tagged


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", type=Path, help="OpenAPI spec JSON to read")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Where to write the augmented spec (defaults to in-place)",
    )
    args = parser.parse_args()

    spec = json.loads(args.input.read_text(encoding="utf-8"))
    tagged = inject(spec)
    destination = args.output if args.output is not None else args.input
    destination.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    group_count = len(spec["paths"][GENERATE_PATH]["get"]["x-param-groups"])
    print(f"Tagged {tagged} query params across {group_count} groups -> {destination}")


if __name__ == "__main__":
    main()

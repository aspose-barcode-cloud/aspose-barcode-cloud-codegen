"""Regression tests for Swift enum documentation post-processing."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_SPEC = importlib.util.spec_from_file_location("swift_docs", Path(__file__).parents[1] / "fix-swift-docs.py")
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
SWIFT_DOCS = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(SWIFT_DOCS)


class SwiftDocsTests(unittest.TestCase):
    def test_enum_docs_and_nested_examples_are_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            models = root / "models"
            docs = root / "docs"
            models.mkdir()
            docs.mkdir()
            spec = root / "spec.json"
            spec.write_text(json.dumps({"definitions": {"BarcodeType": {"description": "Barcode\ntypes."}}}))
            (models / "BarcodeType.swift").write_text(
                "public enum BarcodeType: String, Codable {\n"
                '    case qr = "QR"\n'
                '    case _none = "None"\n'
                '    case unknownDefaultOpenApi = "unknown_default_open_api"\n'
                "}\n"
            )
            (docs / "BarcodeType.md").write_text("Old empty properties table\n")
            api = docs / "GenerateAPI.md"
            api.write_text("let request = Request(type: BarcodeType(), nested: Params(type: BarcodeType()))\n")
            model = docs / "Request.md"
            model.write_text("# Request\n\nUnrelated model documentation.\n")

            SWIFT_DOCS.update_docs(spec, models, docs)

            enum_doc = (docs / "BarcodeType.md").read_text()
            self.assertIn("Barcode types.\n", enum_doc)
            self.assertIn('* **BarcodeType.qr** (`"QR"`)', enum_doc)
            self.assertIn('* BarcodeType._none (`"None"`)', enum_doc)
            self.assertNotIn("unknownDefaultOpenApi", enum_doc)
            self.assertEqual(
                api.read_text(), "let request = Request(type: BarcodeType.qr, nested: Params(type: BarcodeType.qr))\n"
            )
            self.assertEqual(model.read_text(), "# Request\n\nUnrelated model documentation.\n")
            snapshot = {file.name: file.read_bytes() for file in docs.iterdir()}
            SWIFT_DOCS.update_docs(spec, models, docs)
            self.assertEqual(snapshot, {file.name: file.read_bytes() for file in docs.iterdir()})

    def test_no_enums_leaves_docs_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            models = root / "models"
            docs = root / "docs"
            models.mkdir()
            docs.mkdir()
            spec = root / "spec.json"
            spec.write_text('{"components": {"schemas": {}}}')
            (models / "Request.swift").write_text("public struct Request: Codable {}\n")
            doc = docs / "Request.md"
            doc.write_text("# Request\n")
            SWIFT_DOCS.update_docs(spec, models, docs)
            self.assertEqual(doc.read_text(), "# Request\n")


if __name__ == "__main__":
    unittest.main()

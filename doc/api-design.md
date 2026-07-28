API design (no code smells)
===========================

Requirement
-----------

> API does not have "code smells" e.g. do not pass long list of parameters.

(Cloud SDK Requirements → Code quality.)

How this repository satisfies it
--------------------------------

Operations with many optional parameters group them into **typed parameter
objects** instead of a long, flat argument list. For the `generate` family the
options are grouped by concern:

* `BarcodeImageParams` — image format, size, colours, resolution, text location …
* `QrParams`, `Code128Params`, `Pdf417Params` — per-symbology options

so a call takes a few grouped objects rather than dozens of positional
arguments. Swift example:

```swift
GenerateAPI.generate(
    barcodeType: .qr,
    data: "Aspose.BarCode Cloud",
    barcodeImageParams: BarcodeImageParams(imageFormat: .png),
    qrParams: QrParams(qrErrorLevel: .levelM),
    apiConfiguration: client.apiConfiguration
)
```

The grouping is driven from the spec and applied during generation (see the
`Split generate params into groups` change). The generated doc comments label
each argument as `Grouped <name> parameters`, e.g.:

```
- parameter barcodeImageParams: (BarcodeImageParams) Grouped barcodeImageParams parameters.
- parameter qrParams: (QrParams) Grouped qrParams parameters.
```

Keeping parameters grouped in the spec is what keeps every generated SDK free of
the long-parameter-list smell.

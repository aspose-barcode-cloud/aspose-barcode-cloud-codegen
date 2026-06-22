#!/bin/bash
set -euo pipefail

# SWAGGER_SPEC_URL="https://barcode.qa.aspose.cloud/v4.0/barcode/swagger/spec"
SWAGGER_SPEC_URL="https://api.aspose.cloud/v4.0/barcode/swagger/spec"
# SWAGGER_SPEC_URL="http://localhost:47972/v4.0/barcode/swagger/spec"

curl "${SWAGGER_SPEC_URL}" > spec/aspose-barcode-cloud.json

# Re-apply codegen parameter-group metadata (vendor extensions consumed by the
# api.mustache templates to emit grouped generate() methods). A fresh fetch from
# the server does not include them; the injection is idempotent.
python scripts/inject-param-groups.py spec/aspose-barcode-cloud.json

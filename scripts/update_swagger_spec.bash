#!/bin/bash
set -euo pipefail

# SWAGGER_SPEC_URL="https://api.aspose.cloud/v3.0/barcode/swagger/spec"
SWAGGER_SPEC_URL="https://api.aspose.cloud/v4.0/barcode/swagger/spec"
# SWAGGER_SPEC_URL="http://localhost:47972/v3.0/barcode/swagger/spec"

curl "${SWAGGER_SPEC_URL}" > spec/aspose-barcode-cloud.json

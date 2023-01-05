#!/bin/bash
#
# Usage: ./add-new-submodule.bash ../aspose-barcode-cloud-dart
#
set -euo pipefail

rel_url="$1"
[[ $rel_url = "../aspose-barcode-cloud-"* ]] || (echo "Use relative urls like ../aspose-barcode-cloud-dart")
name="${rel_url#../aspose-barcode-cloud-}"
path="submodules/${name}"

echo git submodule add -- "${rel_url}" "${path}"

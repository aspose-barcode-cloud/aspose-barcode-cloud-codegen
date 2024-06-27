.PHONY: all
all: sdk

.PHONY: format
format: format-black

.PHONY: format-black
format-black:
	python -m black --line-length=120 --exclude submodules -v .

.PHONY: update
update:
	./scripts/update_swagger_spec.bash

.PHONY: openapi
openapi:
	curl "https://converter.swagger.io/api/convert?url=https://api.aspose.cloud/v3.0/barcode/swagger/spec" | jq '.' > spec/aspose-barcode-cloud-openapi.json

# Mark parameters as deprecated
.PHONY: deprecated
deprecated: openapi
	jq '.paths[][].parameters? |= map(if .description and (.description | startswith("DEPRECATED:")) then . + {"deprecated": true} else . end)' spec/aspose-barcode-cloud-openapi.json > spec/aspose-barcode-cloud-with-deprecated.json


# Making all SDKs
.PHONY: sdk
sdk:
	./scripts/generate-all.bash

.PHONY: android
android:
	cd codegen && ./generate-android.bash

.PHONY: dart
dart:
	cd codegen && ./generate-dart.bash

.PHONY: dotnet
dotnet:
	cd codegen && ./generate-dotnet.bash

.PHONY: go
go:
	cd codegen && ./generate-go.bash

.PHONY: java
java:
	cd codegen && ./generate-java.bash

.PHONY: node
node:
	cd codegen && ./generate-node.bash

.PHONY: php
php:
	cd codegen && ./generate-php.bash

.PHONY: python
python:
	cd codegen && ./generate-python.bash

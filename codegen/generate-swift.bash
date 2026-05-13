#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/swift"
targetDir="../submodules/swift"

if [ -d "$tempDir" ];
then
    rm -rf "$tempDir"
fi

# java -jar Tools/openapi-generator-cli.jar config-help -g swift5 ; exit 1
# java -DdebugModels -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g swift5 -o "$tempDir" -c config-swift.json > debugModels.swift.json ; exit
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g swift5 -o "$tempDir" -c config-swift.json > debugOperations.swift.json ; exit
java -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g swift5 -o "$tempDir" -c config-swift.json

mkdir -p "$targetDir/Sources"
rm -rf "$targetDir/Sources/AsposeBarcodeCloud"
mv "$tempDir/Sources/AsposeBarcodeCloud" "$targetDir/Sources/AsposeBarcodeCloud"

# OpenAPI Generator 7.8.0 emits Apple-only imports for the URLSession client
# when compiling on Linux. Keep the generated client SwiftPM-compatible in WSL.
perl -0pi -e 's/import Foundation\n#if !os\(macOS\)\nimport MobileCoreServices\n#endif/import Foundation\n#if canImport(FoundationNetworking)\nimport FoundationNetworking\n#endif\n#if canImport(MobileCoreServices)\nimport MobileCoreServices\n#endif/' "$targetDir/Sources/AsposeBarcodeCloud/URLSessionImplementations.swift"
perl -0pi -e 's/        } else {\n            if let uti = UTTypeCreatePreferredIdentifierForTag/        } else {\n            #if canImport(MobileCoreServices)\n            if let uti = UTTypeCreatePreferredIdentifierForTag/' "$targetDir/Sources/AsposeBarcodeCloud/URLSessionImplementations.swift"
perl -0pi -e 's/                return mimetype as String\n            }\n            return "application\/octet-stream"/                return mimetype as String\n            }\n            #endif\n            return "application\/octet-stream"/' "$targetDir/Sources/AsposeBarcodeCloud/URLSessionImplementations.swift"

# Keep the generated runtime warning-free under current Swift toolchains.
perl -0pi -e 's/extension String: CodingKey \{/extension Swift.String: Swift.CodingKey {/' "$targetDir/Sources/AsposeBarcodeCloud/Extensions.swift"
perl -0pi -e 's/}\s*\z/}\n\n#if compiler(>=5.5)\nextension OpenISO8601DateFormatter: \@unchecked Sendable {}\n#endif\n/' "$targetDir/Sources/AsposeBarcodeCloud/OpenISO8601DateFormatter.swift"
perl -0pi -e 's/\n            #else\n            return "application\/octet-stream"\s*\n            #endif/\n            #endif/' "$targetDir/Sources/AsposeBarcodeCloud/URLSessionImplementations.swift"
perl -0pi -e 's/private class SessionDelegate/private final class SessionDelegate/' "$targetDir/Sources/AsposeBarcodeCloud/URLSessionImplementations.swift"
cp Support/swift/*.swift "$targetDir/Sources/AsposeBarcodeCloud/"

rm -rf "$targetDir/docs"
mv "$tempDir/docs" "$targetDir/docs"

mv "$tempDir/.openapi-generator-ignore" "$targetDir/"
mv "$tempDir/.swiftformat" "$targetDir/"

mkdir -p "$targetDir/.openapi-generator"
mv "$tempDir/.openapi-generator/VERSION" "$targetDir/.openapi-generator/"
mv "$tempDir/.openapi-generator/FILES" "$targetDir/.openapi-generator/"

cp ../LICENSE "$targetDir/"

rm -rf "$tempDir"

# Test coverage requirements

Every generated SDK must satisfy two coverage bars. `submodules/android` is exempt from both — it is a
demo application that consumes the published Java SDK, so it has no API surface of its own to cover.

1. **API endpoint coverage — at least 80%.** At least 80% of the API operations defined in
   `spec/aspose-barcode-cloud.json` must be exercised by a test (no fewer than 8 of the 9 at the current
   surface). Every SDK currently covers all 9 operations (100%).
2. **Line code coverage — at least 80%, enforced by a per-SDK CI gate.** Each SDK's own CI fails the build
   when line coverage drops below 80%. The bar is reached with deterministic **offline** tests over the
   generated model / enum / serialization / core code (mirroring java's `GeneratedModelCoverageTest` and
   `SdkCoreCoverageTest`) on top of the live API tests, which run in CI via the
   `TEST_CONFIGURATION_ACCESS_TOKEN` secret.

Regenerating or changing an SDK must not drop either metric below 80%.

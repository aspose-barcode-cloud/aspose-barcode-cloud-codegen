Client configuration and identification
=======================================

Requirement
-----------

> * Set `x-aspose-client` header to indicate language and version of the SDK.
> * SDK API Client has configuration settings: `AppSID`, `AppKey`, `baseURI`,
>   `version`, `debug`.

(Cloud SDK Requirements → Implementation details.)

Client identification headers
-----------------------------

Every SDK sets two headers on each request; the names live in the language
templates under `codegen/Templates/<lang>/`:

* `x-aspose-client` — the SDK name (e.g. `swift sdk`, `nodejs sdk`)
* `x-aspose-client-version` — the SDK package version

These are driven by the configuration's `sdkName` / `sdkVersion` (or the package
version constant), so they stay in sync with the released version automatically.

Configuration settings
----------------------

| Setting | Notes |
|---------|-------|
| `clientId` (mandatory) | OAuth 2 client id |
| `clientSecret` (mandatory) | OAuth 2 client secret |
| `host` (optional) | defaults to `https://api.aspose.cloud/v4.0`; override for private cloud / test |
| `debug` (optional, per-SDK) | e.g. .NET debug logging; not a universal flag |

Additional settings exposed by the client configuration:

* `accessToken` — supply a token directly and skip the OAuth exchange
* `tokenURL` — OAuth token endpoint (`https://id.aspose.cloud/connect/token`)
* `sdkName` / `sdkVersion` — feed the `x-aspose-client*` headers
* request timeout — e.g. Swift `timeoutInterval` (default 300s)

See [authentication.md](authentication.md) for how `clientId`/`clientSecret`
become a bearer token.

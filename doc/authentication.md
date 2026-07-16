Authentication
==============

Requirement
-----------

> Use OAuth protocol for authentication.

(Cloud SDK Requirements → Implementation details.)

How this repository satisfies it
--------------------------------

Each SDK authenticates with **OAuth 2 client credentials**. The client is
configured with a `clientId` and `clientSecret`, exchanges them for a bearer
access token at the token endpoint, and then sends `Authorization: Bearer
<token>` on each request.

Defaults (Swift `AsposeBarcodeCloudConfiguration`, mirrored in the other SDKs):

* token URL — `https://id.aspose.cloud/connect/token`
* host — `https://api.aspose.cloud/v4.0`

The access token is fetched **lazily** on the first API call; an explicit
warm-up call is also available (e.g. Swift `client.authorize()`). A dedicated
auth interceptor injects the `Authorization` header on each authenticated
request.

If a caller already holds a token, it can configure the SDK with an
`accessToken` directly and skip the client-credentials exchange entirely. The
full settings list is in [configuration.md](configuration.md).

Cloud SDK Requirements
======================

Aspose's Cloud SDK requirements, split into one document per requirement and
mapped to how **this** codegen repository satisfies each one.

Source: the legacy internal wiki page "Cloud SDK Requirements". Where the
original wording is obsolete it is updated to current reality — for example
the OAuth 1 `AppSID`/`AppKey` credentials are now OAuth 2
`clientId`/`clientSecret`, and the base URL `https://api.aspose.com/v1.1` is
now `https://api.aspose.cloud/v4.0`.

| Requirement | Document |
|-------------|----------|
| Code quality — formatting | [formatting.md](formatting.md) |
| Code quality — documentation comments | [documentation.md](documentation.md) |
| Code quality — API design (no code smells) | [api-design.md](api-design.md) |
| Implementation — authentication | [authentication.md](authentication.md) |
| Implementation — client configuration & identification | [configuration.md](configuration.md) |
| Versioning | [versioning.md](versioning.md) |
| Release process | [ReleaseWorkflow.md](ReleaseWorkflow.md) |

Each document has the same shape: the **requirement** as originally stated, then
**how this repository satisfies it**, grounded in the actual generate scripts,
templates, and `make` targets.

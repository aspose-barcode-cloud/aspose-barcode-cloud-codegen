Release workflow
================

Requirements
------------

Windows: Bash, WSL, Python3, Java runtime
WSL: Debian (or Ubuntu) Bullseye
Debian packages: list in file `./doc/deb_packages.list`. To install run `./scripts/install-all-packages.bash` in your Debian on WSL

Steps:
1. Call `./scripts/start-release.bash`
    It will refresh the API spec (`spec/aspose-barcode-cloud.json`),
    create a `release-<version>` branch for each submodule,
    and update versions in `config*.json`.

2. Run `make-all.cmd`
    It will generate all SDKs with updated version and template.

3. Update the organization secret
   [`TEST_CONFIGURATION_ACCESS_TOKEN`](https://github.com/organizations/aspose-barcode-cloud/settings/secrets/actions).
   Refresh it less than 24 hours before running SDK integration tests.

4. Review all changes in submodules and open a draft PR on GitHub for each SDK,
    from its `release-<version>` branch into that SDK's default branch.

5. Merge all successful PRs into each SDK's default branch — `main` for every
    SDK except `go`, whose default branch is `v4` (see [branches.md](branches.md)).

6. Phase 2: create the release tag using the SDK-specific version convention
   and create a GitHub prerelease for that tag. Pay special attention to Go,
   Dart, and other SDKs whose tags do not use the standard `vYY.MM.P` form.

7. Publish the packages to their appropriate registries (NuGet, the Aspose
   Java repository, npm, PyPI, Packagist, pub.dev, Go modules). Packages are
   signed at publish time as a per-registry concern — e.g. NuGet packages are
   signed with a code-signing certificate — so confirm the signing setup for
   each registry.

8. Phase 3: after the package is available, promote the GitHub prerelease to
   the stable latest release. Include the changelog and release notes.

9. Link all updated branches and check `codegen` produces the same output.

See [versioning.md](versioning.md) for the version scheme and
[branches.md](branches.md) for the per-SDK repositories and default branches.

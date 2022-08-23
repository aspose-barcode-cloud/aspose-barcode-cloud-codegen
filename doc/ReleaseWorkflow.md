Release workflow
================

Requirements
------------

Windows: Bash, WSL, Python3, Java runtime
WSL: Debian (or Ubuntu) Bullseye
Debian packages: list in file `./doc/deb_packages.list`. To install run `./scripts/install-all-packages.bash` in your Debian on WSL
Steps:

0. Install all required runtimes and dependencies with `make init` for each submodule.

1. Call `./scripts/start-release.bash`
    It will create new branches for each submodule
    And update versions in `config*.json`.

2. Run `make-all.cmd`
    It will generate all SDKs with updated version and template.

3. Update secret <https://github.com/organizations/aspose-barcode-cloud/settings/secrets/actions> and set new value for `TEST_CONFIGURATION_ACCESS_TOKEN`. It should be updatead less than 24 hours ago.

4. Review all changes in submodules and push PR to GitHub.

5. Merge all successfull PRs to main.

6. Create release tags vYY.MM. Put attention to go, dart and other SDK with SemVer 0.x versions.

7. Publish new released packages to appropriate repository (NuGet, Maven, PyPi, NPM ...).

8. After package was published crate Release on GitHub. With changelog and release notes.

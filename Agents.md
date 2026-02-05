# Aspose.BarCode Cloud SDK and Codegen repository

This is repository with swagger generated SDK for Aspose.Barcode.Cloud service and code generating scripts. All sdk are submodules of this repo and located in `submodules` directory. Swagger specification of service API is located in `spec/aspose-barcode-cloud.json` file. Custom mustashe templates are located in `codegen/Templates` dir. Original templates for all languages are in <https://github.com/OpenAPITools/openapi-generator/tree/master/modules/openapi-generator/src/main/resources/> github. Sripts for generating SDK `codegen` directory. Some post processing are in Makefiles in all submodules repo.

## Common requirements for making changes in SDK code

0. Don't commit or push in repo by youreself. But you can pull and stage in git.
1. To run any scripts, use WSL if you're on Windows.
2. After making changes run tests with `make test` or similar comand in Makefile in SDK submodule repo.
3. Add changes to mustache templates after changes in SDK code are made. If you changed some code and template for it not in codegen/Templates dir. Download this template and made changes in local copy in codegen/Templates dir.
4. Enshure that generated code is the same as you new code. For it:
    4.1 Stage your changes in sdk submodule repo.
    4.2 Run `make <skd-name>` command in main repo. See Makefile for it.
    4.3 After generating script are end it work. Enshure there is no unstaged changes in sdk submodule.
    4.4 Fix templates if generated code are not the same as you new code.
5. After templates fixed, you can end your task.

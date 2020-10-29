@echo off

pushd codegen
for %%f in (generate-*.bat) do (
    %%f || echo %%f && goto :error
)
popd

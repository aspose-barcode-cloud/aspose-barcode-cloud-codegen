@echo off

for %%f in (generate-*.bat) do (
    %%f || echo %%f && goto :error
)

#!/bin/bash
set -euo pipefail

year=$1

git ls-files --recurse-submodules | xargs grep -FHn "${year}"

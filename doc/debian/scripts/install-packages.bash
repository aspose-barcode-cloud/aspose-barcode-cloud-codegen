#!/bin/bash
set -euo pipefail

cat ../packages.list | xargs sudo apt install

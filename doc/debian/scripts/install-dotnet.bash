#!/bin/bash
set -euo pipefail

# https://learn.microsoft.com/en-us/dotnet/core/install/linux-debian

wget https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb

sudo apt update
sudo apt install dotnet-sdk-8.0

#!/bin/bash
set -euo pipefail

# https://dart.dev/get-dart

sudo apt update

sudo apt install apt-transport-https gpg

wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-dart.gpg

echo 'deb [signed-by=/usr/share/keyrings/google-dart.gpg arch=amd64] https://storage.googleapis.com/download.dartlang.org/linux/debian stable main' | sudo tee /etc/apt/sources.list.d/dart_stable.list

sudo apt update
sudo apt install dart

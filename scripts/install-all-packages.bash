#!/bin/bash

set -u
sudo apt-get -y install wget
sudo apt-get install -y ca-certificates curl
# Add the Microsoft package signing key to list of trusted keys and add the package repository.
wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb
# Add Dart repository
wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/dart.gpg
echo 'deb [signed-by=/usr/share/keyrings/dart.gpg arch=amd64] https://storage.googleapis.com/download.dartlang.org/linux/debian stable main' | sudo tee /etc/apt/sources.list.d/dart_stable.list
# #Update
sudo apt-get update
#Install
deb_packages_list="../doc/deb_packages.list"
for package in $(cat ${deb_packages_list}) 
do
   echo ****Install  "$package"****
   pkg_ok=$(dpkg-query -W --showformat='${Status}\n' $package|grep "install ok installed")
   echo Checking for $package: $pkg_ok
    if [ "" = "$pkg_ok" ]; then
        echo "No $package. Setting up $package."
        sudo apt-get -y install $package
    fi
done

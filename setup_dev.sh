#!/usr/bin/env bash
if [ ! -d "djangosaml2" ]; then
  git clone -b develop https://github.com/crs4/djangosaml2.git
fi

cd djangosaml2 && python3 setup.py install
cd ../certs

./generate_development.sh

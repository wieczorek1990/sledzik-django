#!/bin/sh

set -eu

rm -rf mkcert/
git clone https://github.com/FiloSottile/mkcert.git
cd mkcert/

go build -o mkcert .
./mkcert -install
./mkcert -cert-file cert.crt -key-file cert.key \
  localhost 127.0.0.1 sledzik.soiree.tech

cp cert.crt cert.key ../certificates/
cd ../
rm -rf mkcert/

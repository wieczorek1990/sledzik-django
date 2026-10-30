#!/bin/sh

set -eu

mkdir -p certificates/

rm -rf mkcert/
git clone --depth=1 https://github.com/FiloSottile/mkcert.git
cd mkcert/

go build -o mkcert .
./mkcert -install
./mkcert -cert-file cert.crt -key-file cert.key\
 proud-amazingly-filly.ngrok-free.app

cp cert.crt cert.key ../certificates/
cd ../
rm -rf mkcert/

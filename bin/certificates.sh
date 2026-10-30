#!/bin/sh

set -eu

cd "$(dirname "$0")/.."

mkdir -p certificates/

rm -rf mkcert/
git clone --depth=1 https://github.com/FiloSottile/mkcert.git
cd mkcert/

go build -o mkcert .
./mkcert -install
./mkcert -cert-file cert.crt -key-file cert.key \
 localhost 127.0.0.1 ::1 sledzik.soiree.tech \
 proud-amazingly-filly.ngrok-free.app

cp cert.crt cert.key ../certificates/
cd ../
rm -rf mkcert/

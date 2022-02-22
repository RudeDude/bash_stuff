#!/bin/bash
set -e

## NATS error that caused me to re-investigate how we generate TLS certs
#  STREAM: Failed to start: x509: certificate relies on legacy Common Name field,
#  use SANs or temporarily enable Common Name matching with GODEBUG=x509ignoreCN=0

### Some reference links with good OpenSSL information
#
# Practical openssl usage examples
# - https://www.sslshopper.com/article-most-common-openssl-commands.html
# Has some Dockerfile and scripts that I haven't tested
# - https://github.com/lowply/private-root-ca-kit
# Long multi-OS and multi-language examples of setting your our CA system
# - https://tarunlalwani.com/post/self-signed-certificates-trusting-them/
# S.O. post I used to update this script originally
# - https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl/41366949#41366949

if [[ "$1" == "" ]]; then
  echo "Usage: $0 hostname <domain>"
  echo "   Will look for a cert auth (ca.crt and ca.key), if missing will generate a self signed CA."
  echo "   Will generate a key and certificate for (common name) HOST.DOMAIN with alternate names"
  echo "   Domain is optional, will default to threateye.io. Using '--' will remove domain entirely."
  exit 1
else
  HOST=$1
fi

if [[ "$2" == "" ]]; then
  DOM="threateye.io"
else
  if [[ "$2" == "--" ]]; then
    DOM=""
  else
    DOM=$2
  fi
fi

if [ -f ca.key ] && [ -f ca.crt ]; then
  echo Using exisiting CA.
else
  echo Need to create the self-signed cert authority...
  ## generateCA
  openssl req -new -newkey rsa:4096 -days 3650 -sha256 -x509 -nodes \
          -keyout ca.key -out ca.crt \
          -subj "/C=US/ST=Virginia/L=Crozet/O=CounterFlow AI, Inc./OU=IT/CN=CFAI Cert Authority"
  # Start a serial number counter file
  echo "FF00000001" > ca.srl
fi

## generateCSR
echo Generate key and \(self signed\) CRT...
openssl req -newkey rsa:4096 -days 3650 -sha256 -x509 -nodes \
  -keyout $HOST.key -out $HOST.crt \
  -subj "/C=US/ST=Virginia/L=Crozet/O=CounterFlow AI, Inc./OU=IT/CN=${HOST}.${DOM}" \
  -addext "subjectAltName = DNS:$HOST,DNS:${HOST}.${DOM},IP:127.0.0.1"

## generateServerCert
echo Generate CA signed cert
openssl x509 -sha256 -CA ca.crt -CAkey ca.key -in $HOST.crt -out $HOST-CAsigned.crt -days 3650

rm -f $HOST.crt && mv $HOST-CAsigned.crt $HOST.crt

echo Chmod files
chmod go-rw *.crt *.key *.srl

# Show cert contents command
# openssl x509 -noout -text -in nats-node.crt


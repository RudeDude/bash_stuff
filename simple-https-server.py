#!/usr/bin/env python3

# Started with code taken from http://www.piware.de/2011/01/creating-an-https-server-in-python/

import http.server
import ssl
import subprocess
import os
import argparse

HOSTNAME=os.uname()[1] + '.ccri.com'

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--directory', default=os.getcwd(),
                    help='serve this directory (default: ./)')
parser.add_argument('-p', '--port', default=4443,
                    help='listen on this port (default: 4443)')
parser.add_argument('-n', '--host', default=HOSTNAME,
                    help='hostname for certificate (default: ' + HOSTNAME +')' )
parser.add_argument('-k', '--keypath', default='~',
                    help='path to save keyfile and server cert (default: ~)')
args = parser.parse_args()

KEY  = os.path.expanduser(args.keypath + '/python-quick-https-key.pem')
CERT = os.path.expanduser(args.keypath + '/python-quick-https-cert.pem')

if( os.path.isfile(KEY) and os.path.isfile(CERT) ):
  print("Using existing key and cert")
else:
  print("Generating new key and cert")
  subprocess.run('openssl req -new -x509 -keyout '+ KEY
    +' -out '+ CERT
    +' -days 365 -nodes -subj "/C=US/ST=Virginia/L=Charlottesville/O=GA-CCRi/OU=Optix/'
    +'CN=' + args.host +'"', shell=True)

ctx = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(certfile=CERT, keyfile=KEY)

os.chdir(args.directory)

server_address = ('', int(args.port) )
httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler )
httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
print("Listening on port:", args.port)
print("Using hostname:", args.host)
httpd.serve_forever()


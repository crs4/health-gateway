#!/usr/bin/env bash

# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


export ROOT_BASE_DIR=$PWD/ca/root

if [ -d "${ROOT_BASE_DIR}" ]; then
    while true; do
        read -p "The Root CA already exists? This will erase all its data and the other CAs. Do you want to continue (y/n)? " YN
        case ${YN} in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done
fi

KEY_FILE=${ROOT_BASE_DIR}/ca.key.pem
CERT_FILE=${ROOT_BASE_DIR}/ca.cert.pem
INDEX_FILE=${ROOT_BASE_DIR}/index.txt
ROOT_CONF=${PWD}/openssl.cnf

rm -rf ${ROOT_BASE_DIR}
mkdir -p ${ROOT_BASE_DIR} ${ROOT_BASE_DIR}/certs ${ROOT_BASE_DIR}/newcerts ${ROOT_BASE_DIR}/crl
touch ${INDEX_FILE} ${INDEX_FILE}.attr
echo 1000 > ${ROOT_BASE_DIR}/serial

PASSKEY=hgwpwd

openssl genrsa -aes256 -passout pass:${PASSKEY} -out ${KEY_FILE} 4096
chmod 400 ${KEY_FILE}

openssl req -config ${ROOT_CONF} \
	-key ${KEY_FILE} \
	-passin pass:${PASSKEY} \
	-new -x509 \
	-days 7300 \
	-sha256 \
	-extensions v3_ca \
	-out ${CERT_FILE} \
	-subj "/C=IT/ST=Italy/O=Fake Certification Institution/OU=Fake Certification Authority/CN=Fake Certification Authority Root CA/"
chmod 444 ${CERT_FILE}

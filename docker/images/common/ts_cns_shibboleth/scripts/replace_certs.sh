#!/usr/bin/env bash

if [[ -z ${SERVER_NAME} ]]; then
    echo "Server name not found. Set SERVER_NAME env variable."
    exit 1
fi

SHIBBOLETH_BASE_DIR=/opt/shibboleth-idp
SHIBBOLETH_CREDENTIALS_DIR=${SHIBBOLETH_BASE_DIR}/credentials
SHIBBOLETH_METADATA=${SHIBBOLETH_BASE_DIR}/metadata/idp-metadata.xml

BACKCHANNEL_CERT=$(cat ${SHIBBOLETH_CREDENTIALS_DIR}/idp-backchannel.crt | head -n -1 | tail -n +2)
SIGNING_CERT=$(cat ${SHIBBOLETH_CREDENTIALS_DIR}/idp-signing.crt | head -n -1 | tail -n +2)
ENCRYPTION_CERT=$(cat ${SHIBBOLETH_CREDENTIALS_DIR}/idp-encryption.crt | head -n -1 | tail -n +2)


awk -v back="replace_back" -v backrepl="$BACKCHANNEL_CERT" \
 -v sign="replace_sign" -v signrepl="$SIGNING_CERT" \
 -v enc="replace_enc" -v encrepl="$ENCRYPTION_CERT" \
 -v server="replace_server" -v serverrepl="$SERVER_NAME" \
 '{gsub(back, backrepl); gsub(sign, signrepl); gsub(enc, encrepl); gsub(server, serverrepl); print}' \
 ${SHIBBOLETH_METADATA}.template > ${SHIBBOLETH_METADATA}

envsubst
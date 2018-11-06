#!/usr/bin/env bash


for cert in /cacerts/*.pem; do
    cp ${cert} /usr/local/share/ca-certificates/`basename ${cert}`.crt
done

update-ca-certificates

if [ -f /custom_entrypoint/docker-entrypoint.sh ]; then
    bash /custom_entrypoint/docker-entrypoint.sh $1
fi
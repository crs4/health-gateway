#!/usr/bin/env bash

for i in hgw_base web_base kafka hgw_frontend hgw_backend hgw_dispatcher consent_manager tscns
do
    docker push crs4/${i}
done

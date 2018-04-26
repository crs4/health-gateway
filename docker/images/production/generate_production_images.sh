#!/usr/bin/env bash
current_dir=$(pwd)
VERSION=$(cat ../../../VERSION)
if [ ! -d health_gateway ]; then
    cd ../../../
    git archive --prefix=health_gateway/ -o ${current_dir}/health_gateway.tar v${VERSION} 2>/dev/null
    if [ ! "$?" == "0" ]; then
        echo "Version not found"
        exit 1
    fi
    cd ${current_dir}
    tar -xvf health_gateway.tar
fi

# Create consent manager
cd ${current_dir}
cp -r health_gateway/consent_manager/ ${current_dir}/consent_manager/service
cp -r health_gateway/hgw_common/hgw_common ${current_dir}/consent_manager/service/

cd ${current_dir}/consent_manager/
docker build -t crs4/consent_manager:latest . && docker tag crs4/consent_manager:latest crs4/consent_manager:${VERSION}

cd ${current_dir}
rm -r  ${current_dir}/consent_manager/service

# Create hgw_backend
cp -r health_gateway/hgw_backend/ ${current_dir}/hgw_backend/service
cp -r health_gateway/hgw_common/hgw_common ${current_dir}/hgw_backend/service/

cd ${current_dir}/hgw_backend/
docker build -t crs4/hgw_backend:latest . && docker tag crs4/hgw_backend:latest crs4/hgw_backend:${VERSION}

cd ${current_dir}
rm -r  ${current_dir}/hgw_backend/service

# Create hgw_frontend
cp -r health_gateway/hgw_frontend/ ${current_dir}/hgw_frontend/service
cp -r health_gateway/hgw_common/hgw_common ${current_dir}/hgw_frontend/service/

cd ${current_dir}/hgw_frontend/
docker build -t crs4/hgw_frontend:latest . && docker tag crs4/hgw_frontend:latest crs4/hgw_frontend:${VERSION}

cd ${current_dir}
rm -r ${current_dir}/hgw_frontend/service

# Create hgw_dispatcher
cp -r health_gateway/hgw_dispatcher/ ${current_dir}/hgw_dispatcher/service

cd ${current_dir}/hgw_dispatcher/
docker build -t crs4/hgw_dispatcher:latest . && docker tag crs4/hgw_dispatcher:latest crs4/hgw_dispatcher:${VERSION}

cd ${current_dir}
rm -r ${current_dir}/hgw_dispatcher/service
rm -r ${current_dir}/health_gateway
rm -r ${current_dir}/health_gateway.tar
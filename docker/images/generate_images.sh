#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
VERSION=$1
if [ ! -d health_gateway ]; then
    cd ${DIR}/../../
    git archive --prefix=health_gateway/ -o ${DIR}/health_gateway.tar HEAD
    res=$?
    if [ ! "$res" == "0" ]; then
        echo ${res}
        echo "Version not found"
        exit 1
    fi
    cd ${DIR}
    tar -xvf health_gateway.tar
fi

cd ${DIR}

# Create Kafka image
docker build -t crs4/kafka:latest ${DIR}/kafka
docker tag crs4/kafka:latest crs4/kafka:$VERSION

# # Create Spid images
# docker build -t crs4/spid-testenv-identityserver:latest ${DIR}/spid_testenv_identityserver
# docker build -t crs4/spid-testenv-backoffice:latest ${DIR}/spid_testenv_backoffice

# # Create TS/CNS image
# docker build -t crs4/tscns:latest ${DIR}/tscns
# docker tag crs4/tscns:latest crs4/tscns:$VERSION

# Create base image
docker build -t crs4/hgw_base:latest ${DIR}/base
docker tag crs4/hgw_base:latest crs4/hgw_base:$VERSION

# Create web_base image
docker build -t crs4/web_base:latest ${DIR}/web_base
docker tag crs4/web_base:latest crs4/web_base:$VERSION


# Create consent manager
cp -r health_gateway/consent_manager/ ${DIR}/consent_manager/service
cp -r health_gateway/hgw_common/hgw_common ${DIR}/consent_manager/service/
docker build -t crs4/consent_manager:latest ${DIR}/consent_manager
docker tag crs4/consent_manager:latest crs4/consent_manager:$VERSION
rm -r  ${DIR}/consent_manager/service

# Create hgw_backend
cp -r health_gateway/hgw_backend/ ${DIR}/hgw_backend/service
cp -r health_gateway/hgw_common/hgw_common ${DIR}/hgw_backend/service/
docker build -t crs4/hgw_backend:latest ${DIR}/hgw_backend
docker tag crs4/hgw_backend:latest crs4/hgw_backend:$VERSION

rm -r  ${DIR}/hgw_backend/service

# Create hgw_frontend
cp -r health_gateway/hgw_frontend/ ${DIR}/hgw_frontend/service
cp -r health_gateway/hgw_common/hgw_common ${DIR}/hgw_frontend/service/
docker build -t crs4/hgw_frontend:latest ${DIR}/hgw_frontend
docker tag crs4/hgw_frontend:latest crs4/hgw_frontend:$VERSION

rm -r ${DIR}/hgw_frontend/service

# Create hgw_dispatcher
cp -r health_gateway/hgw_dispatcher/ ${DIR}/hgw_dispatcher/service
docker build -t crs4/hgw_dispatcher:latest ${DIR}/hgw_dispatcher/
docker tag crs4/hgw_dispatcher:latest crs4/hgw_dispatcher:$VERSION

rm -r ${DIR}/hgw_dispatcher/service

# Create destination_mockup
cp -r health_gateway/destination_mockup/ ${DIR}/destination_mockup/service
docker build -t crs4/destination_mockup:latest ${DIR}/destination_mockup/
docker tag crs4/destination_mockup:latest crs4/destination_mockup:$VERSION

rm -r ${DIR}/destination_mockup/service

# Create source_enpoint_mockup
cp -r health_gateway/source_endpoint_mockup/ ${DIR}/source_endpoint_mockup/service
docker build -t crs4/source_endpoint_mockup:latest ${DIR}/source_endpoint_mockup/
docker tag crs4/source_endpoint_mockup:latest crs4/source_endpoint_mockup:$VERSION

rm -r ${DIR}/source_endpoint_mockup/service

# Create performance_test_endpoint
cp -r health_gateway/performance_test_endpoint/ ${DIR}/performance_test_endpoint/service
docker build -t crs4/performance_test_endpoint:latest ${DIR}/performance_test_endpoint/
docker tag crs4/performance_test_endpoint:latest crs4/performance_test_endpoint:$VERSION
rm -r ${DIR}/performance_test_endpoint/service

rm -r ${DIR}/health_gateway
rm -r ${DIR}/health_gateway.tar

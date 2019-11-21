#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
DEV=$1
NO_CACHE=$2
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

function tag_new_version() {
    SERVICE=$1
    local DIR=$2

    VERSION=$(cat ${DIR}/VERSION)
    LATEST_IMAGE_ID=$(docker images | grep crs4/$SERVICE | grep latest | awk '{print $3}')
    VERSION_IMAGE_ID=$(docker images | grep crs4/$SERVICE | grep ${VERSION} | awk '{print $3}')
    echo $LATEST_IMAGE_ID
    echo $VERSION_IMAGE_ID
    if [ "$LATEST_IMAGE_ID" != "$VERSION_IMAGE_ID" ]; then
        IFS='.' # dot (.) is set as delimiter
        read -ra VERSION_PART <<< "$VERSION" # str is read into an array as tokens separated by IFS
        IFS=' ' # reset to default value after usage
        LAST_NUM=${VERSION_PART[2]}
        docker tag crs4/$SERVICE:latest crs4/$SERVICE:1.0.$(($LAST_NUM + 1))
        echo "Tagged new version 1.0.$(($LAST_NUM + 1))"
        if [ "$DEV" != "dev" ]; then
            echo -n "1.0.$(($LAST_NUM + 1))" > ${DIR}/VERSION
        fi
    else
        echo "Last version already present"
    fi
}

# Create hgw_base, web_base, kafka images
for image in hgw_base web_base kafka; do
    docker build -t crs4/$image:latest ${DIR}/$image
    tag_new_version $image ${DIR}/$image
done

for image in consent_manager hgw_backend hgw_frontend hgw_dispatcher; do
    cp -r health_gateway/$image/ ${DIR}/$image/service
    cp -r health_gateway/hgw_common/hgw_common ${DIR}/$image/service/
    docker build -t crs4/$image:latest ${DIR}/$image
    tag_new_version $image ${DIR}/$image
    rm -r  ${DIR}/$image/service
done

# # Create Spid images
# docker build -t crs4/spid-testenv-identityserver:latest ${DIR}/spid_testenv_identityserver
# docker build -t crs4/spid-testenv-backoffice:latest ${DIR}/spid_testenv_backoffice

# # Create TS/CNS image
docker build -t crs4/tscns:latest ${DIR}/tscns
docker tag crs4/tscns:latest crs4/tscns:$VERSION

# Create destination_mockup
cp -r health_gateway/destination_mockup/ ${DIR}/destination_mockup/service
docker build -t crs4/destination_mockup:latest ${DIR}/destination_mockup/
# docker tag crs4/destination_mockup:latest crs4/destination_mockup:$VERSION
rm -r ${DIR}/destination_mockup/service

# # Create source_enpoint_mockup
cp -r health_gateway/source_endpoint_mockup/ ${DIR}/source_endpoint_mockup/service
docker build -t crs4/source_endpoint_mockup:latest ${DIR}/source_endpoint_mockup/
# docker tag crs4/source_endpoint_mockup:latest crs4/source_endpoint_mockup:$VERSION
rm -r ${DIR}/source_endpoint_mockup/service


# # Create performance_test_endpoint
# cp -r health_gateway/performance_test_endpoint/ ${DIR}/performance_test_endpoint/service
# docker build -t crs4/performance_test_endpoint:latest ${DIR}/performance_test_endpoint/
# docker tag crs4/performance_test_endpoint:latest crs4/performance_test_endpoint:$VERSION
# # rm -r ${DIR}/performance_test_endpoint/service

rm -r ${DIR}/health_gateway
rm -r ${DIR}/health_gateway.tar

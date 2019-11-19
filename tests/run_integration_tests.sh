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


#set -e

PROGRAM_NAME=$0
NO_SPID="false"
SLEEP_TIME=5
message_received=0

function usage {
    echo "usage: ${PROGRAM_NAME} [-s] [-h]"
    echo " -s       specify the time to wait before publishing data/checking data received. Default ${SLEEP_TIME} seconds"
    echo " -n       it runs without spid containers. It means that the containers has to be run separately"
    echo " -h       print this message"
}

if [ $# -ge 1 ]; then
    case "$1" in
            -h)
                usage
                exit 0
                ;;

            -s)
                if [ "$#" = 1 ]; then
                    echo ERROR: Missing param for -s option
                    exit 1
                fi
                SLEEP_TIME=$2
                ;;

            -n)
                NO_SPID="true"
                ;;
    esac
fi

DIR=$(pwd)
INTEGRATION_DOCKER_DIR=${DIR}/../docker/environments/development/

finish(){
    ret=$?
    cd ${INTEGRATION_DOCKER_DIR}
    if [ "$NO_SPID" == "true" ]; then
        make down
    else
        make down_with_spid
    fi

    if [ "$message_received" -eq 0 ]; then
        echo "TESTS FAILED"
    else
        echo "TESTS OK"
    fi
    cd ${DIR}

}
trap finish EXIT

prepare_docker(){
    cd ${INTEGRATION_DOCKER_DIR}
    make down_with_spid  # This will work if the previous run was with or without spid
    if [ "$NO_SPID" == "true" ]; then
        make build_init_db_rund
    else
        make build_init_db_rund_with_spid
    fi
}

check_identity_server_up(){
    echo "Waiting identity server. This can take a while"
    IP_ADDRESS=$(docker ps | grep spid-testenv-identityserver_1 | awk '{print $1}' |
        xargs docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
    PORT_OPENED=1
    while [ "$PORT_OPENED" != "0" ]
    do
        OUTPUT=$(nmap -p 9443 ${IP_ADDRESS} | grep open 2>&1)
        PORT_OPENED=$?
    done
    echo "Identity server up"

}

run_unittest(){
    echo "RUNNING TESTS"
    cd ${DIR}
    cd integration_tests
    python3 tests.py

}

publish_data(){
    echo PUBLISH DATA
    cd ${INTEGRATION_DOCKER_DIR}
    ret=100
    set +e
    trap - EXIT
    while [ "${ret}" != 0 ]
    do
        sleep ${SLEEP_TIME}
        docker-compose exec source_endpoint_mockup python3 manage.py publish_data data/ -c
        ret=$?;
        if [ ${ret} != 0 ] ; then
        echo "ERROR: source cannot send data (no connectors?). Retrying in ${SLEEP_TIME}..."
        fi
    done
    set -e
    trap finish EXIT

}

check_message_received(){
    cd ${INTEGRATION_DOCKER_DIR}
    for container in kafka_destination_mockup rest_destination_mockup; do
        echo Check message received for ${container}
        message_received=0
        while [ "${message_received}" -eq 0 ]
        do
            sleep ${SLEEP_TIME}
            message_received=$(docker-compose exec ${container} ls -1 /tmp/msgs | wc -l)
            echo "message received: ${message_received}, should be > 0"
        done
    done
}

prepare_docker
check_identity_server_up
#check_containers_up # does not seem to work well (especially on mac), anyway it is someway redundant
run_unittest
publish_data
check_message_received


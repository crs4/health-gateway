#!/usr/bin/env bash

function usage {
    echo "Creates certificates for CAs and for services. By default it creates web and kafka certs for consentmanager hgwfrontend hgwbackend. If you need other services specify them"
    echo "usage: ${0} [-s] [-h] [list of additional services]"
    echo " -o          specify output dir [with respect to certs]. If not present it will use the current dir"
    echo " -c --clean  cleans the certificates folders forcibly"
    echo " -h          print this message"
}

if [ $# -ge 1 ]; then
    case "$1" in
        -h)
            usage
            exit 1
            ;;
        -o)
            if [ "$#" = 1 ]; then
                echo ERROR: Missing param for -o option
                exit 1
            fi
            OUTPUT_DIR=$2
            ;;
        -c|--clean)
            echo "Removing certs/ca"
            sudo rm -rf certs/ca
            echo "certs/kafka"
            sudo rm -rf certs/kafka
            echo "certs/root"
            sudo rm -rf certs/root
            echo "certs/web"
            sudo rm -rf certs/web
            echo "...done!"
            sleep 2
    esac
fi

if [ ! -d "djangosaml2" ]; then
  git clone -b develop https://github.com/crs4/djangosaml2.git
fi

cd djangosaml2 && python3 setup.py install
cd ../certs

keytool 2>/dev/null || sudo apt install openjdk-13-jre-headless -y

./generate_development.sh $OUTPUT_DIR

mkdir -p ca/kafka/certs
sudo cp -r kafka/certs/* ca/kafka/certs

for TGT_HOST in consentmanager destinationmockup spid-testenv-identityserver spid-testenv-backoffice hgwbackend
hgwfrontend kafka tscns; do
    ping ${TGT_HOST} -c 1 2>&1 1>/dev/null || sudo bash -c 'echo "127.0.0.1 ${TGT_HOST}" >> /etc/hosts'
done
[![Build Status](https://travis-ci.org/crs4/health-gateway.png)](https://travis-ci.org/crs4/health-gateway)

# Health Gateway Project

Health Gateway is a system that allows a citizen to authorize the tranfer of his/her clinical data from a Source to a Destination

# Run Health Gateway locally

To run Health Gateway locally you will need docker [https://www.docker.com/] and docker-compose.
The development environment we'll run, with all the hgw services, one Destination and one Source.
To run the HGW follow this steps

1. Clone the repository
2. Create the development certs:
    1. move into certs/ dir and then follow one of the two steps
        1. METHOD 1: run the script `generate_development.sh`. This will create a ca/ directory with all the necessary files
        2. METHOD 2: if you don't have bash (i.e., you're using Windows) you can build the docker images by running `docker build -t hgw_certs and .`
    
3. Move to `docker/environments/integration` directory and launch `make_run_with_tscns` to run all the services

## File host

To make the development environment work you need to add the following entries to your file host:

* 127.0.0.1 consentmanager
* 127.0.0.1 destinationmockup
* 127.0.0.1 spid-testenv-identityserver
* 127.0.0.1 spid-testenv-backoffice
* 127.0.0.1 hgwbackend
* 127.0.0.1 hgwfrontend
* 127.0.0.1 kafka

## NB
Install the 'keytool' package, which is part of the standard java distribution.
Use 'hgwpwd' as a password for certificates.

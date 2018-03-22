# Health Gateway Project


Health Gateway is a system that allows a citizen to authorize the tranfer of his/her clinical data from a Source to a Destination

# Requirements

Health Gateway is mainly written using Python 3. To install Python requirements launch 

```bash
pip3 install -r requirements
```

To create certs from the scripts in  `certs` directory you will need openssl and keytool

Finally to launch integration_tests you will need `nmap` 

# Get started

1. Clone the repository
2. Move into `certs` dir and generate all necessary certificates
3. Move to `docker/environments/development` directory and launch `make build` and `make init_db_run` to run a 
   developement environment

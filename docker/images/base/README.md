# Health Gateway Base image

This image is the base upon which other hgw related images are created. It has installed 
some common software and handle certification authorities.
Infact it allows to add some custom CA (Certification Authority) to system trusted ones. 

To add CAs you want to trust, mount their certs in the volume /cacerts/ with cert

The entrypoint just calls the `update-ca-certificates` command and then execute the script
in `/custom_entrypoint/docker-entrypoint.sh` if it exists.

## Run

An example of execution of a container is

`docker run -it -v mycert.pem /cacerts/mycert.pem crs4/hgw_base`

Notice that this image doesn't do anything useful and it is meant to be extended by other images
# Health Gateway Web base image

This image is built starting from crs4/hgw_base. It is an image for Django web applications 
that runs using nginx. The web server is configured for https and needs your certs files to be
mounted in volume `/container/web_certs/`. The key and certs file MUST be called cert.pem and key.pem
 It allows to specify the HTTPS port using the env variable `HTTP_PORT`

The Django module has to be mounted in volume `/container/service/`.

The first time the container is created, the entrypoint will create the Django database and 
load initial_data. If you want to load some other data, mount the Django fixtures in the volume
`/container/fixtures`

## Run

An example to run the command is:

```bash
docker run -it -e HTTP_PORT=8000 \ 
    -v my_django_app/:/container/service/ \ 
    -v mycacert.pem:/cacerts/mycacert.pem \
    -v my_web_server_cert.pem:/container/web_certs/cert.pem \
    -v my_web_server_key.pem:/container/web_certs/key.pem
    crs4/web_base
```  
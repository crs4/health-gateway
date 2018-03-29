# Consent Manager image

This is the image with Consent Manager service. It is based on crs4/web_base and it has
the Consent Manager service already installed, so you don't need to mount the Django application.

You still need to mount other files:
 * CA certs (if needed)
 * web server certs:
 * YAML configuration required by the service (an example is [here](https://github.com/crs4/health-gateway/blob/develop/docker/environments/common/config_files/consent_manager_config.yml)).
   It has to mounted in /etc/hgw_service/consent_manager_config.yaml

## Run

An example run command is:

```bash
docker run -it -e HTTP_PORT=8000 \ 
    -v consent_manager_config.yaml:/etc/hgw_service/consent_manager_config.yml
    -v mycacert.pem:/cacerts/mycacert.pem \
    -v my_web_server_cert.pem:/container/web_certs/cert.pem \
    -v my_web_server_key.pem:/container/web_certs/key.pem \
    crs4/consent_manager
```  
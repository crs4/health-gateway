# Health Gateway Backend image

This is the image with Health Gateway Backend service. It is based on crs4/web_base and it has
the Health Gateway Backend service already installed, so you don't need to mount the Django application.

You still need to mount other files:
 * CA certs (if needed)
 * web server certs:
 * YAML configuration required by the service (an example is [here](https://github.com/crs4/health-gateway/blob/develop/docker/environments/common/config_files/hgw_backend_config.yml)).
   It has to mounted in /etc/hgw_service/hgw_backend_config.yaml
 * Kafka cert, key and CA files in `/container/client_certs/` needed by the service to connect to kafka.
   (N.B.: Be aware to specify the correct path of the certs in the config file)

## Run

An example run command is:

```bash
docker run -it -e HTTP_PORT=8000 \ 
    -v hgw_backend_config.yaml:/etc/hgw_service/hgw_backend_config.yml
    -v mycacert.pem:/cacerts/mycacert.pem \
    -v my_web_server_cert.pem:/container/web_certs/cert.pem \
    -v my_web_server_key.pem:/container/web_certs/key.pem \
    -v kafka_cert_client.pem:/container/client_certs/kafka_cert.pem \
    -v kafka_key_client.pem:/container/client_certs/kafka_key.pem \
    -v kafka_ca_client.pem:/container/client_certs/kafka_ca.pem \
    crs4/hgw_backend
```  
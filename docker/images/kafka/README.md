This image is created starting from blacktop/docker-kafka-alpine:0.11. 

References:
 - Source: https://github.com/blacktop/docker-kafka-alpine
 - Docker: https://hub.docker.com/r/blacktop/kafka/
 
The configuration is the same.

It adds two funcionality:
 
 * It adds the ACL configuration functionality for Health Gateway Project. That means that you can specify
   the producer and consumer that can access to a topic in the KAFKA_CREATE_TOPICS variable
 * It needs the keystore and truststore JKS file with the CA certs to use. The stores can be created
   using the utility in [github](https://github.com/crs4/health-gateway/blob/develop/certs/generate_kafka_server_certificates.sh)
   

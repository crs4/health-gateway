# Enrolling a Source

This page describes how to enroll a new Source.

## Registration in the admin page

Access to the /admin/ page of the backend to create an Authentication object and a Source object.

### Creation of the authentication object

To create an authentication object, which contains the parameters to connect to the
Source. There are two methods supported:

 * Certificates authentication
 * OAuth2 authentications

#### Certificate authentication

This type of authentication needs a pair of client key/certificate that the Source trusts (i.e., the certificate has been
signed by a CA that the Source trusts). The method to obtain these files is out of the scope of the tutorial.

To create the authentication object add one and upload the two files in PEM format. Take a not of the ID of the newly
created object.

#### OAuth2 authentication

TBD

### Creation of the Source object

Now create a Source object. The fields you must insert are:

 * **Source id:** The ID of the Source. Leave the autocreated value and note it. This value has to be given to the Source
   since it is the id of the kafka topic it has to use to send messages
 * **Name:** The name of the source
 * **URL:** The url of the endpoint to create connectors (e.g.: https://sourceendpoint/v1/connectors/)
 * **Auth Type:** Select the auth type among the available. It has to correspond to the correct authentication object
   created before
 * **Content type:** Select the contenttype that corresponds to the authentication object created before
 * **Object id:**  Insert the ID of the object noted before

## Creation of Kafka topic and relative ACL for the destination

In the Kafka server it is necessary adding a new topic for the destination and the relative ACL. The topic has to be
accessed only by the Source endpoint in Write mode and by the HGW Dispatcher in Read mode.
If using docker just set the environment variable KAFKA_CREATE_TOPICS when running the container to the value:

<source_id>:1:1:<publisher>:<consumer>

Alternatively you can execute the command `create_topics.sh` in a running kafka container 

```bash
docker exec -e KAFKA_CREATE_TOPICS=<destination_id>:1:1:<publisher>:<consumer> <kafka_container> /create_topics.sh 
```

The <source_id> is the one configured in the web application. The <publisher> is hgw_dipatcher and the <consumer>
is the service name used in the `generate_kafka_client_certificates.sh`.
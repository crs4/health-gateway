Enrolling a Source
------------------

To enroll a new Source, access to the /admin/ page of the backend to
create an Authentication object and a Source object.

Creation of the Authentication Object
#####################################

An Authentication object contains the parameters to authenticate to the
REST API of the Source Endpoint. The Health Gateway can support two
methods:

 * Certificates
 * OAuth2

The Certificates method needs a pair of client key/certificate
that the Source trusts (i.e., the certificate has been signed by a CA that the
Source trusts).
The method to obtain these files is out of the scope of the tutorial.
To create the object, add one and upload the two files in PEM
format.
Take a note of the ID of the newly created object.

OAuth2 method means that the Source Endpoint uses OAuth2 client_credentials
method to authenticate the clients. This means that the Health Gateway
need a pair of client_id and client_secret assigned by the Source Endpoint
administrators. If the Source Endpoint wants also a Basic auth to get
an authorization token, it is required it to give also the Auth Username
and Auth Password.
After having obtained the parameters, create an OAuth2 Authentication object,
fill the form and save. Take a not the ID of the object in this case as well.

Creation of the Source object
#############################

Now create the Source object. The fields you must insert are:

 * **Source id:** The ID of the Source. Leave the autocreated value and note
    it. This value has to be given to the Source since it is the id of the
    kafka topic it has to use to send messages
 * **Name:** The name of the source
 * **URL:** The url of the endpoint to create connectors (e.g.: https://sourceendpoint/v1/connectors/)
 * **Auth Type:** Select the auth type among the available.
    It has to correspond to the correct authentication object
    created before
 * **Content type:** Select the contenttype that corresponds to the
    authentication object created before
 * **Object id:**  Insert the ID of the object noted before

Creation of Kafka client certificates
########################################

In the case the Source is configured to send the messages using a Kafka
client, it will need a certificate with its associated private key
to access to Kafka. So it is necessary to create them.
To do that use the script `generate_kafka_client_certificates.sh`
in hgw/certs/ directory. The script will generate
PEM files and also the JKS keystore and truststore
in case the Source needs them

In the Kafka server it is necessary the creation of a new topic and its ACL
for the Source Endpoint. The topic has to be
accessed only by the Source Endpoint in Write mode and by the HGW
Dispatcher in read mode.
If using docker just set the environment variable
KAFKA_CREATE_TOPICS when running the container to the value:

`<source_id>:1:1:<publisher>:<consumer>`

Alternatively you can execute the command
`create_topics.sh` in a running kafka container:

```bash
docker exec -e KAFKA_CREATE_TOPICS=<source_id>:1:1:<publisher>:<consumer> <kafka_container> /create_topics.sh 
```

The ``source_id`` is the one configured in the web application.
The ``publisher`` is the name used when generating the Kafka client
certs and the <consumer> is hgw_dispatcher
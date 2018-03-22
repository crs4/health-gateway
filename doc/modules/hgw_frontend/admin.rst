Enrolling a Destination
***********************

This page describes how to enroll a new Destination.

Creation of Private/Public Key Pair
-----------------------------------

First of all you will need to create an RSA Private/Public Key pair that will be used to encrypt messages paylod. The
private key has to be kept secret by the destination while the public has to be registered in the HGW Frontend
application. To generates the key you can use the `create_rsa_key_pair.sh` script in hgw/utils directory.

Registration to Web
-------------------

Now you will need to create a new Destination in the HGW Frontend web page. Access to the /admin/ url of the frontend
and click Destination->Add Destination.

Here you will have to fill the form with the following data:

    * **Destination id**:
        it is the identifier of the destination in the Health Gateway. It is created by Django so just use the value already present-
        This value is also the name of the Kafka topic associated to the destination

    * **Rest or Kafka**: If the Destinatio will consume messages using Kafka or REST

    * **Name**: The name of the Destination

    * **Kafka public key**: The public key created before

After that you will need to create also the REST client corrsponding to the Destination. Go in /admin/ page and
click REST Clients->Add Rest Client.

Here it is necessary to fill the form. The data to be inserted are:

    *
        **Client id**: it is the OAuth2 client id assigned to the destination. It is created by Django so just use the value already present
    *
        **User**: Leave it blank
    *
        **Redirect uris**: Leave blank
    *
        **Client type**: the OAuth2 client type. Must be Confidential
    *
        **Authorization Grant Type**: The OAuth2 authorization grant type. Must be Client credentials
    *
        **Client Secret**:
        it is the OAuth2 client secret of the the destination. It is created by Django so just use the value already present
    *
        **Destination**: Select the Destination created in the step before

    *
        **Scopes**: Leave the default ones

Creation of Kafka client certificates
-------------------------------------

The destination will need a Certificate with its associated Private Key to access to Kafka. So it is necessary to create them.
To do that use the script `generate_kafka_client_certificates.sh` in hgw/certs/ directory. The script will generate
PEM files and also the JKS keystore and truststore in case the Destination needs them

Creation of Kafka topic and relative ACL for the destination
------------------------------------------------------------

In the Kafka server it is necessary adding a new topic for the destination and the relative ACL. The topic has to be
accessed only by the HGW dispatcher in Write mode and by the Destination itself in Read mode.
If using docker just add a record to KAFKA_TOPIC variable in the Kafka service specifying:

<destination_id>:1:1:<publisher>:<consumer>

The <destination_id> is the one configured in the web application. The <publisher> is hgw_dipatcher and the <consumer>
is the service name used in the `generate_kafka_client_certificates.sh`.


Information to give to the Destination
--------------------------------------

The Destination will need the following informations back:

    * OAuth2 Client id and Client secret: necessary to use the HGW Frontend REST API
    * Destination id: This is used as the name of the Kafka topic associated to the Destination, so it is needed to get messages
    * Kafka Client Key/Certificates: The destination needs them to connect to the Kafka Broker



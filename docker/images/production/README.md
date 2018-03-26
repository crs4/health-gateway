# Launching the production environment

The production environment of Health Gateway is composed by the main service and 
does not have any Destination and Source enrolled in the service.

Here we describe the actions to run the environment

## Changes to file host

First of all you need to add entries for the services in your file hosts. The entries are:

127.0.0.1   hgwfrontend
127.0.0.1   hgwbackend
127.0.0.1   consentmanager

## Enrolling a Destination

To enroll a destination you need to open the health gateway frontend admin page from a browser.
Go to `https://hgwfrontend:8000/admin` and add a REST Client and a Destination.
Register the assigned destination id.

## Enrolling a Source

To enroll a source you need to open the health gateway backend admin page from a browser.
Go to `http://hgwbackend:8003/admin` and add a Source entry
Register the assigned destination id.

## Create kafka topics

Now you need to create the topics for the destination and the source in kafka. To do that
launch the following command from the docker-compose directory:

```bash
docker-compose exec kafka -e KAFKA_CREATE_TOPICS=<source_id>:1:1:<source_host_name>:hgwdispatcher,<destination_id>:1:1:hgwdispatcher:<destination_host_name>
```


# Launching the production environment

The production environment of Health Gateway is composed by the main service and 
does not have any Destination and Source enrolled in the service.

Here we describe the actions to run the environment

## Changes to file host

First of all you need to add entries for the services in your file hosts. The entries are:

* 127.0.0.1   hgwfrontend
* 127.0.0.1   hgwbackend
* 127.0.0.1   consentmanager
* 127.0.0.1   spid-testenv-identityserver
* 127.0.0.1   spid-testenv-backoffice

## Enrolling a Destination

Refer to the Health Gateway Frontend documentation

## Enrolling a Source

Refer to the Health Gateway Backend documentation

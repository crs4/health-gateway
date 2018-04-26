# How to run the Docker environment

Health Gateway is composed of different Docker images, one for every service. 
The main images/services are

 * hgw_frontend
 * hgw_backend
 * hgw_dispatcher
 * consent_manager
 * kafka
 
Besides this, there are some mock images for the destinations and sources which are

 * destination_mockup
 * source_endpoint_mockup
 
Finally, there are the two SPID images, which are extensions of AgID images, to use as Identity Providers

## Environments

There are different docker-compose environments that can be run to test the system. These environment are configured
with docker-compose. There are two environment that can be run for development which are :

 * development: these launches the environment for development, with source_endpoint_mockup  and destination_mockup as destination
 * i2b2: these uses source_endpoint_mockup and i2b2_destination as destination
 
There are also two other environments:
 
 * integration: environment to run integration tests
 * dispatcher_performance: environment to test dispatcher performance. It permits to run arbitrary number of sources 
   and destinations
 
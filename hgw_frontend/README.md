# Health Gateway Frontend

This Django project is part of the Health Gateway project. It implements a REST api to access to 
Health Gateway frontend

## Requirements

The Health Gateway Frontend needs some Python packages to run. The requirements are listed in `requirements.txt` file

## Installation

To install the Health Gateway Frontend, firts install the requirements:

```bash
pip install -r requirements.txt
```

Then create the database and load initial data: 

```bash
python manage.py makemigrations hgw_frontend
python manage.py migrate
python manage.py loaddata fixtures/initial_data.json
```

## Run

You will need to run the server using ssl. For development you can use the following commands

```bash
python manage.py runsslserver --certificate certs/cert.pem --key certs/key.pem 0.0.0.0:8000
```

*NOTE: the certs files are for development only*

### Single Sign On
 
The Health Gateway Frontend uses SSO authentication and it acts the role of Service Provider in a SAML
environemnt. For development purpose the IdP is implemented using a Shibboleth installation with docker compose, 
which needs to be installed in the system.
To create and run the docker compose images go in the directory ``docker/spid-mockup`` and run

```bash
docker-compose build 
docker-compose up
```

#### Hosts

To make the development environment works you should set the hosts in your file hosts. In particular you should
add two hosts:

```
hgwfrontend <localhost>
```


## Notebook requirements

The notebook needs some extra packages to run. To install them run

```bash
pip install -r notebooks/requirements.txt
```

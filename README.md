# Netsoc Admin

## Purpose

This is intended to be a one-stop shop for users of UCC Netsoc's servers.

## Features

### We have

* Automated user account creation
* MySQL database managment
* Backup managment
* Facility to contact a sysadmin
* WordPress installer
* Tutorials

### We will have

* Server password reset functionality
* Own domain name linking to WordPress installation

## Installation

**NOTE** if this is for production, use Portainer. It provides a `Recreate` button that can automatically pull the latest image and make a new container with the same settings

To build the docker image:

1. Create a `netsocadmin/config.py` following the same format as of that in `netsocadmin/config.py`. This file configures the netsoc admin server itself.
2. In this directory, run:

```bash
docker build -t netsocadmin .
```

To run the docker image:

```bash
docker run \
    -d -p 5050:5050 \
    --name netsocadmin \
    -v /path/to/backups:/backups \
    -v /path/to/home/dirs:/home/users \
    -v /path/to/admin_passwords.py:/netsocadmin/config.py \
    docker.netsoc.co/netsocadmin:latest
```

## Dev Environment

### To Run

To bring up the external services needed for NetsocAdmin to run (LDAP and MySQL), run `docker-compose -f docker-compose-dev.yml up -d`.

Then you can run `cd netsocadmin` followed by `python3 netsoc_admin.py` to run the actual netsoc admin.
Please ensure you have Python3.6+ for this.
Also note that you must run the script from inside the `netsocadmin` directory or else flask won't be able to find the templates!

Go to `http://localhost:5050` and away you go!

To shut down the services afterwards, run `docker-compose -f docker-compose-dev.yml down`.

### Dev Env User Details
Admin User details:

* username: `john`
* password: `johns-password`

Normal User details:

* username: `sofia`
* password: `sofias-password`

### Note
Just to be aware that testing on MacOS might require you to build the netsocadmin docker image locally to test it, due to some issues with crypt functions on MacOS.
I don't know why it's a thing, but it is :(

1. `docker build -t netsocadmin .`
2. `docker run -d -p 5050:5050 --name netsocadmin netsocadmin`
3. Connect to `localhost:5050` and continue as normal

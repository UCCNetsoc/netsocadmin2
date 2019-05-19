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
* Change your login shell

### We will have

* Server password reset functionality
* Own domain name linking to WordPress installation
* Slide upload page
* And more

## Installation

### For developing locally, please look further below

To build the docker image:

1. Create a `netsocadmin/config.py` following the same format as of that in `netsocadmin/config.py`. This file configures the netsoc admin server itself.
2. In this directory, run the following for a non development image:

```bash
docker build -t docker.netsoc.co/netsoc/netsocadmin .
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

## Developer Environment

Please checkout our [Netsoc Developer Environment](https://github.com/UCCNetworkingSociety/dev-env)

### Note

Just to be aware that testing on MacOS might require you to build the netsocadmin docker image locally to test it, due to some issues with crypt functions on MacOS.
I don't know why it's a thing, but it is :(

1. `docker build -t netsocadmin .`
2. `docker run -d -p 5050:5050 --name netsocadmin --net host netsocadmin`
3. Connect to `localhost:5050` and continue as normal

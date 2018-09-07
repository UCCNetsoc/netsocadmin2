# Netsoc Admin

## Purpose

This is intended to be a one-stop shop for users of UCC Netsoc's servers.

## Features

### We have:
* Automated user account creation
* MySQL database managment
* Backup managment
* Facility to contact a sysadmin
* WordPress installer
* Tutorials

### We will have:
* Server password reset functionality
* Own domain name linking to WordPress installation

## Installation

**NOTE** if this is for production, use Portainer. It provides a `Recreate` button that can automatically pull the latest image and make a new container with the same settings

To build the docker image:

1. Create a file called `wordpress_installer_config.py` following the same format as of that in `sample_wordpress_installer_config.py`. This file configures the wordpress_installer package. 
2. Create a `admin_passwords.py` following the same format as of that in `sample_admin_passwords.py`. This file configures the netsoc admin server itself.
3. In this directory, run:

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
    -v /path/to/admin_passwords.py:/netsocadmin/webapp/passwords.py \
    -v /path/to/wordpress_installer_config.py:/netsocadmin/wordpress_installer/wordpress_installer/config.py \
    docker.netsoc.co/netsocadmin:latest


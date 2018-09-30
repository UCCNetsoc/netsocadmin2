FROM python:alpine3.7
LABEL maintainer="netsoc@netsoc.co"

COPY . /netsocadmin

RUN apk update && apk upgrade

RUN apk add --no-cache curl pkgconfig python3-dev openssl-dev libffi-dev musl-dev make gcc openssh

# install all python requirements
RUN pip3 install -r /netsocadmin/webapp/requirements.txt

# move the configuration files to their relevant directories
RUN mv /netsocadmin/sample_wordpress_installer_config.py /netsocadmin/wordpress_installer/wordpress_installer/config.py
RUN mv /netsocadmin/sample_admin_passwords.py /netsocadmin/webapp/passwords.py

# install the wordpress installer package
RUN pip3 install -e /netsocadmin/wordpress_installer
RUN python3 -m wordpress_installer.calibrate

# this will be the mount point for the user home directories
RUN mkdir /home/users

# the server SSH's to leela in order to initialise user home directories
RUN mkdir ~/.ssh
RUN ssh-keyscan -t ecdsa leela.netsoc.co >> ~/.ssh/known_hosts

WORKDIR /netsocadmin/webapp

VOLUME ["/backups", "/home/users", "/netsocadmin/config.py"]

# # not actually used, just for documentaion
EXPOSE 5050
ENTRYPOINT ["python3", "/netsocadmin/netsoc_admin.py"]

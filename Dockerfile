FROM python:latest
MAINTAINER "broderickciaran@gmail.com"

ARG mode="notdebug"


COPY . /netsocadmin

# install all python requirements
RUN pip3 install -r /netsocadmin/webapp/requirements.txt

# move the configuration files to their relevant directories
RUN mv /netsocadmin/wordpress_installer_config.py /netsocadmin/wordpress_installer/wordpress_installer/config.py
RUN mv /netsocadmin/admin_passwords.py /netsocadmin/webapp/passwords.py

# install the wordpress installer package
RUN pip3 install -e /netsocadmin/wordpress_installer
RUN python3 -m wordpress_installer.calibrate

# this will be the mount point for the user home directories
RUN mkdir /home/users

# the server SSH's to leela in order to initialise user home directories
RUN mkdir ~/.ssh
RUN ssh-keyscan -t ecdsa leela.netsoc.co >> ~/.ssh/known_hosts

WORKDIR /netsocadmin/webapp

# not actually used, just for documentaion
EXPOSE 5050

ENV runtimemode $mode
ENTRYPOINT python3 /netsocadmin/webapp/netsoc_admin.py $runtimemode

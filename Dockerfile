FROM python:latest
COPY . /netsocadmin
RUN "pip3 install -r /netsocadmin/webapp/requirements.txt"
RUN cd /netsocadmin/wordpress_installer; pip3 install -e .; python3 -m wordpress_installer.configure
ENTRYPOINT "cd /netsocadmin/webapp/; python3 netsocadmin.py debug"

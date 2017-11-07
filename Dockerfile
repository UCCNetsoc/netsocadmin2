FROM python:latest
MAINTAINER "broderickciaran@gmail.com"
COPY . /netsocadmin
RUN pip3 install -r /netsocadmin/webapp/requirements.txt
RUN cd /netsocadmin/wordpress_installer; pip3 install -e .; python3 -m wordpress_installer.calibrate
EXPOSE 5050
ENTRYPOINT ["python3", "/netsocadmin/webapp/netsoc_admin.py", "debug"]

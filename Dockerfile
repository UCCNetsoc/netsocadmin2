FROM python:3.7-slim as dev
LABEL maintainer="netsoc@uccsocieties.co"

VOLUME [ "/backups", "/home/users" ]

WORKDIR /netsocadmin/netsocadmin

ENV PYTHONPATH=/netsocadmin

EXPOSE 5050

RUN apt update && \
    apt install -y libssl-dev openssh-client

RUN pip3 install gunicorn==19.10.0

COPY requirements.txt /netsocadmin/requirements.txt

RUN pip3 install -r /netsocadmin/requirements.txt

COPY . /netsocadmin

CMD [ "gunicorn", \
    "--reload", \
    "-b", "0.0.0.0:5050", \
    "--log-config", "/netsocadmin/logging.conf", \
    "-c", "/netsocadmin/gunicorn.conf", \
    "netsoc_admin:app" ]

FROM python:3.7-slim
LABEL maintainer="netsoc@uccsocieties.co"

VOLUME [ "/backups", "/home/users" ]

WORKDIR /netsocadmin/netsocadmin

ENV PYTHONPATH=/netsocadmin

EXPOSE 5050

RUN apt update && \
    apt install -y libssl-dev openssh-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* 

# the server SSH's to leela in order to initialise user home directories
RUN mkdir ~/.ssh && \
    ssh-keyscan -t ecdsa leela.netsoc.co >> ~/.ssh/known_hosts

RUN pip3 install gunicorn==19.10.0 && \
    pip3 install gunicorn[gevent]

COPY --from=dev /netsocadmin /netsocadmin

RUN pip3 install -r /netsocadmin/requirements.txt

CMD [ "gunicorn", \
    "-b", "0.0.0.0:5050", \
    "--log-config", "/netsocadmin/logging.conf", \
    "-k", "gevent", \
    "-c", "/netsocadmin/gunicorn.conf", \
    "netsoc_admin:app" ]
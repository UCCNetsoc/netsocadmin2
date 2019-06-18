FROM python:alpine3.7 as dev
LABEL maintainer="netsoc@netsoc.co"

VOLUME [ "/backups", "/home/users" ]

# not actually used, just for documentaion
EXPOSE 5050

RUN apk update

RUN apk add --no-cache pkgconfig python3-dev openssl-dev libffi-dev gcc musl-dev make

COPY requirements.txt /netsocadmin/requirements.txt
# install all python requirements
RUN pip3 install -r /netsocadmin/requirements.txt && \
    pip3 install gunicorn

COPY . /netsocadmin

WORKDIR /netsocadmin/netsocadmin

CMD [ "gunicorn", \
    "--reload", \
    "-b", "0.0.0.0:5050", \
    "--log-config", "/netsocadmin/logging.conf", \
    "-c", "/netsocadmin/gunicorn.conf", \
    "netsoc_admin:app" ]

FROM python:alpine3.7

RUN apk update && \
    apk add --no-cache python3 openssl-dev openssh pkgconfig python3-dev openssl-dev libffi-dev gcc musl-dev make

# the server SSH's to leela in order to initialise user home directories
RUN mkdir ~/.ssh && \
    ssh-keyscan -t ecdsa leela.netsoc.co >> ~/.ssh/known_hosts

COPY --from=dev /netsocadmin /netsocadmin

RUN pip3 install -r /netsocadmin/requirements.txt && \
    pip3 install gunicorn

WORKDIR /netsocadmin/netsocadmin

CMD [ "gunicorn", "-b", "0.0.0.0:5050", "--log-config", "/netsocadmin/gunicorn.conf", "-c", "/netsocadmin/gunicorn.conf", "netsoc_admin:app" ]

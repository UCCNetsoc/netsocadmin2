FROM python:alpine3.7 as dev
LABEL maintainer="netsoc@netsoc.co"

VOLUME [ "/backups", "/home/users" ]

# not actually used, just for documentaion
EXPOSE 5050

COPY requirements.txt /netsocadmin/requirements.txt

RUN apk update

RUN apk add --no-cache pkgconfig python3-dev openssl-dev libffi-dev gcc musl-dev make

# install all python requirements
RUN pip3 install -r /netsocadmin/requirements.txt

COPY . /netsocadmin

WORKDIR /netsocadmin/netsocadmin

CMD [ "python3", "netsoc_admin.py" ]

FROM python:alpine3.7

RUN apk update && \
    apk add --no-cache python3 openssl-dev openssh pkgconfig python3-dev openssl-dev libffi-dev gcc musl-dev make

# the server SSH's to leela in order to initialise user home directories
RUN mkdir ~/.ssh && \
    ssh-keyscan -t ecdsa leela.netsoc.co >> ~/.ssh/known_hosts

COPY --from=dev /netsocadmin /netsocadmin

RUN pip3 install -r /netsocadmin/requirements.txt && \
    pip3 install gunicorn

<<<<<<< HEAD
# not actually used, just for documentaion
EXPOSE 5050
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
=======
WORKDIR /netsocadmin/netsocadmin

CMD [ "gunicorn", "-b", "0.0.0.0:5050", "netsoc_admin:app" ]
>>>>>>> Made gud dockerfile with gunicorn for prod

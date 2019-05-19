import os

# flask app secret key
SECRET_KEY = os.urandom(64)

# Config for flask
FLASK_CONFIG = {
    "host": "0.0.0.0",
    "port": "5050",
    "debug": True,
}

SHELL_PATHS = {
    "bash": "/bin/bash",
    "csh": "/bin/csh",
    "fish": "/usr/bin/fish",
    "ksh": "/usr/bin/ksh",
    "zsh": "/usr/bin/zsh"
}

# key of the cookie given to maintain sessions
# corresponding value should be true or false
LOGGED_IN_KEY = str(os.urandom(32))

# ldap shit
LDAP_AUTH = {
    "password": "netsoc",
    "user": "cn=admin,dc=netsoc,dc=co"
}

LDAP_HOST = "auth:389"
LDAP_USER_GROUP_ID = 422

# location of the markdown tutorials
TUTORIAL_FOLDER = "./tutorials"

# the root directory with all of the backups in it
BACKUPS_DIR = "/backups"

# local uri db name
TOKEN_DB_NAME = ".uri.db"  # should end with .db for .gitignore

# mysql db details
MYSQL_DETAILS = {
    "host": "db",
    "user": "root",
    "password": "netsoc",
    "db": "netsoc_admin",
}

# sendgrid api key
SENDGRID_KEY = "sample_text"
NETSOC_EMAIL_ADDRESS = "netsoc@uccsocieties.com"
NETSOC_ADMIN_EMAIL_ADDRESS = "netsocadmin@netsoc.co"

# blacklisted usernames
USERNAME_BLACKLIST = [
    "test"
]

# the URL which the netsoc discord bot can be reached at
DISCORD_WEBHOOK_ADDRESS = "https://apitester.com"

SYSADMIN_EMAILS = [
    "john@netsoc.co"
]

# sysadmin email blacklist for testing.
EMAIL_WHITELIST = [
    "john@netsoc.co"
]

# used for making the ssh connection to the server
SERVER_HOSTNAME = "localhost"

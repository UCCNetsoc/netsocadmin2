import os

# flask app secret key 
SECRET_KEY = 1234

# key of the cookie given to maintain sessions
# corresponding value should be true or false
LOGGED_IN_KEY = "1234"

# sendgrid api key
SENDGRID_KEY = ""
SENDGRID_USERNAME = "myusername"
SENDGRID_PASSWORD = "password123"
NETSOC_EMAIL_ADDRESS = "orgaddress@mydomain.com"
NETSOC_ADMIN_EMAIL_ADDRESS = "netsocadminname@mydomain.com"


# ldap shit
LDAP_KEY = ""
LDAP_HOST = "ldap.mydomain.com:390"
LDAP_USER = "cn=admin,dc=mydomain,dc=com"

# local uri db name
DBNAME = ".uri.db" # should end with .db for .gitignore

# mysql db details
SQL_HOST = "mysql.mydomain.com"
SQL_USER = "admin"
SQL_PASS = "password123"
SQL_DB = "netsoc_admin_db"

# email blacklist for testing.
EMAIL_WHITELIST = [
    "123456789@umail.ucc.ie", # developer's student email
]

# blacklisted usernames
BLACKLIST = [
    "root",
    "apache2",
    "httpd",
    "www-data",
]

# the root directory with all of the backups in it
BACKUPS_DIR = "/netsocadmin/backups"

# the URL which the netsoc discord bot can be reached at 
DISCORD_BOT_HELP_ADDRESS = "http://discordbot.mydomain.com:4201/help"

SYSADMIN_EMAILS = [
    "me@gmail.com", # email address will be notified with help-requests
]

# used for making the ssh connection to the server
SERVER_HOSTNAME = "leela.netsoc.co"

# location of the markdown tutorials
TUTORIAL_FOLDER = "/netsocadmin/webapp/tutorials"


wordpress_config = {
    "db": {
        "user": "me",
        "password": "password123",
        "host": "mysql.mydomain.com",
    },


    # (Make this an absolute path)
    "package": {
        "logging_config":
            "<location-of-netsocadmin>/netsocadmin/logging_config.ini"
    }

}

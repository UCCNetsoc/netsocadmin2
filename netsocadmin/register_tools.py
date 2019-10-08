"""
This file contains functions which are used during
registration by the main netsoc admin file.
"""
# stdlib
import crypt
import hashlib
import random
import sqlite3
import string
import typing

# lib
import ldap3
import paramiko
import pymysql

# local
import config
import db
import mail_helper

ldap_server = ldap3.Server(config.LDAP_HOST, get_info=ldap3.ALL)


def send_confirmation_email(email: str, server_url: str) -> bool:
    """
    Sends email containing the link which users use to set up their accounts.

    :param email the email address which the user registered with
    :param server_url the address of the flask application
    :returns boolean true if the email was sent succesfully, false otherwise.
    """
    uri = generate_uri(email)
    message_body = f"""
Hello,

Please confirm your account by going to:

http://{server_url}/signup?t={uri}&e={email}

Yours,

The UCC Netsoc SysAdmin Team
"""
    if not config.FLASK_CONFIG['debug']:
        response = mail_helper.send_mail(
            "server.registration@netsoc.co",
            email,
            "Account Registration",
            message_body,
        )
    else:
        response = type("Response", (object,), {"status_code": 200, "token": uri})
    return response


def send_details_email(email: str, user: str, password: str, mysql_pass: str) -> bool:
    """
    Sends an email once a user has registered succesfully confirming
    the details they have signed up with.

    :param email the email address which this email is being sent
    :param user the username which you log into the servers with
    :param password the password which you log into the servers with
    :returns True if the email has been sent succesfully, False otherwise
    """

    message_body = f"""
Hello,

Thank you for registering with UCC Netsoc! Your server log-in details are as follows:

username: {user}
password: {password}

We also provide MySQL free of charge.
You can access it with any MySQL client at mysql.netsoc.co with the following details:

username: {user}
password: {mysql_pass}

You can change your MySQL password at https://admin.netsoc.co/tools/mysql.

If you need any help, please contact netsoc@uccsocieties.ie, or via the help section on https://admin.netsoc.co/help.

To log in, run:
    ssh {user}@leela.netsoc.co
and enter your password when prompted.
If you are using Windows, go to http://www.putty.org/ and download the SSH client.

Please change your password when you first log-in to something you'll remember!

Yours,

The UCC Netsoc SysAdmin Team

P.S. We are always changing and improving our services, with new features and services being added all the time.
Follow us on social media or join our discord at https://discord.gg/qPUmuYw to keep up to date with our latest updates!
    """
    if not config.FLASK_CONFIG['debug']:
        response = mail_helper.send_mail(
            "server.registration@netsoc.co",
            email,
            "Account Registration",
            message_body,
        )
    else:
        response = type("Response", (object,), {"status_code": 200})
    return str(response.status_code).startswith("20")


def generate_uri(email: str) -> str:
    """
    Generates a uri token which will identify this user's email address.
    This should be checked when the user signs up to make sure it was the
    token they sent.

    :param email the email used to sign up with
    :returns the generated uri string or None of there was a failure
    """
    try:
        chars = string.ascii_uppercase + string.digits
        size = 10
        id_ = "".join(random.choice(chars) for _ in range(size))
        uri = hashlib.sha256(id_.encode()).hexdigest()

        conn = sqlite3.connect(config.TOKEN_DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO uris VALUES (?, ?)", (email, uri))
        conn.commit()
    except sqlite3.OperationalError:
        c.execute(db.RESET)
        c.execute(db.CREATE)
        c.execute("INSERT INTO uris VALUES (?, ?)", (email, uri))
        conn.commit()
    finally:
        if conn:
            conn.close()
    return uri


def good_token(email: str, uri: str) -> bool:
    """
    Confirms whether an email and uri pair are valid.

    :param email the email which we are testing the uri for
    :param uri the identifier token which we geerated and sent
    :returns True if the token is valid (i.e. sent by us to this email),
        False otherwise (including if a DB error occured)
    """
    with sqlite3.connect(config.TOKEN_DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM uris WHERE uri=?", (uri,))
        row = c.fetchone()
        if not row or row[0] != email:
            return False
    return True


def remove_token(email: str):
    """
    Removes a token from the database for a given email address.

    :param email the email address corresponding to the token being removed
    """
    with sqlite3.connect(config.TOKEN_DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM uris WHERE email=?", (email,))
        conn.commit()


class LDAPException(Exception):
    pass


class UserExistsInLDAPException(Exception):
    pass


def add_ldap_user(user: str) -> typing.Dict[str, object]:
    """
    Adds the user to the Netsoc LDAP DB.

    :param user the username which has been requested
    :returns (success, info) tuple
        sucess is True if detals were succesfully added and False otherwise.
        info is a dictionary of information values for the mysql db. This will
            have to be added to when the user completes the form.
    """
    info = {
        "uid": user,
        "gid": config.LDAP_USER_GROUP_ID,
        "home_dir": f"/home/users/{user}",
    }
    with ldap3.Connection(ldap_server, auto_bind=True, receive_timeout=5, **config.LDAP_AUTH) as conn:
        success = conn.search(
            search_base="cn=member,dc=netsoc,dc=co",
            search_filter="(objectClass=account)",
            attributes=["uidNumber", "uid"],
        )
        if not success and conn.last_error is not None:
            raise LDAPException(f"error adding ldap user: {conn.last_error}")

        last = None
        for account in conn.entries:
            if account["uid"] == user:
                raise UserExistsInLDAPException(f"{user} exists in LDAP")
            last = account["uidNumber"]
        next_uid = int(str(last)) + 1
        info["uid_num"] = next_uid

        # creates initial password for user. They will be asked to change
        # this when they first log in.
        password = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
        # pylint: disable=E1101
        crypt_password = "{crypt}" + crypt.crypt(password,  crypt.mksalt(crypt.METHOD_SHA512))
        info["password"] = password
        info["crypt_password"] = crypt_password

        # add information to Netsoc LDAP DB
        object_class = [
            "account",
            "top",
            "posixAccount",
            "mailAccount",
        ]

        attributes = {
            "cn":            user,
            "gidNumber":     config.LDAP_USER_GROUP_ID,
            "homeDirectory": info["home_dir"],
            "mail":          f"{user}@netsoc.co",
            "uid":           user,
            "uidNumber":     next_uid,
            "loginShell":    "/bin/bash",
            "userPassword":  crypt_password,
        }

        success = conn.add(
            f"cn={user},cn=member,dc=netsoc,dc=co",
            object_class,
            attributes,
        )
        if not success:
            raise LDAPException(f"error adding ldap user: {conn.last_error}")
    return info


def remove_ldap_user(user: str) -> bool:
    """
    Removes a user from LDAP

    :param user the username
    :returns True if successful
    """
    with ldap3.Connection(ldap_server, auto_bind=True, receive_timeout=5, **config.LDAP_AUTH) as conn:
        return conn.delete(f"cn={user},cn=member,dc=netsoc,dc=co")


class MySQLException(Exception):
    pass


def add_netsoc_database(info: typing.Dict[str, str]) -> pymysql.Connection:
    """
    Adds a user's details to the Netsoc MySQL database.

    :param info a dictionary containing all the information
        collected during signup to go in the database.
    :returns Connection object to rollback the transaction if needed
    """
    try:
        conn = pymysql.connect(**config.MYSQL_DETAILS)
        conn.begin()
        with conn.cursor() as c:
            sql = \
                """
                INSERT INTO users
                    (uid, name, email)
                VALUES (%s, %s, %s);
                """
            row = (
                info["uid"],
                info["name"],
                info["email"],
            )
            c.execute(sql, row)
        return conn
    except Exception as e:
        raise MySQLException(e)


def has_account(email: str) -> bool:
    """
    Sees if their is already an account on record with this email address.

    :param email the in-question email address being used to sign up
    :returns True if their already as an account with that email,
        False otherwise.
    """
    conn = pymysql.connect(**config.MYSQL_DETAILS)
    with conn.cursor() as c:
        sql = "SELECT * FROM users WHERE email=%s;"
        c.execute(sql, (email,))
        if c.fetchone():
            return True
    return False


def is_in_ldap(username: str) -> bool:
    """
    Tells us whether or not a username is already used on the server.

    :param username the username being queried about
    :returns True if the username exists, False otherwise
    """
    if username in config.USERNAME_BLACKLIST:
        return True
    with ldap3.Connection(ldap_server, auto_bind=True, receive_timeout=5, **config.LDAP_AUTH) as conn:
        username = ldap3.utils.conv.escape_filter_chars(username)
        return conn.search(
            search_base="dc=netsoc,dc=co",
            search_filter=f"(&(objectClass=account)(uid={username}))",
            attributes=["uid"],
        )
    return True


def initialise_directories(username: str, password: str):
    """
    Makes an ssh connection to the server which will initialise a
    user's home directory. This allows them to not have to ever connect
    to the server directly and still use netsoc admin.

    :param username the user's UID
    :param password the user's account password
    """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(
        hostname=config.SERVER_HOSTNAME,
        username=username,
        password=password,
    )

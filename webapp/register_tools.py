"""
This file contains functions which are used during
registration by the main netsoc admin file.
"""
import crypt
import db
import hashlib
import ldap3
import passwords as p
import pymysql
import random
from sendgrid import Email, sendgrid
from sendgrid.helpers.mail import Content, Mail
import sqlite3
import string
import typing

def send_confirmation_email(email:str, server_url:str) -> bool:
    """
    Sends email containing the link which users use to set up their accounts.

    :param email the email address which the user registered with
    :param server_url the address of the flask application
    :returns boolean true if the email was sent succesfully, false otherwise.
    """
    uri = generate_uri(email)
    message_body = \
    """
Hello,

Please confirm your account by going to:

http://%s/signup?t=%s&e=%s 

Yours,

The UCC Netsoc SysAdmin Team
    """%(server_url, uri, email)
    sg = sendgrid.SendGridAPIClient(apikey=p.SENDGRID_KEY)
    from_email = Email("lowdown@netsoc.co")
    subject = "Account Registration"
    to_email = Email(email)
    content = Content("text/plain", message_body)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return str(response.status_code).startswith("20")


def send_details_email(email:str, user:str, password:str) -> bool:
    """
    Sends an email once a user has registered succesfully confirming
    the details they have signed up with.

    :param email the email address which this email is being sent
    :param user the username which you log into the servers with
    :param password the password which you log into the servers with
    :returns True if the email has been sent succesfully, False otherwise
    """
    message_body = \
    """
Hello,

Thank you for registering with UCC Netsoc! Your server log-in details are as follows:

username: %s
password: %s

To log in, run:
    ssh %s@leela.netsoc.co
and enter your password when prompted. If you are using windows, go to http://www.putty.org/ and download the SSH client.

Please change your password when you first log-in to something you'll remember!

Yours,

The UCC Netsoc SysAdmin Team
    """%(user, password, user)
    sg = sendgrid.SendGridAPIClient(apikey=p.SENDGRID_KEY)
    from_email = Email("lowdown@netsoc.co")
    subject = "Account Registration"
    to_email = Email(email)
    content = Content("text/plain", message_body)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return str(response.status_code).startswith("20")

def generate_uri(email:str) -> str:
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

        conn = sqlite3.connect(p.DBNAME)
        c = conn.cursor()
        c.execute("INSERT INTO uris VALUES (?, ?)", (email, uri))
        conn.commit()

    except sqlite3.OperationalError:
        c.execute(db.RESET)
        c.execute(db.CREATE)
        c.execute("INSERT INTO uris VALUES (?, ?)", (email, uri))
        conn.commit()

    finally:
        if conn: conn.close()

    return uri


def good_token(email:str, uri:str) -> bool:
    """
    Confirms whether an email and uri pair are valid.

    :param email the email which we are testing the uri for
    :param uri the identifier token which we geerated and sent
    :returns True if the token is valid (i.e. sent by us to this email),
        False otherwise (including if a DB error occured)
    """
    with sqlite3.connect(p.DBNAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM uris WHERE uri=?", (uri,))
        row = c.fetchone()
        if not row or row[0] != email:
            return False
    return True


def remove_token(email:str):
    """
    Removes a token from the database for a given email address.

    :param email the email address corresponding to the token being removed
    """
    with sqlite3.connect(p.DBNAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM uris WHERE email=?", (email,))
        conn.commit()


def add_ldap_user(user:str) -> typing.Tuple[bool, typing.Dict[str, object]]:
    """
    Adds the user to the Netsoc LDAP DB.

    :param user the username which has been requested
    :returns (success, info) tuple
        sucess is True if detals were succesfully added and False otherwise.
        info is a dictionary of information values for the mysql db. This will
            have to be added to when the user completes the form.
    """
    ldap_server = ldap3.Server(p.LDAP_HOST, get_info=ldap3.ALL)
    info = {
        "uid": user,
        "gid": 422,
        "home_dir": "/home/users/%s"%(user),
    }
    with ldap3.Connection(
                        ldap_server,
                        user=p.LDAP_USER,
                        password=p.LDAP_KEY,
                        auto_bind=True) as conn:
        
        # checks if username exists and also gets next uid number
        success = conn.search(
                    search_base="cn=member,dc=netsoc,dc=co",
                    search_filter="(objectClass=account)",
                    attributes=["uidNumber", "uid"],)
        if not success:
            return False, conn.last_error
        last = None
        for account in conn.entries:
            if account["uid"] == user:
                return False, conn.last_error
            last = account["uidNumber"]
        next_uid = int(str(last)) + 1
        info["uid_num"] = next_uid

        # creates initial password for user. They will be asked to change
        # this when they first log in.
        password = "".join(random.choice(
            string.ascii_letters + string.digits) for _ in range(12))
        crypt_password = "{crypt}" + \
                crypt.crypt(password,  crypt.mksalt(crypt.METHOD_SHA512))
        info["password"] = password
        info["crypt_password"] = crypt_password

        # add information to Netsoc LDAP DB
        object_class = [
            "account",
            "top",
            "posixAccount",
            "mailAccount"
        ]
        attributes = {
            "cn" : user ,
            "gidNumber": 422,
            "homeDirectory": info["home_dir"],
            "mail": "%s@netsoc.co"%(user),
            "uid" : user,
            "uidNumber": next_uid, 
            "loginShell": "/bin/bash",
            "userPassword": crypt_password,
        }
        success = conn.add(
            "cn=%s,cn=member,dc=netsoc,dc=co"%(user), 
            object_class, 
            attributes)
        if not success:
            return False, conn.last_error
    return True, info

def add_netsoc_database(info:typing.Dict[str, str]) -> bool:
    """
    Adds a user's details to the Netsoc MySQL database.

    :param info a dictionary containing all the information
        collected during signup to go in the database.
    :returns Boolean True if the data was succesfully added
    """
    conn = pymysql.connect(
            host=p.SQL_HOST,
            user=p.SQL_USER,
            password=p.SQL_PASS,
            db=p.SQL_DB,)
    with conn.cursor() as c:
        sql = \
            """
            INSERT INTO users 
                (uid, name, password, gid, home_directory, uid_number, 
                student_id, course, graduation_year, email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
        row = (
            info["uid"],
            info["name"],
            info["crypt_password"],
            info["gid"],
            info["home_dir"],
            info["uid_num"],
            info["student_id"],
            info["course"],
            info["grad_year"],
            info["email"],
        )
        c.execute(sql, row)
    conn.commit()
    return True

def has_account(email:str) -> bool:
    """
    Sees if their is already an account on record with this email address.

    :param email the in-question email address being used to sign up
    :returns True if their already as an account with that email, 
        False otherwise.
    """
    conn = pymysql.connect(
        host=p.SQL_HOST,
        user=p.SQL_USER,
        password=p.SQL_PASS,
        db=p.SQL_DB,)
    with conn.cursor() as c:
        sql = "SELECT * FROM users WHERE email=%s;"
        c.execute(sql, (email,))
        if c.fetchone():
            return True
    return False

def has_username(uid:str) -> bool:
    """
    Tells whether or not a uid is already used on the server.

    :param uid the uid being queried about
    :returns True if the uid exists, False otherwise
    """
    if uid in p.BLACKLIST:
        return True
    ldap_server = ldap3.Server(p.LDAP_HOST, get_info=ldap3.ALL)
    with ldap3.Connection(
                        ldap_server,
                        user=p.LDAP_USER,
                        password=p.LDAP_KEY,
                        auto_bind=True) as conn:
    
        return conn.search(
                    search_base="dc=netsoc,dc=co",
                    search_filter="(&(objectClass=account)(uid=%s))"%(
                            ldap3.utils.conv.escape_filter_chars(uid)),
                    attributes=["uid"],)
    return True

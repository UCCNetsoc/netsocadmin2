import random
import string
import hashlib
import passwords as p

import smtplib
import sqlite3
from sendgrid import Email, sendgrid
from sendgrid.helpers.mail import Content, Mail

def send_confirmation_email(email:string, server_url:string):
    """
    Sends email containing the link which users use to set up their accounts.

    :param email the email address which the user registered with
    :param server_url the address of the flask application
    :returns boolean true if the email was sent succesfully, false otherwise.
    """
    uri = generate_uri(email)
    message_body = "Hello,\n\nPlease confirm your account by going to:\n\nhttp://%s/signup?t=%s&e=%s \n\nYours,\nThe UCC Netsoc Sys Admin Team"%(
        server_url, uri, email)
    """ Uncomment when send grid works again
    sg = sendgrid.SendGridAPIClient(apikey=p.SENDGRID_KEY)
    from_email = Email("lowdown@netsoc.co")
    subject = "Account Registration"
    to_email = Email(email)
    content = Content("text/plain", message_body)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return str(response.status_code).startswith("20")
    """
    to = email
    from_ = "adamgillessen@gmail.com"
    subject = "server signup test"
    email = "\From: %s\nTo: %s\nSubject: %s\n\n\n%s" % (from_, to, subject, message_body)
    with smtplib.SMTP("smtp.gmail.com:587") as smtp:
        smtp.starttls()
        smtp.ehlo()
        smtp.login(from_, p.EMAIL_PASSWORD)
        smtp.sendmail(from_, to, email)
    return True

def generate_uri(email:string):
    """
    Generates a uri token which will identify this user's email address.
    This should be checked when the user signs up to make sure it was the
    token they sent.
    
    :param email the email used to sign up with
    :returns the generated uri string or None of there was a failure
    """
    conn, c, uri = None, None, None
    try:
        chars = string.ascii_uppercase + string.digits
        size = 10
        id_ = "".join(random.choice(chars) for _ in range(size))
        uri = hashlib.sha256(id_.encode()).hexdigest()
        conn = sqlite3.connect(p.DBNAME)
        c = conn.cursor()
        c.execute("INSERT INTO uris VALUES (?, ?)", (email, uri))
        conn.commit()
    finally:
        if c:
            c.close()
        if conn:
            conn.close()
    return uri

def good_token(email:string, uri:string):
    """
    Confirms whether an email and uri pair are valid.

    :param email the email which we are testing the uri for
    :param uri the identifier token which we geerated and sent
    :returns True if the token is valid (i.e. sent by us to this email),
        False otherwise (including if a DB error occured)
    """
    conn, c = None, None
    try:
        conn = sqlite3.connect(p.DBNAME)
        c = conn.cursor()
        c.execute("SELECT * FROM uris WHERE uri=?", (uri,))
        row = c.fetchone()
        if not row or row[0] != email:
            return False
        # uncomment when not debuging c.execute("DELETE FROM uris WHERE uri=?", (uri,))
        conn.commit()
    finally:
        if c:
            c.close()
        if conn:
            conn.close()
    return True

def get_next_user_id_number():
    """
    Returns the next available user_id_number and increments the value for next use.
    """
    next_uid_num = None
    with open("next_user_id_number", "r+") as f:
        next_uid_num = int(f.read().strip())
        f.seek(0)
        f.write(str(next_uid_num + 1))
    return next_uid_num
'''
This file takes care of sending off the data from the help section to multiple areas
currently Discord and email of SysAdmins and the main Netsoc email
'''
import json
import smtplib
from email.message import EmailMessage

import requests

from netsocadmin import config

DISCORD_BOT_HELP_ADDRESS = config.DISCORD_BOT_HELP_ADDRESS


def send_help_email(username: str, user_email: str, subject: str, message: str) -> bool:
    """
    Sends an email to the netsoc email address containing the help data,
    CC'ing all the SysAdmins and the user requesting help.
    This enables us to reply to the email directly instead of copypasting the
    from address and disconnecting history.

    :param username the user requesting help
    :param user_email the user's email address
    :param subject the subject of the user's help requests
    :param message the user's actual message
    """
    message_body = f"""
From: {username}\n
Email: {user_email}

{message}

PS: Please "Reply All" to the emails so that you get a quicker response."""

    msg = EmailMessage()
    msg.set_content(message_body)
    msg["From"] = config.NETSOC_ADMIN_EMAIL_ADDRESS
    msg["To"] = config.NETSOC_EMAIL_ADDRESS
    msg["Subject"] = "[Netsoc Help] " + subject
    msg["Cc"] = tuple(config.SYSADMIN_EMAILS + [user_email])
    try:
        with smtplib.SMTP("smtp.sendgrid.net", 587) as s:
            s.login(config.SENDGRID_USERNAME, config.SENDGRID_PASSWORD)
            s.send_message(msg)
    except:
        return False
    return True


def send_sudo_request_email(username: str, user_email: str):
    """
    Sends an email notifying SysAdmins that a user has requested an account on feynman.

    :param username the server username of the user who made the request.
    :param user_email the email address of that user to contact them for vetting.
    """
    message_body = \
        """
Hi {username},

Thank you for making a request for an account with sudo privileges on feynman.netsoc.co.

We will be in touch shortly.

Best,

The UCC Netsoc SysAdmin Team.

PS: Please "Reply All" to the emails so that you get a quicker response.

""".format(username=username)

    msg = EmailMessage()
    msg.set_content(message_body)
    msg["From"] = config.NETSOC_ADMIN_EMAIL_ADDRESS
    msg["To"] = config.NETSOC_EMAIL_ADDRESS
    msg["Subject"] = "[Netsoc Help] Sudo request on Feynman for {user}".format(
        user=username)
    msg["Cc"] = tuple(config.SYSADMIN_EMAILS + [user_email])

    with smtplib.SMTP("smtp.sendgrid.net", 587) as s:
        s.login(config.SENDGRID_USERNAME, config.SENDGRID_PASSWORD)
        s.send_message(msg)


def send_help_bot(username: str, email: str, subject: str, message: str) -> bool:
    """
    This sends the help data to the Netsoc Discord Bot, which will then post it in the relevant channel
    in the Netsoc Committee Server
    """
    output = {"user": username, "email": email, "subject": subject, "message": message}
    headers = {'Content-Type': 'application/json'}

    response = requests.post(DISCORD_BOT_HELP_ADDRESS, data=json.dumps(output).encode(), headers=headers)
    return response.status_code == 200

'''
This file takes care of sending off the data from the help section to multiple areas
currently Discord and email of SysAdmins and the main Netsoc email
'''
# lib
import requests

# local
import config
import mail_helper

sysadmin_tag = '<@&547450539726864384>'


def send_help_email(username: str, user_email: str, subject: str, message: str) -> object:
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
    if not config.FLASK_CONFIG['debug']:
        response = mail_helper.send_mail(
            config.NETSOC_ADMIN_EMAIL_ADDRESS,
            config.NETSOC_EMAIL_ADDRESS,
            "[Netsoc Help] " + subject,
            message_body,
            [user_email] + config.SYSADMIN_EMAILS,
        )
    else:
        response = type("Response", (object,), {"status_code": 200})
    return response


def send_sudo_request_email(username: str, user_email: str) -> object:
    """
    Sends an email notifying SysAdmins that a user has requested an account on feynman.

    :param username the server username of the user who made the request.
    :param user_email the email address of that user to contact them for vetting.
    """
    message_body = \
        f"""
Hi {username},

Thank you for making a request for an account with sudo privileges on feynman.netsoc.co.

We will be in touch shortly.

Best,

The UCC Netsoc SysAdmin Team.

PS: Please "Reply All" to the emails so that you get a quicker response.

"""
    return mail_helper.send_mail(
        config.NETSOC_ADMIN_EMAIL_ADDRESS,
        config.NETSOC_EMAIL_ADDRESS,
        "[Netsoc Help] Sudo request on Feynman for " + username,
        message_body,
        [user_email] + config.SYSADMIN_EMAILS,
    )


def send_help_webhook(username: str, email: str, subject: str, message: str) -> bool:
    """
    This sends the help data to the Netsoc Discord Bot, which will then post it in the relevant channel
    in the Netsoc Committee Server
    """
    output = {
        "content": f"{sysadmin_tag}\n\n```From: {username}\nEmail: {email}\n\nSubject: {subject}\n\n{message}```",
    }
    headers = {'Content-Type': 'application/json'}

    if not config.FLASK_CONFIG['debug']:
        response = requests.post(config.DISCORD_WEBHOOK_ADDRESS, json=output, headers=headers)
    else:
        response = type("Response", (object,), {"status_code": 200})
    return response.status_code == 200

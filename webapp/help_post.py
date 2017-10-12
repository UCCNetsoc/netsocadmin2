'''
This file takes care of sending off the data from the help section to multiple areas
currently Discord and email of SysAdmins and the main Netsoc email
'''
import json
from email.message import EmailMessage
import passwords as p
import requests
import smtplib


DISCORD_BOT_HELP_ADDRESS = p.DISCORD_BOT_HELP_ADDRESS



def send_help_email(username:str, user_email:str, subject:str, message:str) -> bool:
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
    message_body = \
    """
From: %s\n
Email: %s

%s"""%(username, user_email, message)
    
    msg = EmailMessage()
    msg.set_content(message_body)
    msg["From"] = p.NETSOC_ADMIN_EMAIL_ADDRESS
    msg["To"] = p.NETSOC_EMAIL_ADDRESS
    msg["Subject"] = "[Netsoc Help] " + subject
    msg["Cc"] = tuple(p.SYSADMIN_EMAILS + [user_email])
    try:
        with smtplib.SMTP("smtp.sendgrid.net", 587) as s:
            s.login(p.SENDGRID_USERNAME, p.SENDGRID_PASSWORD)
            s.send_message(msg)
    except:
        return False
    return True


def send_help_bot(username:str, email:str, subject:str, message:str) -> bool:
    """
    This sends the help data to the Netsoc Discord Bot, which will then post it in the relevant channel
    in the Netsoc Committee Server
    """
    output = {"user":username, "email":email, "subject":subject, "message":message}
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(DISCORD_BOT_HELP_ADDRESS, data=json.dumps(output).encode(), headers=headers)
    return response.status_code == 200

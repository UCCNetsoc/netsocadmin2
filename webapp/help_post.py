'''
This file takes care of sending off the data from the help section to multiple areas
currently Discord and email of SysAdmins and the main Netsoc email
'''
import json
import passwords as p
import requests
from sendgrid import Email, sendgrid
from sendgrid.helpers.mail import Content, Mail
import string
import typing


DISCORD_BOT_HELP_ADDRESS = p.DISCORD_BOT_HELP_ADDRESS
SYSADMIN_EMAILS = p.SYSADMIN_EMAILS


def send_help_email(username:str, email:str, subject_in:str, message:str) -> bool:
    """
    Sends an email containing the help data to the various emails of SysAdmins etc
    Will add more emails soon:tm:
    """
    message_body = \
    """
From: %s\n
Email: %s

%s"""%(username, email, message)

    sg = sendgrid.SendGridAPIClient(apikey=p.SENDGRID_KEY)
    from_email = Email("netsocadmin@netsoc.co")
    subject = "[Netsoc Help] "+subject_in
    content = Content("text/plain", message_body)

    success = False
    for addr in SYSADMIN_EMAILS:
        to_email = Email(addr)
        mail = Mail(from_email, subject, to_email, content)
        response = sg.client.mail.send.post(request_body=mail.get())
        success = success or str(response.status_code).startswith("20")
    return success


def send_help_bot(username:str, email:str, subject:str, message:str) -> bool:
    """
    This sends the help data to the Netsoc Discord Bot, which will then post it in the relevant channel
    in the Netsoc Committee Server
    """
    output = {"user":username, "email":email, "subject":subject, "message":message}
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(DISCORD_BOT_HELP_ADDRESS, data=json.dumps(output).encode(), headers=headers)
    return response.status_code == 200

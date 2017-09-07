'''
This file takes care of sending off the data from the help section to multiple areas
currently Discord and email of SysAdmins and the main Netsoc email
'''

from sendgrid import Email, sendgrid
from sendgrid.helpers.mail import Content, Mail
import string
import passwords as p
import json
import requests

#Sends an email containing the help data to the various emails of SysAdmins etc
#Will add more emails soon:tm:
def send_help_email(username, email, subject_in, message):
    message_body = \
    """
From: %s\n
Email: %s

%s"""%(username, email, message)

    sg = sendgrid.SendGridAPIClient(apikey=p.SENDGRID_KEY)
    from_email = Email("help@netsoc.co")
    to_email = Email("noah@santschi-cooney.ch")
    subject = "[Netsoc Help] "+subject_in
    content = Content("text/plain", message_body)

    mail = Mail(from_email, subject, to_email, content)

    response = sg.client.mail.send.post(request_body=mail.get())

    return str(response.status_code).startswith("20")

#This sends the help data to the Netsoc Discord Bot, which will then post it in the relevant channel
#in the Netsoc Committee Server
def send_help_bot(username, email, subject, message):
    output = {"user":username, "email":email, "subject":subject, "message":message}
    url = "http://strum355.netsoc.co:4201/help"
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, data=json.dumps(output), headers=headers)

    return(response)

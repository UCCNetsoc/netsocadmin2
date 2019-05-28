from typing import List

import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail

import config


def send_mail(from_mail: str, to_mail: str, subject: str, content: str, cc: List[str] = None) -> object:
    sg = sendgrid.SendGridAPIClient(apikey=config.SENDGRID_KEY)
    from_email = Email(from_mail, "UCC Netsoc")
    subject = "Account Registration"
    to_email = Email(to_mail)
    content = Content("text/plain", content)
    mail = Mail(from_email, subject, to_email, content)
    if cc:
        for email in cc:
            mail.personalizations[0].add_cc(Email(email))
    return sg.client.mail.send.post(request_body=mail.get())

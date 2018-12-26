from typing import List
import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail
import config


def send_mail(from_mail: str, to_mail: str, subject: str, content: str, cc: List[str] = None) -> int:
    sg = sendgrid.SendGridAPIClient(apikey=config.SENDGRID_KEY)
    from_email = Email("server.registration@netsoc.co")
    subject = "Account Registration"
    to_email = Email(to_mail)
    content = Content("text/plain", content)
    mail = Mail(from_email, subject, to_email, content)
    if cc:
        for email in cc:
            mail.personalizations[0].add_cc(Email(email))
    return sg.client.mail.send.post(request_body=mail.get())

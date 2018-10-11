from typing import List
import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail, Personalization
import config


def send_mail(from_mail: str, to_mail: str, subject: str, content: str, cc: List[str]=None) -> int:
    sg = sendgrid.SendGridAPIClient(apikey=config.SENDGRID_KEY)
    from_email = Email("server.registration@netsoc.co")
    subject = "Account Registration"
    to_email = Email(to_mail)
    content = Content("text/plain", content)
    mail = Mail(from_email, subject, to_email, content)
    if cc:
        personalization = Personalization()
        for email in cc:
            personalization.add_cc(Email(email))
        mail.add_personalization(personalization)
    return sg.client.mail.send.post(request_body=mail.get())

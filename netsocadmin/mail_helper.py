from typing import List
import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail, Personalization

def send_mail(from_mail: str, to_mail: str, subject: str, content: str, cc: List[str]=None) -> int:
    sg = sendgrid.SendGridAPIClient(apikey=config.SENDGRID_KEY)
    from_email = Email("server.registration@netsoc.co")
    subject = "Account Registration"
    to_email = Email(email)
    content = Content("text/plain", message_body)
    mail = Mail(from_email, subject, to_email, content)
    if cc:
        personlization = Personalization()
        for email in cc:
            personlization.add_cc(Email(email))
        mail.add_personlization(personlization)
    return sg.client.mail.send.post(request_body=mail.get())
import random
import string
from _sha256 import sha256

from sendgrid import Email
from sendgrid import sendgrid
from sendgrid.helpers.mail import Content, Mail

domain = "localhost:5000/"

def send_confirmation_email(given_email):
    """
    Sends email containing the link which users use to set up their accounts.

    Returns true if the email was sent succesfully, false otherwise.
    """
    message_body = "Hello, Email! \n \n" + "Link: " + domain + "signup?t=" + generateTempURI() + "&e=" + given_email

    sg = sendgrid.SendGridAPIClient(apikey="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")
    from_email = Email("lowdown@netsoc.co")
    subject = "Account Registration"
    to_email = Email(given_email)
    content = Content("text/plain", message_body)
    mail = Mail(from_email, subject, to_email, content)

    response = sg.client.mail.send.post(request_body=mail.get())
    return str(response.status_code).startswith("20")


#Genrates URI token and stores to TXT
def generateTempURI():
    uri     = sha256(id_generator().encode('utf-8')).hexdigest()
    uriFile = open("TempUrIs.txt", "a")
    uriFile.write(uri)
    uriFile.write("\n")
    return uri

#Generates Random String
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

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
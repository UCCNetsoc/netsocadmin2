# stdlib
import structlog

# lib
import flask

# local
import help_post

from .index import ProtectedToolView


class Sudo(ProtectedToolView):
    """
    Route: /sudo
        This route will render the page for applying for sudo privilages.
    """
    # Logger instance
    logger = structlog.getLogger("netsocadmin.sudo")

    page_title = "Apply for Sudo"

    template_file = "sudo.html"

    active = "sudo"

    def dispatch_request(self) -> str:
        return self.render()


class CompleteSudo(Sudo):
    """
    Route: /completesudoapplication
        This is run by the sudo-signup form in sudo.html.
        It will send an email to the SysAdmin team as well as to the discord server notifying us that a request for
            sudo on feynman has been made.
    """

    logger = structlog.getLogger("netsocadmin.completesudoapplication")

    methods = ["POST"]

    template_file = "message.html"

    def dispatch_request(self) -> str:
        # Get the details from the form data
        email = flask.request.form["email"]
        reason = flask.request.form["reason"]
        username = flask.session["username"]
        email_failed = False
        discord_failed = False

        # Try to send the email
        try:
            email_resp = help_post.send_sudo_request_email(username, email)
            if not str(email_resp.status_code).startswith("20"):
                self.logger.error(f"non 20x status code for help email: {email_resp.status_code} - {email_resp.body}")
            email_failed = not str(email_resp.status_code).startswith("20")
        except Exception as e:
            email_failed = True
            self.logger.error(f"failed to send email: {e}")

        # Try to send a message to the Discord
        try:
            subject = "Feynman Account Request"
            msg = f"This user wants an account on Feynman pls.\nReason: {reason}"
            discord_failed = help_post.send_help_webhook(username, email, subject, msg)
        except Exception as e:
            discord_failed = True
            self.logger.error(f"failed to fire discord webhook: {e}")

        if discord_failed and email_failed:
            caption = "There was a problem :("
            message = "Please email netsoc@uccsocieties.ie instead!"
        else:
            caption = "Success!"
            message = "A confirmation email has been sent to you. We will be in touch shortly." + \
                "<br/>Return to <a href='/tools'>tools page</a>."
        # Return an appropriate response depending on whether or not the message sent
        return self.render(
            caption=caption,
            message=message,
        )

# stdlib
import logging

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
    logger = logging.getLogger("netsocadmin.sudo")

    page_title = "Apply for Sudo"

    template_file = "sudo.html"

    active = "sudo"

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        return self.render()


class CompleteSudo(Sudo):
    """
    Route: /completesudoapplication
        This is run by the sudo-signup form in sudo.html.
        It will send an email to the SysAdmin team as well as to the discord server notifying us that a request for
            sudo on feynman has been made.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.completesudoapplication")
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]

    template_file = "message.html"

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        # Get the details from the form data
        email = flask.request.form["email"]
        reason = flask.request.form["reason"]
        username = flask.session["username"]
        email_failed = False
        discord_failed = False

        # Try to send the email
        try:
            help_post.send_sudo_request_email(username, email)
        except Exception as e:
            email_failed = True
            self.logger.error(f"Failed to send email: {e}")

        # Try to send a message to the Discord
        try:
            subject = "Feynman Account Request"
            msg = f"This user wants an account on Feynman pls.\nReason: {reason}"
            help_post.send_help_webhook(username, email, subject, msg)
        except Exception as e:
            discord_failed = True
            self.logger.error(f"Failed to send message to Discord: {e}")

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

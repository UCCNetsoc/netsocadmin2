# stdlib
import logging

# lib
import flask

# local
import help_post
import login_tools

from .index import ProtectedToolView


class CompleteSudo(ProtectedToolView):
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

    page_title = "Apply for Sudo"

    def render(self, error=False) -> str:
        """Render the template with appropriate messages for whether or not there's an error"""
        if error:
            caption = "There was a problem :("
            message = "Please email netsoc@uccsocieties.ie instead!"
        else:
            caption = "Success!"
            message = "A confirmation email has been sent to you. We will be in touch shortly." + \
                "<br/>Return to <a href='/tools'>tools page</a>."
        return flask.render_template(
            "message.html",
            is_logged_in=login_tools.is_logged_in(),
            caption=caption,
            message=message,
        )

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

        # Return an appropriate response depending on whether or not the message sent
        return self.render(email_failed and discord_failed)


class Sudo(ProtectedToolView):
    """
    Route: /sudo
        This route will render the page for applying for sudo privilages.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.sudo")

    page_title = "Apply for Sudo"

    template_file = "sudo.html"

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        return self.render()

import logging

import flask

import help_post

from .index import ProtectedToolView


class HelpView(ProtectedToolView):
    template_file = "help.html"

    page_title = "Help"

    active = "help"

    def dispatch_request(self, **data):
        return self.render(**data)


class Help(HelpView):
    """
    Route: help
        This takes care of the help section, sending the data off
        to the relevant functions.
        This can only be reached if you are logged in.
    """
    # Specify the method(s) that are allowed to be used to reach this view
    methods = ["POST"]
    # Logger instance
    logger = logging.getLogger("netsocadmin.help")

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        email = flask.request.form.get("email", "")
        subject = flask.request.form.get("subject", "")
        message = flask.request.form.get("message", "")
        # Ensure all fields are populated
        if not all([email, subject, message]):
            self.logger.debug("Not all fields specified")
            return self.render(help_error="Please specify all fields", help_active=True)
        # Send the email
        sent_email = help_post.send_help_email(flask.session["username"], email, subject, message)
        # Try and send to Discord bot
        try:
            sent_discord = help_post.send_help_webhook(flask.session["username"], email, subject, message)
        except Exception as e:
            self.logger.error(f"Failed to send message to discord bot: {str(e)}")
            # in this case, the Discord bot was unreachable. We log this error but
            # continue as success because the email may still be sent. This fix will have
            # to remain until the Discord bot becomes more reliable.
            sent_discord = True
        # Check that at least one form of communication was sent
        if not sent_email and not sent_discord:
            # If not, report an error to the user
            self.logger.error(f"Unable to send email and unable to send to discord bot: {message}")
            return self.render(
                help_error="There was a problem :( Please email netsoc@uccsocieties.ie instead",
                help_active=True,
            )
        # Otherwise when things are okay, report back stating so
        self.logger.debug("Successfully sent help email or contacted discord bot")
        return self.render(help_success=True, help_active=True)

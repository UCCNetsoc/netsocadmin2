import structlog as logging

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
        email = flask.request.form.get("email", "")
        subject = flask.request.form.get("subject", "")
        message = flask.request.form.get("message", "")
        # Ensure all fields are populated
        if not all([email, subject, message]):
            self.logger.info("not all fields specified")
            return self.render(help_error="Please specify all fields", help_active=True)

        sent_email, sent_discord = True, True

        # Send the email
        try:
            email_resp = help_post.send_help_email(flask.session["username"], email, subject, message)
            if not str(email_resp.status_code).startswith("20"):
                self.logger.error(f"non 20x status code for help email: {email_resp.status_code} - {email_resp.body}")
            sent_email = str(email_resp.status_code).startswith("20")
        except Exception as e:
            self.logger.error(f"failed to send help email: {str(e.body)}")

        # Try and send to Discord
        try:
            sent_discord = help_post.send_help_webhook(flask.session["username"], email, subject, message)
        except Exception as e:
            self.logger.error(f"failed to send help discord webhook: {str(e)}")

        # Check that at least one form of communication was sent
        if not sent_email and not sent_discord:
            # If not, report an error to the user
            return self.render(
                help_error="There was a problem :( Please email netsoc@uccsocieties.ie instead",
                help_active=True,
            )
        # Otherwise when things are okay, report back stating so
        message = ''
        if sent_email:
            message += "sent help email"
        if sent_discord and sent_email:
            message += " and "
        if sent_discord:
            message += "fired discord webhook"
        self.logger.info(message)
        return self.render(help_success=True, help_active=True)

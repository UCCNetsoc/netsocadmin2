# stdlib
import logging
import re
# lib
import flask
from flask.views import View
# local
import config
import register_tools


__all__ = [
    'CompleteSignup',
    'Confirmation',
    'Signup',
    'Username',
]


class CompleteSignup(View):
    """
    Route: /completeregistration
        This is the route which is run by the registration form
        and should only be available through POST. It adds the
        given data to the Netsoc LDAP database.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.completeregistration")
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        # make sure token is valid
        email = flask.request.form["email"]
        uri = flask.request.form["_token"]
        if not register_tools.good_token(email, uri):
            self.logger.debug(f"Invalid token {uri} for email {email}")
            return flask.render_template(
                "index.html",
                page="login",
                error_message="Your token has expired or never existed. Please try again or contact us",
            )

        # make sure form is flled out and username is still legit
        form_fields = (
            flask.request.form["email"],
            flask.request.form["_token"],
            flask.request.form["uid"],
            flask.request.form["name"],
            flask.request.form["student_id"],
            flask.request.form["course"],
            flask.request.form["graduation_year"],
        )
        if not all(form_fields):
            return flask.render_template(
                "form.html",
                email_address=email,
                token=uri,
                error_message="You must fill out all of the fields",
            )

        user = flask.request.form["uid"]
        if register_tools.has_username(user):
            self.logger.debug(f"Username {user} not available")
            return flask.render_template(
                "form.html",
                email_address=email,
                token=uri,
                error_message="The requested username is not available",
            )

        # add user to ldap db
        success, info = register_tools.add_ldap_user(user)
        if not success:
            self.logger.debug(f"Failed to add user to LDAP: {info}")
            # clean db of token so they have to start again
            register_tools.remove_token(email)
            return flask.render_template(
                "index.html",
                page="login",
                error_message="An error occured. Please try again or contact us")

        # add all info to Netsoc MySQL DB
        info["name"] = flask.request.form["name"]
        info["student_id"] = flask.request.form["student_id"]
        info["course"] = flask.request.form["course"]
        info["grad_year"] = flask.request.form["graduation_year"]
        info["email"] = email
        if not register_tools.add_netsoc_database(info):
            self.logger.debug("Failed to add data to mysql db")
            return flask.render_template(
                "index.html",
                page="login",
                error_message="An error occured. Please try again or contact us")

        # send user's details to them
        if not register_tools.send_details_email(email, user, info["password"]):
            self.logger.debug("Failed to send confirmation email")
            return flask.render_template(
                "index.html",
                page="login",
                error_message="An error occured. Please try again or contact us")

        # initialise the user's home directories so they can use netsoc admin
        # without ever having to SSH into the server.
        if not config.FLASK_CONFIG["debug"]:
            register_tools.initialise_directories(user, info["password"])

        # registration complete, remove their token
        register_tools.remove_token(email)

        caption = "Thank you!"
        message = "An email has been sent with your log-in details. Please change your password as soon as you log in."
        self.logger.debug(f"Successfully signed up {flask.request.form['name']} and confirmation email sent")
        return flask.render_template("message.html", caption=caption, message=message)


class Confirmation(View):
    """
    Route: /sendconfirmation
        Users will be lead to this route when they submit an email for server sign up from route /
        sendconfirmation() will check whether users posted data via a form.
        It then checks that form data to make sure it's a valid UCC email.
        Sends an email with a link to validate the email holder is who is registering.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.sendcomfirmation")
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        # make sure is ucc email
        email = flask.request.form['email']
        if not re.match(r"[0-9]{9}@umail\.ucc\.ie", email) and not re.match(r"[a-zA-Z0-9]+@uccsocieties.ie", email):
            self.logger.debug(f"Email {email} is not a valid UCC email")
            return flask.render_template(
                "index.html",
                page="login",
                error_message="Must be a UCC Umail or Society email address")

        # make sure email has not already been used to make an account
        if email not in config.EMAIL_WHITELIST and register_tools.has_account(email):
            self.logger.debug(f"Account already exists with email {email}")
            return flask.render_template(
                "message.html",
                caption="Sorry!",
                message=(
                    f"There is an existing account with email '{email}'. "
                    "Please contact us if you think this is an error."
                ),
            )

        # send confirmation link to ensure they own the email account
        out_email = (
            "admin.netsoc.co" if not config.FLASK_CONFIG["debug"]
            else f"{config.FLASK_CONFIG['host']}:{config.FLASK_CONFIG['port']}"
        )
        confirmation_sent = register_tools.send_confirmation_email(email, out_email)
        if not confirmation_sent:
            self.logger.debug("Confirmation email failed to send")
            return flask.render_template(
                "index.html",
                page="login",
                error_message="An error occured. Please try again or contact us")

        caption = "Thank you!"
        message = f"Your confirmation link has been sent to {email}"
        self.logger.debug(f"Confirmation link sent to {email}")
        return flask.render_template("message.html", caption=caption, message=message)


class Signup(View):
    """
    Route: signup
        This is the link which they will be taken to with the confirmation email.
        It checks if the token they have used is valid and corresponds to the email.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.signup")

    def render(self, email: str, token: str, error: bool = False) -> str:
        """Render the template with appropriate messages for whether or not there's an error"""
        if error:
            self.logger.debug(f"Bad token {token} used for email {email}")
            template = "index.html"
            kw = {"error_message": "Your request was not valid. Please try again or contact us."}
        else:
            template = "form.html"
            kw = {"email_address": email, "token": token}
        return flask.render_template(template, **kw)

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        # Make sure they haven't forged the URL
        email = flask.request.args.get("e")
        token = flask.request.args.get("t")
        return self.render(email, token, not register_tools.good_token(email, token))


class Username(View):
    """
    Route: username
        This should be called by javascript in the registration form
        to test whether or not a username is already used.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.username")
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        if ("email" not in flask.request.headers or "uid" not in flask.request.headers or
                "token" not in flask.request.headers):
            self.logger.debug("Invalid request some information missing. Aborting.")
            return flask.abort(400)

        # check if request is legit
        email = flask.request.headers["email"]
        token = flask.request.headers["token"]
        if not register_tools.good_token(email, token):
            self.logger.debug(f"Bad token {token} used for email {email}")
            return flask.abort(403)

        # check db for username
        requested_username = flask.request.headers["uid"]
        if register_tools.has_username(requested_username):
            self.logger.debug(f"Uid {requested_username} is in use")
            return "Not available"
        self.logger.debug(f"Username {requested_username} available")
        return "Available"

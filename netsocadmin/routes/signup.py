# stdlib
import re

# lib
import flask
import sentry_sdk
import structlog as logging
from flask.views import View

# local
import config
import mysql
import register_tools

__all__ = [
    'CompleteSignup',
    'ResetPassword',
    'Forgot',
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
        # make sure token is valid
        email = flask.request.form["email"]
        uri = flask.request.form["_token"]

        with sentry_sdk.configure_scope() as scope:
            scope.user = {
                "email": email,
            }

        mysql_conn = None

        if not register_tools.good_token(email, uri):
            self.logger.warn(f"invalid token {uri} for email {email}")
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
        )
        if not all(form_fields):
            return flask.render_template(
                "form.html",
                email_address=email,
                token=uri,
                error_message="You must fill out all of the fields",
            )

        user = flask.request.form["uid"]
        if user != user.lower():
            return flask.render_template(
                "form.html",
                email_address=email,
                token=uri,
                error_message="The requested username contains uppercase characters.\
                 Please enter a username in lowercase",
            )

        if len(user) > 15:
            return flask.render_template(
                "form.html",
                email_address=email,
                token=uri,
                error_message="The requested username is too long. Maximum length is 15 characters",
            )

        try:
            if register_tools.is_in_ldap(user):
                self.logger.info(f"username {user} not available")
                return flask.render_template(
                    "form.html",
                    email_address=email,
                    token=uri,
                    error_message="The requested username is not available",
                )

            # add user to ldap db
            info = register_tools.add_ldap_user(user)

            # add all info to Netsoc MySQL DB
            info["name"] = flask.request.form["name"]
            info["email"] = email
            mysql_conn = register_tools.add_netsoc_database(info)

            mysql_pass = mysql.create_user(user)

            # send user's details to them
            if not register_tools.send_details_email(email, user, info["password"], mysql_pass):
                self.logger.error(f"failed to send confirmation email")

            # initialise the user's home directories so they can use netsoc admin
            # without ever having to SSH into the server.
            if not config.FLASK_CONFIG["debug"]:
                register_tools.initialise_directories(user, info["password"])

            # all went well, commit changes to MySQL
            mysql_conn.commit()

            # registration complete, remove their token
            register_tools.remove_token(email)
        except register_tools.UserExistsInLDAPException:
            return flask.render_template(
                "index.html",
                page="login",
                error_message="A user already exists with that username.",
            )
        except (register_tools.LDAPException, register_tools.MySQLException) as e:
            self.logger.error(f"ldap or mysql error when creating user: {e}")
            # If an error occured, roll back changes
            register_tools.remove_token(email)
            if mysql_conn is not None:
                mysql_conn.rollback()
            if register_tools.is_in_ldap(user):
                register_tools.remove_ldap_user(user)
            mysql.delete_user(user)
            return flask.render_template(
                "index.html",
                page="login",
                error_message="An error occured. Please try again or contact us",
            )
        except Exception as e:
            # If an error occured, roll back changes
            register_tools.remove_token(email)
            if mysql_conn is not None:
                mysql_conn.rollback()
            if register_tools.is_in_ldap(user):
                register_tools.remove_ldap_user(user)
            # TODO preserve stacktrace
            raise e
        finally:
            if mysql_conn is not None:
                mysql_conn.close()

        caption = "Thank you!"
        message = "An email has been sent with your log-in details. Please change your password as soon as you log in."
        self.logger.info(f"successfully signed up {flask.request.form['name']} and confirmation email sent")
        return flask.render_template("message.html", caption=caption, message=message)

class ResetPassword(View):
    """
    Route: /resetpassword
        This is the link which they will be taken to with the forgot email.
        It checks if the token they have used is valid and corresponds to the email.
        It then resets the password.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.resetpassword")

    def render(self, user, email: str, token: str, error: bool = False) -> str:
        """Render the template with appropriate messages for whether or not there's an error"""
        if error:
            self.logger.warn(f"bad token {token} used for email {email}")
            template = "index.html"
            kw = {"error_message": "Your request was not valid. Please try again or contact us."}
            return flask.render_template(template, **kw)

        register_tools.remove_token(email)

        reset_resp = register_tools.reset_password(user, email)

        if reset_resp == False:
            return flask.render_template(
                "index.html",
                page="login",
                error_message="An error occured. Please try again or contact us",
            )

        template = "message.html"
        caption = "Success!"
        message = f"An email has been sent with your new password. Please change your password as soon as you log in."
        return flask.render_template(template, caption=caption, message=message)

    def dispatch_request(self) -> str:
        # Make sure they haven't forged the URL
        user = flask.request.args.get("u")
        email = flask.request.args.get("e")
        with sentry_sdk.configure_scope() as scope:
            scope.user = {
                "email": email,
            }

        token = flask.request.args.get("t")
        return self.render(user, email, token, not register_tools.good_token(email, token))

class Forgot(View):
    """
    Route: /forgot
        Users will be lead to this route when they submit an email for a reminder of their
        username and, optionally, resetting their password.
        It then checks that form data to make sure it's a valid UCC email.
        Sends an email with a link to validate the email holder is who is registering.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.forgot")
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]

    def dispatch_request(self) -> str:
        # make sure is ucc email
        email = flask.request.form['email']

        with sentry_sdk.configure_scope() as scope:
            scope.user = {
                "email": email,
            }

        if not re.match(r"[0-9]{8,11}@umail\.ucc\.ie", email) and not re.match(r"[a-zA-Z.0-9]+@uccsocieties.ie", email):
            self.logger.info(f"email {email} is not a valid UCC email")
            return flask.render_template(
                "index.html",
                page="login",
                error_message="Must be a UCC Umail or Society email address")

        # make sure email has not already been used to make an account
        if email in config.EMAIL_WHITELIST or not register_tools.has_account(email):
            self.logger.info(f"account doesn't exist with email {email}")
            return flask.render_template(
                "message.html",
                caption="Sorry!",
                message=(
                    f"There isn't an existing account with email '{email}'. "
                    "Please contact us if you think this is an error."
                ),
            )

        # send confirmation link to ensure they own the email account
        out_email = (
            "admin.netsoc.co" if not config.FLASK_CONFIG["debug"]
            else f"{config.FLASK_CONFIG['host']}:{config.FLASK_CONFIG['port']}"
        )
        forgot_resp = register_tools.send_forgot_email(email, out_email)
        if not str(forgot_resp.status_code).startswith("20"):
            self.logger.error("confirmation email failed to send")
            return flask.redirect("/?e=e")

        caption = "Success!"
        if not config.FLASK_CONFIG["debug"]:
            message = f"Your username reminder and password reset link has been sent to {email}"
        else:
            host = config.FLASK_CONFIG['host']
            port = config.FLASK_CONFIG['port']
            message = f"Forgot URL: \
                <a href='http://{host}:{port}/resetpassword?t={forgot_resp.token}&e={email}&u={forgot_resp.user}'>\
                    http://{host}:{port}/resetpassword?t={forgot_resp.token}&e={email}&u={forgot_resp.user}</a>"
        self.logger.info(f"forgot username link sent to {email}")
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
    logger = logging.getLogger("netsocadmin.sendconfirmation")
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]

    def dispatch_request(self) -> str:
        # make sure is ucc email
        email = flask.request.form['email']

        with sentry_sdk.configure_scope() as scope:
            scope.user = {
                "email": email,
            }

        if not re.match(r"[0-9]{8,11}@umail\.ucc\.ie", email) and not re.match(r"[a-zA-Z.0-9]+@uccsocieties.ie", email):
            self.logger.info(f"email {email} is not a valid UCC email")
            return flask.render_template(
                "index.html",
                page="login",
                error_message="Must be a UCC Umail or Society email address")

        # make sure email has not already been used to make an account
        if email not in config.EMAIL_WHITELIST and register_tools.has_account(email):
            self.logger.info(f"account already exists with email {email}")
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
        confirmation_resp = register_tools.send_confirmation_email(email, out_email)
        if not str(confirmation_resp.status_code).startswith("20"):
            self.logger.error("confirmation email failed to send")
            return flask.redirect("/?e=e")

        caption = "Thank you!"
        if not config.FLASK_CONFIG["debug"]:
            message = f"Your confirmation link has been sent to {email}"
        else:
            host = config.FLASK_CONFIG['host']
            port = config.FLASK_CONFIG['port']
            message = f"Confirmation URL: \
                <a href='http://{host}:{port}/signup?t={confirmation_resp.token}&e={email}'>\
                    http://{host}:{port}/signup?t={confirmation_resp.token}&e={email}</a>"
        self.logger.info(f"confirmation link sent to {email}")
        return flask.render_template("message.html", caption=caption, message=message)


class Signup(View):
    """
    Route: /signup
        This is the link which they will be taken to with the confirmation email.
        It checks if the token they have used is valid and corresponds to the email.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.signup")

    def render(self, email: str, token: str, error: bool = False) -> str:
        """Render the template with appropriate messages for whether or not there's an error"""
        if error:
            self.logger.warn(f"bad token {token} used for email {email}")
            template = "index.html"
            kw = {"error_message": "Your request was not valid. Please try again or contact us."}
        else:
            template = "form.html"
            kw = {"email_address": email, "token": token}
        return flask.render_template(template, **kw)

    def dispatch_request(self) -> str:
        # Make sure they haven't forged the URL
        email = flask.request.args.get("e")
        with sentry_sdk.configure_scope() as scope:
            scope.user = {
                "email": email,
            }

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
        if ("email" not in flask.request.headers or "uid" not in flask.request.headers or
                "token" not in flask.request.headers):
            self.logger.info("invalid request some information missing, aborting.")
            return flask.abort(400)

        # check if request is legit
        email = flask.request.headers["email"]
        token = flask.request.headers["token"]

        with sentry_sdk.configure_scope() as scope:
            scope.user = {
                "email": email,
            }

        if not register_tools.good_token(email, token):
            self.logger.info(f"bad token {token} used for email {email}")
            return flask.abort(403)

        # check db for username
        requested_username = flask.request.headers["uid"]
        if register_tools.is_in_ldap(requested_username):
            self.logger.info(f"username {requested_username} is in use")
            return "Not available"
        self.logger.info(f"username {requested_username} available")
        return "Available"

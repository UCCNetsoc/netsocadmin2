"""
This file contains the main webapp for netsoc admin.
Sets up a local server running the website. Requests should
then be proxied to this address.
"""
import os
import re
import sys

import flask
import login_tools
import register_tools as r
import routes
import config


TUTORIALS = []


app = flask.Flask("netsocadmin")
app.secret_key = config.SECRET_KEY
app.config["SESSION_REFRESH_EACH_REQUEST"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 10  # seconds


@app.route('/')
def signinup():
    """
    Route: /
        This route is for the index page. If a user is already logged in, it will
        redirect to the server tools page.
    """
    if login_tools.is_logged_in():
        return flask.redirect("/tools")

    app.logger.debug("Received index page request")
    return flask.render_template("index.html")


# ------------------------------Server Signup Routes------------------------------#


@app.route("/sendconfirmation", methods=["POST"])
def sendconfirmation() -> str:
    """
    Route: /sendconfirmation
        Users will be lead to this route when they submit an email for server sign up from route /
        sendconfirmation() will check whether users posted data via a form.
        It then checks that form data to make sure it's a valid UCC email.
        Sends an email with a link to validate the email holder is who is registering.
    """
    # make sure is ucc email
    email = flask.request.form['email']
    if not re.match(r"[0-9]{9}@umail\.ucc\.ie", email):
        app.logger.debug(f"sendconfirmation(): address {email} is not a valid UCC email")
        return flask.render_template("index.html", error_message="Must be a UCC Umail email address")

    # make sure email has not already been used to make an account
    if email not in config.EMAIL_WHITELIST and r.has_account(email):
        caption = "Sorry!"
        message = f"There is an existing account with email '{email}'. Please contact us if you think this is an error."
        app.logger.debug(f"sendconfirmation(): account already exists with email {email}")
        return flask.render_template("message.html", caption=caption, message=message)

    # send confirmation link to ensure they own the email account
    out_email = "admin.netsoc.co" if not DEBUG else f"{config.FLASK_CONFIG['HOST']}:{config.FLASK_CONFIG['PORT']}"
    confirmation_sent = r.send_confirmation_email(email, out_email)
    if not confirmation_sent:
        app.logger.debug("sendconfirmation(): confirmation email failed to send")
        return flask.render_template("index.html", error_message="An error occured. Please try again or contact us")

    caption = "Thank you!"
    message = f"Your confirmation link has been sent to {email}"
    return flask.render_template("message.html", caption=caption, message=message)


@app.route("/signup")
def signup() -> str:
    """
    Route: signup
        This is the link which they will be taken to with the confirmation email.
        It checks if the token they have used is valid and corresponds to the email.
    """
    # make sure they haven't forged the URI
    email = flask.request.args.get('e')
    uri = flask.request.args.get('t')
    if not r.good_token(email, uri):
        app.logger.debug(f"signup(): bad token {uri} used for email {email}")
        return flask.render_template(
            "index.html",
            error_message="Your request was not valid. Please try again or contact us",
        )

    return flask.render_template("form.html", email_address=email, token=uri)


@app.route("/completeregistration", methods=["POST"])
def completeregistration():
    """
    Route: register
        This is the route which is run by the registration form
        and should only be available through POST. It adds the
        given data to the Netsoc LDAP database.
    """
    # make sure token is valid
    email = flask.request.form["email"]
    uri = flask.request.form["_token"]
    if not r.good_token(email, uri):
        app.logger.debug(f"completeregistration(): invalid token {uri} for email {email}")
        return flask.render_template(
            "index.html",
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
    if r.has_username(user):
        return flask.render_template(
            "form.html",
            email_address=email,
            token=uri,
            error_message="The requested username is not available",
        )

    # add user to ldap db
    success, info = r.add_ldap_user(user)
    if not success:
        app.logger.debug(f"completeregistration(): failed to add user to LDAP: {info}")
        # clean db of token so they have to start again
        r.remove_token(email)
        return flask.render_template("index.html", error_message="An error occured. Please try again or contact us")

    # add all info to Netsoc MySQL DB
    info["name"] = flask.request.form["name"]
    info["student_id"] = flask.request.form["student_id"]
    info["course"] = flask.request.form["course"]
    info["grad_year"] = flask.request.form["graduation_year"]
    info["email"] = email
    app.logger.debug(f"info: {info}")
    if not r.add_netsoc_database(info):
        app.logger.debug("completeregistration(): failed to add data to mysql db")
        return flask.render_template("index.html", error_message="An error occured. Please try again or contact us")

    # send user's details to them
    if not r.send_details_email(email, user, info["password"]):
        app.logger.debug("completeregistration(): failed to send confirmation email")
        return flask.render_template("index.html", error_message="An error occured. Please try again or contact us")

    # initialise the user's home directories so they can use netsoc admin
    # without ever having to SSH into the server.
    r.initialise_directories(user, info["password"])

    # registration complete, remove their token
    r.remove_token(email)

    caption = "Thank you!"
    message = "An email has been sent with your log-in details. Please change your password as soon as you log in."
    return flask.render_template("message.html", caption=caption, message=message)


@app.route("/username", methods=["POST"])
def username():
    """
    Route: username
        This should be called by javascript in the registration form
        to test whether or not a username is already used.
    """
    if ("email" not in flask.request.headers or
            "uid" not in flask.request.headers or
            "token" not in flask.request.headers):
        return flask.abort(400)

    # check if request is legit
    email = flask.request.headers["email"]
    token = flask.request.headers["token"]
    if not r.good_token(email, token):
        return flask.abort(403)

    # check db for username
    requested_username = flask.request.headers["uid"]
    if r.has_username(requested_username):
        app.logger.debug(f"username(): uid {requested_username} is in use")
        return "Not available"
    return "Available"


# -------------------------------Login/Logout Routes-----------------------------#
app.add_url_rule('/login', view_func=routes.Login.as_view('login'))
app.add_url_rule('/logout', view_func=routes.Logout.as_view('logout'))

# -------------------------------Server Tools Routes----------------------------- #
app.add_url_rule(
    '/backup/<string:username>/<string:timeframe>/<string:backup_date>',
    view_func=routes.Backup.as_view('backup'),
)
app.add_url_rule('/change-shell', view_func=routes.ChangeShell.as_view('change_shell'))
app.add_url_rule('/createdb', view_func=routes.CreateDB.as_view('createdb'))
app.add_url_rule('/deletedb', view_func=routes.DeleteDB.as_view('deletedb'))
app.add_url_rule('/help', view_func=routes.Help.as_view('help'))
app.add_url_rule('/resetpw', view_func=routes.ResetPassword.as_view('resetpw'))
app.add_url_rule('/tools', view_func=routes.ToolIndex.as_view('tools'))
app.add_url_rule('/wordpressinstall', view_func=routes.WordpressInstall.as_view('wordpressinstall'))


# ------------------------------------Tutorials---------------------------------- #
app.add_url_rule('/tutorials', view_func=routes.Tutorials.as_view('tutorials'))


# --------------------------------------Sudo------------------------------------- #
app.add_url_rule('/sudo', view_func=routes.Sudo.as_view('sudo'))
app.add_url_rule('/completesudoapplication', view_func=routes.CompleteSudo.as_view('completesudoapplication'))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        DEBUG = True

    if os.getenv("NETSOCADMINDEBUG"):
        DEBUG = True

    app.run(
        threaded=True,
        **config.FLASK_CONFIG,
    )

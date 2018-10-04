"""
This file contains the main webapp for netsoc admin.
Sets up a local server running the website. Requests should
then be proxied to this address.
"""
import os
import re
import sys

import flask
import help_post
import markdown
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


@app.route("/login", methods=["POST"])
def login():
    """
    Route: login
    This route should be reached by a form sending login information to it via
    a POST request.
    """
    if not login_tools.is_correct_password(flask.request.form["username"], flask.request.form["password"]):
        return flask.render_template("index.html", error_message="Username or password was incorrect")
    if not config.FLASK_CONFIG["debug"]:
        r.initialise_directories(flask.request.form["username"], flask.request.form["password"])
    flask.session[config.LOGGED_IN_KEY] = True
    flask.session["username"] = flask.request.form["username"]
    return flask.redirect("/")


@app.route("/logout")
def logout():
    """
    Route: logout
        This route logs a user out an redirects them back to the index page.
    """
    flask.session.pop(config.LOGGED_IN_KEY, None)
    return flask.redirect("/")


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
def populate_tutorials():
    """
    Opens the tutorials folder and parses all of the markdown tutorials
    contained within.
    """
    for tut_file in filter(lambda f: f.endswith(".md"), os.listdir(config.TUTORIAL_FOLDER)):
        with open(os.path.join(config.TUTORIAL_FOLDER, tut_file)) as f:
            tutorial = markdown.markdown(f.read())
            TUTORIALS.append(flask.Markup(tutorial))


@app.route("/tutorials")
def tutorials():
    """
    Route: /tutorials
        This route will render the tutorials page. Note that the markdown tutorial
        files are read when the application starts-up.
    """
    global TUTORIALS
    if len(TUTORIALS) == 0:
        return flask.render_template(
            "tutorials.html",
            show_logout_button=login_tools.is_logged_in(),
            error="No tutorials to show",
        )
    if DEBUG:
        TUTORIALS = []
        populate_tutorials()
    return flask.render_template(
        "tutorials.html",
        show_logout_button=login_tools.is_logged_in(),
        tutorials=TUTORIALS,
    )


# --------------------------------------Sudo------------------------------------- #
@app.route("/sudo")
@login_tools.protected_page
def sudo():
    """
    Route: /sudo
        This route will render the page for applying for sudo privilages.
    """
    return flask.render_template("sudo.html",
                                 show_logout_button=login_tools.is_logged_in(),
                                 username=flask.session["username"])


@app.route("/completesudoapplication", methods=["POST"])
@login_tools.protected_page
def completesudoapplication():
    """
    Route: /completesudoapplication
        This is run by the sudo-signup form in sudo.html. It will send an
        email to the SysAdmin team as well as to the discord server
        notifying us that a request for sudo on feynman has been made.
    """
    email = flask.request.form["email"]
    reason = flask.request.form["reason"]
    username = flask.session['username']

    email_failed, discord_failed = False, False
    try:
        help_post.send_sudo_request_email(username, email)
    except Exception as e:
        email_failed = True
        app.logger.error(f"Failed to send email: {str(e)}")

    try:
        help_post.send_help_bot(
            username,
            email,
            "Feynman Account Request",
            f"This user wants an account on feynman pls.\nReason: {reason}",
        )
    except Exception as e:
        discord_failed = True
        app.logger.error(f"Failed to send message to discord bot: {str(e)}")

    if email_failed and discord_failed:
        return flask.render_template(
            "message.html",
            show_logout_button=login_tools.is_logged_in(),
            caption="There was a problem :(",
            message="Please email netsoc@uccsocieties.ie instead",
        )

    return flask.render_template(
        "message.html",
        show_logout_button=login_tools.is_logged_in(),
        caption="Success!",
        message="A confirmation email has been sent to you. We will be in touch shortly.",
    )


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        DEBUG = True

    if os.getenv("NETSOCADMINDEBUG"):
        DEBUG = True

    populate_tutorials()

    app.run(
        threaded=True,
        **config.FLASK_CONFIG,
    )

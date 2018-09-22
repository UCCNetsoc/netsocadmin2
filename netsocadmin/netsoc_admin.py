"""
This file contains the main webapp for netsoc admin.
Sets up a local server running the website. Requests should
then be proxied to this address.
"""
import os
import re
import sys

import flask
import ldap3
import markdown
import netsocadmin.backup_tools as b
import netsocadmin.cli.mysql as m
import netsocadmin.help_post as h
import netsocadmin.login_tools as l
import netsocadmin.register_tools as r
import netsocadmin.wordpress_install as w
from netsocadmin import config


TUTORIALS = []


app = flask.Flask(__name__)
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
    if l.is_logged_in():
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
        return flask.render_template("index.html", error_message="Your request was not valid. Please try again or contact us")

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
        return flask.render_template("index.html", error_message="Your token has expired or never existed. Please try again or contact us")

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
    if not l.is_correct_password(flask.request.form["username"], flask.request.form["password"]):
        return flask.render_template("index.html", error_message="Username or password was incorrect")
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


# -------------------------------Server Tools Routes-----------------------------#


@app.route("/tools")
@l.protected_page
def tools():
    """
    Route: tools
        This is the main page where the server tools that users can avail of are
        displayed.
        Note that this should only be shown when a user is logged in.
    """
    app.logger.debug("tools(): received tools page request")

    return render_tools()


@app.route("/createdb", methods=["POST"])
@l.protected_page
def createdb():
    """
    Route: createdb
        This route must be accessed via post. It is used to create a new
        database with the name in the request.form.
        This can only be reached if you are logged in.
    """
    app.logger.debug(f"Form: {flask.request.form}")
    username = flask.request.form["username"]
    password = flask.request.form["password"]
    dbname = flask.request.form["dbname"]

    # make sure each value is non-empty
    if not all([username, password, dbname]):
        return render_tools(
            mysql_error="Please specify all fields.",
            mysql_active=True,
        )

    # if password is correct, create the new database
    if not l.is_correct_password(username, password):
        return render_tools(
            mysql_error="Wrong username or password.",
            mysql_active=True,
        )
    try:
        m.create_database(username, dbname, False)
    except m.DatabaseAccessError as e:
        return render_tools(
            mysql_error=e.__cause__,
            mysql_active=True,
        )
    # Why does it redirect? Shouldn't it display a message?
    return flask.redirect("/")


@app.route("/deletedb", methods=["POST"])
@l.protected_page
def deletedb():
    """
    Route: deletedb
        This route must be accessed via post. It is used to delete the database
        contained in the request.form. This can only be reached if you are
        logged in.
    """
    app.logger.debug(f"Form: {flask.request.form}")
    username = flask.request.form["username"]
    password = flask.request.form["password"]
    dbname = flask.request.form["dbname"]

    # make sure each value is non-empty
    if not all([username, password, dbname]):
        return render_tools(
            mysql_error="Please specify all fields.",
            mysql_active=True,
        )

    # if password is correct, do database removal
    if not l.is_correct_password(username, password):
        return render_tools(
            mysql_error="Wrong username or password.",
            mysql_active=True,
        )
    try:
        m.create_database(username, dbname, True)
    except m.DatabaseAccessError as e:
        return render_tools(
            mysql_error=e.__cause__,
            mysql_active=True,
        )
    # Why redirect when it can display a message?
    return flask.redirect("/")


@app.route("/resetpw", methods=["POST"])
@l.protected_page
def resetpw():
    """
    Route: resetpw
        This route must be accessed via post. It is used to reset the user's
        MySQL account password.
        This can only be reached if you are logged in.
    """
    app.logger.debug(f"Form: {flask.request.form}")
    username = flask.request.form["username"]
    password = flask.request.form["password"]

    # make sure each value is non-empty
    if not all([username, password]):
        return render_tools(
            mysql_error="Please specify all fields.",
            mysql_active=True,
        )

    # if password is correct, reset password
    if not l.is_correct_password(username, password):
        return render_tools(
            mysql_error="Wrong username or password.",
            mysql_active=True,
        )
    try:
        m.delete_user(username)
        new_password = m.create_user(username)
    except m.UserError as e:
        return render_tools(
            mysql_error=e.__cause__,
            mysql_active=True,
        )
    else:
        return render_tools(
            new_mysql_password=new_password,
            mysql_active=True,
        )


@app.route("/wordpressinstall")
@l.protected_page
def wordpressinstall():
    """
    Route: wordpressinstall
        This endpoint only allows a GET method.
        If a user is authenticated and accessed this endpoint, then wordpress is installed to their public_html directory.
        This endpoint is pinged via an AJAX request on the clients' side.
    """
    username = flask.session["username"]
    home_dir = "/home/users/" + username
    w.get_wordpress(home_dir, username, DEBUG)
    return username, 200


@app.route("/help", methods=["POST"])
@l.protected_page
def help():
    """
    Route: help
        This takes care of the help section, sending the data off
        to the relevant functions.
        This can only be reached if you are logged in.
    """
    email = flask.request.form['email']
    subject = flask.request.form['subject']
    message = flask.request.form['message']
    if not all([email, subject, message]):
        return render_tools(
            help_error="Please enter all fields",
            help_active=True,
        )

    sent_email = h.send_help_email(flask.session['username'], email, subject, message)

    try:
        sent_discord = h.send_help_bot(flask.session['username'], email, subject, message)
    except Exception as e:
        app.logger.error(f"Failed to send message to discord bot: {str(e)}")
        # in this case, the disocrd bot was unreachable. We log this error but
        # continue as success because the email is still sent. This fix will have
        # to remain until the Discord bot becomes more reliable.
        sent_discord = True
    if not sent_email or not sent_discord:
        return render_tools(
            help_error="There was a problem :( Please email netsoc@uccsocieties.ie instead",
            help_active=True,
        )
    # Success
    return render_tools(
        help_success=True,
        help_active=True,
    )



@app.route("/backup/<string:username>/<string:timeframe>/<string:backup_date>")
@l.protected_page
def backup(username: str, timeframe: str, backup_date: str):
    """
    Route: /backup/username/timeframe/backup_date
        This route returns the requested backup.

    :param username the server username of the user needing their backup.
    :param timeframe the timeframe of the requested backup. Can be either
        "weekly", or "monthly".
    :param backup_date the backup-date of the requested backup. Must be in the
        form YYYY-MM-DD.
    """
    # make sure the arguments are valid
    if not re.match(r"^[a-z]+$", username) or \
            not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}", backup_date) or \
                    timeframe not in ["weekly", "monthly"]:
        app.logger.debug(f"backups({username}, {timeframe}, {backup_date}): invalid arguments")
        return flask.abort(400)

    backups_base_dir = os.path.join(b.BACKUPS_DIR, username, timeframe)
    return flask.send_from_directory(backups_base_dir, backup_date + ".tgz")


@app.route("/change-shell", methods=["POST"])
@l.protected_page
def change_shell():
    """
    Route: /change-shell
        This route will change the user's shell in the LDAP server to the one
        that they request from the dropdown
    """
    # Ensure the selected shell is in the list of allowed shells
    shell_path = SHELL_PATHS.get(flask.request.form["shell"], None)

    if shell_path is None:
        # Return an error message
        return render_tools(
            shells_active=True,
            shells_error="Invalid shell selected",
        )

    # Attempt to update the LDAP DB for the logged in user and set their loginShell value to be the path
    ldap_server = ldap3.Server(config.LDAP_HOST, get_info=ldap3.ALL)
    with ldap3.Connection(ldap_server, auto_bind=True, **config.LDAP_AUTH) as conn:
        # Find the group for the user
        username = flask.session["username"]
        groups = ["admins", "committee", "member"]
        found = False
        for group in groups:
            success = conn.search(
                search_base=f"cn={group},dc=netsoc,dc=co",
                search_filter=f"(&(uid={username}))",
            )
            if success:
                found = True
                break
        if found:
            # Now that we've found the group, we can modify the value
            success = conn.modify(
                dn=f"cn={username},cn={group},dc=netsoc,dc=co",
                changes={'loginShell': [(ldap3.MODIFY_REPLACE, [shell_path])]},
            )
            if not success:
                return render_tools(
                    shells_active=True,
                    shells_error=conn.last_error,
                )

            return render_tools(
                shells_active=True,
                shells_success=True,
            )

        # If we reach here, we didn't find the user in the LDAP (???)
        return render_tools(
            shells_active=True,
            shells_error="User could not be found to modify.",
        )


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
            show_logout_button=l.is_logged_in(),
            error="No tutorials to show",
        )
    if DEBUG:
        TUTORIALS = []
        populate_tutorials()
    return flask.render_template(
        "tutorials.html",
        show_logout_button=l.is_logged_in(),
        tutorials=TUTORIALS,
    )


@app.route("/sudo")
@l.protected_page
def sudo():
    """
    Route: /sudo
        This route will render the page for applying for sudo privilages.
    """
    return flask.render_template("sudo.html",
                                 show_logout_button=l.is_logged_in(),
                                 username=flask.session["username"])


@app.route("/completesudoapplication", methods=["POST"])
@l.protected_page
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
        h.send_sudo_request_email(username, email)
    except Exception as e:
        email_failed = True
        app.logger.error(f"Failed to send email: {str(e)}")

    try:
        h.send_help_bot(
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
            show_logout_button=l.is_logged_in(),
            caption="There was a problem :(",
            message="Please email netsoc@uccsocieties.ie instead",
        )

    return flask.render_template(
        "message.html",
        show_logout_button=l.is_logged_in(),
        caption="Success!",
        message="A confirmation email has been sent to you. We will be in touch shortly.",
    )


def populate_tutorials():
    """
    Opens the tutorials folder and parses all of the markdown tutorials
    contained within.
    """
    for tut_file in filter(lambda f: f.endswith(".md"), os.listdir(config.TUTORIAL_FOLDER)):
        with open(os.path.join(config.TUTORIAL_FOLDER, tut_file)) as f:
            tutorial = markdown.markdown(f.read())
            TUTORIALS.append(flask.Markup(tutorial))


def render_tools(**data):
    """
    Helper that ensures all necessary data is passed to tools every time it's rendered
    """
    return flask.render_template(
        "tools.html",
        show_logout_button=l.is_logged_in(),
        databases=m.list_dbs(flask.session["username"]),
        wordpress_exists=w.wordpress_exists(f"/home/users/{flask.session['username']}"),
        wordpress_link=f"http://{flask.session['username']}.netsoc.co/wordpress/wp-admin/index.php",
        weekly_backups=b.list_backups(flask.session["username"], "weekly"),
        monthly_backups=b.list_backups(flask.session["username"], "monthly"),
        username=flask.session["username"],
        login_shells=[(k, k.capitalize()) for k in config.SHELL_PATHS],
        **data,
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

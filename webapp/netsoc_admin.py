"""
This file contains the main webapp for netsoc admin.
Sets up a local server running the website. Requests should
then be proxied to this address.
"""
import backup_tools as b
import flask
import login_tools as l
import markdown
import mysql_tools as m
import os
import passwords as p
import re
import sys
import register_tools as r
from wordpress_installer.wordpress_install import get_wordpress, wordpress_exists
import help_post as h

HOST = "127.0.0.1"
PORT = "5050"
DEBUG = False
TUTORIALS = []

app = flask.Flask(__name__)
app.secret_key = p.SECRET_KEY
app.config["SESSION_REFRESH_EACH_REQUEST"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 10 # seconds


@app.route('/signinup')
def signinup():
    """
    Route: /
        This route is for the index directory.
        If the user goes to this, it will load the index.html template.
    """
    app.logger.debug("Received index page request")
    return flask.render_template("index.html")


#------------------------------Server Signup Routes------------------------------#


@app.route("/sendconfirmation", methods=["POST", "GET"])
def sendconfirmation() -> str:
    """
    Route: /sendconfirmation
        Users will be lead to this route when they submit an email for server sign up from route /
        sendconfirmation() will check whether users posted data via a form.
        It then checks that form data to make sure it's a valid UCC email.
        Sends an email with a link to validate the email holder is who is registering.
    """
    # if they got here through GET, something done fucked up
    if flask.request.method != "POST":
        app.logger.debug("sendconfirmation(): method not POST: %s"%flask.request.method)
        return flask.redirect("/signinup")

    # make sure is ucc email
    email = flask.request.form['email']
    if not re.match(r"[0-9]{9}@umail\.ucc\.ie", email):
        app.logger.debug(
            "sendconfirmation(): address %s is not a valid UCC email"%email)
        return flask.render_template("index.html",
            error_message="Must be a UCC Umail email address")

    # make sure email has not already been used to make an account
    if email not in p.EMAIL_WHITELIST and r.has_account(email):
        caption = "Sorry!"
        message = "There is an existing account with email '%s'. Please contact us if you think this is an error."%(email)
        app.logger.debug(
            "senconfirmation(): account already exists with email %s"%(email))
        return flask.render_template("message.html", caption=caption, message=message)

    # send confirmation link to ensure they own the email account
    out_email = "admin.netsoc.co" if not DEBUG else "%s:%s"%(HOST, PORT)
    confirmation_sent = r.send_confirmation_email(email, out_email)
    if not confirmation_sent:
        app.logger.debug("sendconfirmation(): confirmation email failed to send")
        return flask.render_template("index.html",
            error_message="An error occured. Please try again or contact us")

    caption = "Thank you!"
    message = "Your confirmation link has been sent to %s"%(email)
    return flask.render_template("message.html", caption=caption, message=message)


@app.route("/signup", methods=["GET"])
def signup() -> str:
    """
    Route: signup
        This is the link which they will be taken to with the confirmation email.
        It checks if the token they have used is valid and corresponds to the email.
    """
    # this check isn't vital but better safe than sorry
    if flask.request.method != "GET":
        app.logger.debug("signup(): method was not GET: %s"%flask.request.method)
        return flask.redirect("/signinup")

    # make sure they haven't forged the URI
    email = flask.request.args.get('e')
    uri = flask.request.args.get('t')
    if not r.good_token(email, uri):
        app.logger.debug("signup(): bad token %s used for email %s"%(uri, email))
        return flask.render_template("index.html",
            error_message="Your request was not valid. Please try again or contact us")

    return flask.render_template("form.html", email_address=email, token=uri)


@app.route("/completeregistration", methods=["POST", "GET"])
def completeregistration():
    """
    Route: register
        This is the route which is run by the registration form
        and should only be available through POST. It adds the
        given data to the Netsoc LDAP database.
    """
    # if they haven't gotten here through POST something has gone wrong
    if flask.request.method != "POST":
        app.logger.debug("completeregistration(): method was not POST: %s"%flask.request.method)
        return flask.redirect("/signinup")

    # make sure token is valid
    email = flask.request.form["email"]
    uri = flask.request.form["_token"]
    if not r.good_token(email, uri):
        app.logger.debug(
            "completeregistration(): invalid token %s for email %s"%(uri, email))
        return flask.render_template("index.html",
            error_message="Your token has expired or never existed. Please try again or contact us")

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
        return flask.render_template("form.html",
            email_address=email,
            token=uri,
            error_message="You must fill out all of the fields")

    user = flask.request.form["uid"]
    if r.has_username(user):
        return flask.render_template("form.html",
            email_address=email,
            token=uri,
            error_message="The requested username is not available")

    # add user to ldap db
    success, info = r.add_ldap_user(user)
    if not success:
        app.logger.debug("completeregistration(): failed to add user to LDAP: %s"%(info))
        # clean db of token so they have to start again
        r.remove_token(email)
        return flask.render_template("index.html",
            error_message="An error occured. Please try again or contact us")

    # add all info to Netsoc MySQL DB
    info["name"] = flask.request.form["name"]
    info["student_id"] = flask.request.form["student_id"]
    info["course"] = flask.request.form["course"]
    info["grad_year"] = flask.request.form["graduation_year"]
    info["email"] = email
    app.logger.debug("info: %s"%(info))
    if not r.add_netsoc_database(info):
        app.logger.debug("completeregistration(): failed to add data to mysql db")
        return flask.render_template("index.html",
            error_message="An error occured. Please try again or contact us")

    # send user's details to them
    if not r.send_details_email(email, user, info["password"]):
        app.logger.debug("completeregistration(): failed to send confirmation email")
        return flask.render_template("index.html",
            error_message="An error occured. Please try again or contact us")

    # initialise the user's home directories so they can use netsoc admin
    # without ever having to SSH into the server.
    r.initialise_directories(user, info["password"])

    # registration complete, remove their token
    r.remove_token(email)

    caption = "Thank you!"
    message = "An email has been sent with your log-in details. Please change your password as soon as you log in."
    return flask.render_template("message.html", caption=caption, message=message)


@app.route("/username", methods=["POST", "GET"])
def username():
    """
    Route: username
        This should be called by javascript in the registration form
        to test whether or not a username is already used.
    """
    if flask.request.method != "POST" or \
            "email" not in flask.request.headers or \
            "uid" not in flask.request.headers or \
            "token" not in flask.request.headers:
        return flask.abort(400)

    # check if request is legit
    email = flask.request.headers["email"]
    token = flask.request.headers["token"]
    if not r.good_token(email, token):
        return flask.abort(403)

    # check db for username
    requested_uername = flask.request.headers["uid"]
    if r.has_username(requested_uername):
        app.logger.debug("username(): uid %s is in use"%(requested_uername))
        return "Not available"
    return "Available"


#-------------------------------Login/Logout Routes-----------------------------#


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Route: login
    This route should be reached by a form sending login information to it via
    a POST request.
    """
    if flask.request.method != "POST":
        return flask.render_template("index.html", error_message="Bad request")
    if not l.is_correct_password(flask.request.form["username"], flask.request.form["password"]):
        return flask.render_template("index.html", error_message="Username or password was incorrect")
    r.initialise_directories(flask.request.form["username"], flask.request.form["password"])
    flask.session[p.LOGGED_IN_KEY] = True
    flask.session["username"] = flask.request.form["username"]
    return flask.redirect("/")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """
    Route: logout
        This route logs a user out an redirects them back to the index page.
    """
    if flask.request.method != "GET":
        return flask.redirect("/signinup")
    flask.session.pop(p.LOGGED_IN_KEY, None)
    return flask.redirect("/signinup")


#-------------------------------Server Tools Routes-----------------------------#


@app.route("/", methods=["POST", "GET"])
@l.protected_page
def tools():
    """
    Route: tools
        This is the main page where the server tools that users can avail of are
        displayed.
        Note that this should only be shown when a user is logged in.
    """
    app.logger.debug("tools(): received tools page request")
    if flask.request.method != "GET":
        app.logger.debug("tools(): bad request method")
        return flask.redirect("/signinup")

    #The wordpress variables are used by the WordPress card in the rendered HTML
    wordpress_link = "http://%s.netsoc.co/wordpress/wp-admin/index.php" % (flask.session["username"])

    return flask.render_template("tools.html",
            databases=m.list_dbs(flask.session["username"]),
            WORDPRESS_EXISTS=wordpress_exists("/home/users/" + (flask.session["username"])),
            WORDPRESS_LINK=wordpress_link,
            weekly_backups=b.list_backups(flask.session["username"], "weekly"),
            monthly_backups=b.list_backups(flask.session["username"], "monthly"),
            username=flask.session["username"])


@app.route("/createdb", methods=["POST", "GET"])
@l.protected_page
def createdb():
    """
    Route: createdb
        This route must be accessed via post. It is used to create a new
        database with the name in the request.form.
        This can only be reached if you are logged in.
    """
    if flask.request.method != "POST":
        return flask.redirect("/")

    app.logger.debug("Form: %s", flask.request.form)
    username = flask.request.form["username"]
    password = flask.request.form["password"]
    dbname = flask.request.form["dbname"]

    # make sure each value is non-empty
    if not all([username, password, dbname]):
        return flask.render_template(
                "tools.html",
                databases=m.list_dbs(flask.session["username"]),
                mysql_error="Please specify all fields",
                weekly_backups=b.list_backups(flask.session["username"], "weekly"))

    # if password is correct, create the new database
    if l.is_correct_password(username, password):
        try:
            m.create_database(username, dbname, False)
        except m.DatabaseAccessError as e:
            return flask.render_template(
                    "tools.html",
                    databases=m.list_dbs(flask.session["username"]),
                    mysql_error=e.__cause__,
                    weekly_backups=b.list_backups(flask.session["username"], "weekly"))
    else:
        return flask.render_template(
                "tools.html",
                databases=m.list_dbs(flask.session["username"]),
                weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                monthly_backups=b.list_backups(flask.session["username"], "monthly"),
                mysql_error="Wrong username or password")
    return flask.redirect("/")


@app.route("/deletedb", methods=["POST", "GET"])
@l.protected_page
def deletedb():
    """
    Route: deletedb
        This route must be accessed via post. It is used to delete the database
        contained in the request.form. This can only be reached if you are
        logged in.
    """
    if flask.request.method != "POST":
        return flask.redirect("/")

    app.logger.debug("Form: %s", flask.request.form)
    username = flask.request.form["username"]
    password = flask.request.form["password"]
    dbname = flask.request.form["dbname"]

    # make sure each value is non-empty
    if not all([username, password, dbname]):
        return flask.render_template(
                "tools.html",
                databases=m.list_dbs(flask.session["username"]),
                weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                monthly_backups=b.list_backups(flask.session["username"], "monthly"),
                mysql_error="Please specify all fields")

    # if password is correct, do database removal
    if l.is_correct_password(username, password):
        try:
            m.create_database(username, dbname, True)
        except m.DatabaseAccessError as e:
            return flask.render_template(
                    "tools.html",
                    databases=m.list_dbs(flask.session["username"]),
                    weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                    monthly_backups=b.list_backups(flask.session["username"], "monthly"),
                    mysql_error=e.__cause__)
    else:
        return flask.render_template(
                "tools.html",
                databases=m.list_dbs(flask.session["username"]),
                weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                monthly_backups=b.list_backups(flask.session["username"], "monthly"),
                mysql_error="Wrong username or password")
    return flask.redirect("/")


@app.route("/resetpw", methods=["POST", "GET"])
@l.protected_page
def resetpw():
    """
    Route: resetpw
        This route must be accessed via post. It is used to reset the user's
        MySQL account password.
        This can only be reached if you are logged in.
    """
    if flask.request.method != "POST":
        return flask.redirect("/")

    app.logger.debug("Form: %s", flask.request.form)
    username = flask.request.form["username"]
    password = flask.request.form["password"]

    # make sure each value is non-empty
    if not all([username, password]):
        return flask.render_template(
                "tools.html",
                databases=m.list_dbs(flask.session["username"]),
                weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                monthly_backups=b.list_backups(flask.session["username"], "monthly"),
                mysql_error="Please specify all fields",
                mysql_active=True)

    # if password is correct, reset password
    if l.is_correct_password(username, password):
        try:
            m.delete_user(username)
            new_password = m.create_user(username)
            return flask.render_template(
                    "tools.html",
                    databases=m.list_dbs(flask.session["username"]),
                    weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                    monthly_backups=b.list_backups(flask.session["username"], "monthly"),
                    new_mysql_password=new_password,
                    mysql_active=True)
        except m.UserError as e:
            return flask.render_template(
                    "tools.html",
                    databases=m.list_dbs(flask.session["username"]),
                    weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                    monthly_backups=b.list_backups(flask.session["username"], "monthly"),
                    mysql_error=e.__cause__,
                    mysql_active=True)
    else:
        return flask.render_template(
                "tools.html",
                databases=m.list_dbs(flask.session["username"]),
                weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                monthly_backups=b.list_backups(flask.session["username"], "monthly"),
                mysql_error="Wrong username or password",
                mysql_active=True)
    return flask.redirect("/")


@app.route("/wordpressinstall", methods=["GET"])
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
    get_wordpress(home_dir, username)
    return username, 200


@app.route("/help", methods=["POST", "GET"])
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
        return flask.render_template(
                "tools.html",
                databases=m.list_dbs(flask.session["username"]),
                help_error="Please enter all fields",
                help_active=True,
                weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                monthly_backups=b.list_backups(flask.session["username"], "monthly"),)

    sent_email = h.send_help_email(flask.session['username'], email, subject, message)

    try:
        sent_discord = h.send_help_bot(flask.session['username'], email, subject, message)
    except Exception as e:
        app.logger.error("Failed to send message to discord bot: %s", str(e))
        # in this case, the disocrd bot was unreachable. We log this error but
        # continue as success because the email is still sent. This fix will have
        # to remain until the Discord bot becomes more reliable.
        sent_discord = True
    if not sent_email or not sent_discord:
        return flask.render_template(
                "tools.html",
                databases=m.list_dbs(flask.session["username"]),
                help_error="There was a problem :( Please email netsoc@uccsocieties.ie instead",
                help_active=True,
                weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                monthly_backups=b.list_backups(flask.session["username"], "monthly"),)

    return flask.render_template(
                "tools.html",
                databases=m.list_dbs(flask.session["username"]),
                help_success=True,
                help_active=True,
                weekly_backups=b.list_backups(flask.session["username"], "weekly"),
                monthly_backups=b.list_backups(flask.session["username"], "monthly"),)


@app.route("/backup/<string:username>/<string:timeframe>/<string:backup_date>",
        methods=["POST", "GET"])
@l.protected_page
def backup(username:str, timeframe:str, backup_date:str):
    """
    Route: /backup/username/timeframe/backup_date
        This route returns the requested backup.

    :param username the server username of the user needing their backup.
    :param timeframe the timeframe of the requested backup. Can be either
        "weekly", or "monthly".
    :param backup_date the backup-date of the requested backup. Must be in the
        form YYYY-MM-DD.
    """
    if flask.request.method != "GET":
        return flask.abort(400)

    # make sure the arguments are valid
    if not re.match(r"^[a-z]+$", username) or \
            not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}", backup_date) or \
            timeframe not in ["weekly", "monthly"]:
        app.logger.debug("backups(%s, %s, %s): invalid arguments"%(
                username, timeframe, backup_date))
        return flask.abort(400)

    backups_base_dir = os.path.join(b.BACKUPS_DIR, username, timeframe)
    return flask.send_from_directory(backups_base_dir, backup_date+".tgz")


@app.route("/tutorials", methods=["POST", "GET"])
def tutorials():
    """
    Route: /tutorials
        This route will render the tutorials page. Note that the markdown tutorial
        files are read when the application starts-up.
    """
    global TUTORIALS
    if flask.request.method != "GET":
        return flask.abort(400)
    if len(TUTORIALS) == 0:
        return flask.render_template("tutorials.html", error="No tutorials to show")
    if DEBUG:
        TUTORIALS = []
        populate_tutorials()
    return flask.render_template("tutorials.html", tutorials=TUTORIALS)


def populate_tutorials():
    """
    Opens the tutorials folder and parses all of the markdown tutorials
    contained within.
    """
    for tut_file in filter(lambda f: f.endswith(".html"), os.listdir(p.TUTORIAL_FOLDER)):
        with open(os.path.join(p.TUTORIAL_FOLDER, tut_file)) as f:
            tutorial = f.read()
            TUTORIALS.append(flask.Markup(tutorial))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        DEBUG = True
        user = os.getenv("USER")
        b.BACKUPS_DIR = "/Users/%s/Documents/backups/"%(user)
        p.TUTORIAL_FOLDER = "./tutorials"

    populate_tutorials()

    app.run(
        host=HOST,
        port=int(PORT),
        threaded=True,
        debug=DEBUG,)

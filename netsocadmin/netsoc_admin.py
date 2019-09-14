"""
This file contains the main webapp for netsoc admin.
Sets up a local server running the website. Requests should
then be proxied to this address.
"""
import traceback
from uuid import uuid4

import flask

import config
import logger as nsa_logger
import login_tools
import routes
import sentry_sdk
import structlog
from sentry_sdk.integrations.flask import FlaskIntegration

# init sentry
sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    integrations=[FlaskIntegration()]
)

app = flask.Flask("netsocadmin")
app.secret_key = config.SECRET_KEY
app.config["SESSION_REFRESH_EACH_REQUEST"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 10  # seconds

nsa_logger.configure()

logger = structlog.getLogger("netsocadmin")


@app.route('/')
def index():
    """
    Route: /
        This route is for the index page. If a user is already logged in, it will
        redirect to the server tools page.
    """
    if login_tools.is_logged_in():
        return flask.redirect("/tools")
    # pylint: disable=E1101
    message = ''
    if flask.request.args.get("asdf") == "lol":
        message = "Please log in to view this page"
    elif flask.request.args.get("asdf") == "borger":
        message = "Access not granted at this time"
    return flask.render_template(
        "index.html",
        page="login",
        error_message=message
    )


@app.before_request
def before_request():
    uid = uuid4()
    flask.g.request_id = uid
    logger.info("before request", request_id=uid, request_path=flask.request.path)


@app.after_request
def after_request(response: flask.Response):
    logger.info("after request", request_id=flask.g.request_id, request_path=flask.request.path)
    return response


@app.route('/robots.txt')
def robots():
    return flask.send_file('static/robots.txt')


@app.errorhandler(404)
def not_found(e):
    logger.error(e)
    return flask.render_template("404.html"), 404


@app.errorhandler(Exception)
def internal_error(e: Exception):
    sentry_sdk.capture_exception(e)
    logger.critical('Exception on %s [%s]' % (flask.request.path, flask.request.method),
                    request_id=flask.g.request_id,
                    request_path=flask.request.path,
                    stacktrace=traceback.format_exc())
    return flask.render_template(
        "500.html",
        username=flask.session["username"] if "username" in flask.session else None,
    ), 500


# ------------------------------Server Signup Routes------------------------------#
app.add_url_rule('/completeregistration', view_func=routes.CompleteSignup.as_view('completeregistration'))
app.add_url_rule('/sendconfirmation', view_func=routes.Confirmation.as_view('sendconfirmation'))
app.add_url_rule('/signup', view_func=routes.Signup.as_view('signup'))
app.add_url_rule('/username', view_func=routes.Username.as_view('username'))
app.add_url_rule('/exception', view_func=routes.ExceptionView.as_view('exception'))

# -------------------------------Login/Logout Routes-----------------------------#
app.add_url_rule('/login', view_func=routes.Login.as_view('login'))
app.add_url_rule('/logout', view_func=routes.Logout.as_view('logout'))

# -------------------------------Server Tools Routes----------------------------- #
app.add_url_rule('/help', view_func=routes.Help.as_view('help'))
app.add_url_rule('/help', view_func=routes.HelpView.as_view('help_view'))
app.add_url_rule('/sudo', view_func=routes.Sudo.as_view('sudo'))
app.add_url_rule('/completesudoapplication', view_func=routes.CompleteSudo.as_view('completesudoapplication'))
app.add_url_rule('/tutorials', view_func=routes.Tutorials.as_view('tutorials'))

# -------------------------------Server Login Only Tools Routes----------------------------- #
app.add_url_rule(
    '/backup/<string:username>/<string:timeframe>/<string:backup_date>',
    view_func=routes.Backup.as_view('backup'),
)
app.add_url_rule('/change-shell', view_func=routes.ChangeShell.as_view('change_shell'))
app.add_url_rule('/createdb', view_func=routes.CreateDB.as_view('createdb'))
app.add_url_rule('/deletedb', view_func=routes.DeleteDB.as_view('deletedb'))
app.add_url_rule('/changepw', view_func=routes.ChangePassword.as_view('changepw'))
app.add_url_rule('/wordpressinstall', view_func=routes.WordpressInstall.as_view('wordpressinstall'))
app.add_url_rule('/tools', view_func=routes.ToolIndex.as_view('tools'))
app.add_url_rule('/tools/wordpress', view_func=routes.WordpressView.as_view('wordpress'))
app.add_url_rule('/tools/mysql', view_func=routes.MySQLView.as_view('mysql'))
app.add_url_rule('/tools/shells', view_func=routes.ShellsView.as_view('shells'))
app.add_url_rule('/tools/backups', view_func=routes.BackupsView.as_view('backups'))


if __name__ == '__main__':
    app.run(
        threaded=True,
        **config.FLASK_CONFIG,
    )

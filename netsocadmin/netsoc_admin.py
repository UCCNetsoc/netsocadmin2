"""
This file contains the main webapp for netsoc admin.
Sets up a local server running the website. Requests should
then be proxied to this address.
"""
# stdlib
import traceback
from uuid import uuid4

# lib
import flask
import sentry_sdk
import structlog as logging
from sentry_sdk.integrations.flask import FlaskIntegration

# local
import config
import logger as nsa_logger
import login_tools
import routes

# init sentry
if not config.FLASK_CONFIG['debug']:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        default_integrations=False,
        send_default_pii=True,
        environment="Development" if config.FLASK_CONFIG['debug'] else "Production",
        integrations=[FlaskIntegration()]
    )

app = flask.Flask("netsocadmin")
app.secret_key = config.SECRET_KEY
app.config["SESSION_REFRESH_EACH_REQUEST"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 10  # seconds

nsa_logger.configure()

logger = logging.getLogger("netsocadmin")


@app.route('/')
def index():
    """
    Route: /
        This route is for the index page. If a user is already logged in, it will
        redirect to the server tools page.
    """
    if login_tools.is_logged_in():
        return flask.redirect("/tools")
    message = ''
    if flask.request.args.get("e") == "e":
        message = "An error occured. Please try again or contact us"
    elif flask.request.args.get("e") == "l":
        message = "Please log in to view this page"
    elif flask.request.args.get("e") == "d":
        message = "Access not granted at this time"
    elif flask.request.args.get("e") == "i":
        message = "Username or password was incorrect"
    return flask.render_template(
        "index.html",
        page="login",
        redirect=flask.request.args.get("r"),
        error_message=message
    )


@app.before_request
def before_request():
    uid = str(uuid4())
    flask.g.request_id = uid
    with sentry_sdk.configure_scope() as scope:
        if "username" in flask.session:
            scope.user = {
                "username": flask.session["username"],
                "admin": flask.session["admin"],
            }
        scope.set_extra("request_id", uid)
    """ logger.info(
        "incoming request",
        request_id=uid,
        request_path=flask.request.path,
        user_agent=flask.request.user_agent,
        http_referrer=flask.request.referrer,
        ip_address=flask.request.remote_addr,
    ) """


@app.after_request
def after_request(response: flask.Response):
    meta = {}
    if "username" in flask.session:
        meta["username"] = flask.session["username"]
    logger.info(
        "request finished",
        user_agent=flask.request.user_agent,
        http_referrer=flask.request.referrer,
        ip_address=flask.request.remote_addr,
        status_code=response.status_code,
        **meta,
    )
    return response


@app.route('/robots.txt')
def robots():
    return flask.send_file('static/robots.txt')


@app.errorhandler(404)
def not_found(e):
    logger.warn(e)
    return flask.render_template(
        "404.html",
        username=flask.session["username"] if "username" in flask.session else None,
    ), 404


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
app.add_url_rule('/forgot', view_func=routes.Forgot.as_view('forgot'))
app.add_url_rule('/resetpassword', view_func=routes.ResetPassword.as_view('resetpassword'))
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
app.add_url_rule('/changedbpw', view_func=routes.ChangeMySQLPassword.as_view('changedbpw'))
app.add_url_rule('/changeaccountpw', view_func=routes.ChangeAccountPassword.as_view('changeaccountpw'))
app.add_url_rule('/wordpressinstall', view_func=routes.WordpressInstall.as_view('wordpressinstall'))
app.add_url_rule('/tools', view_func=routes.ToolIndex.as_view('tools'))
app.add_url_rule('/tools/wordpress', view_func=routes.WordpressView.as_view('wordpress'))
app.add_url_rule('/tools/mysql', view_func=routes.MySQLView.as_view('mysql'))
app.add_url_rule('/tools/account', view_func=routes.AccountView.as_view('account'))
app.add_url_rule('/tools/shells', view_func=routes.ShellsView.as_view('shells'))
app.add_url_rule('/tools/backups', view_func=routes.BackupsView.as_view('backups'))

logger.info("netsocadmin has been started")

if __name__ == '__main__':
    app.run(
        threaded=True,
        **config.FLASK_CONFIG,
    )

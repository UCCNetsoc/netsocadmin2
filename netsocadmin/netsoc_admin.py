"""
This file contains the main webapp for netsoc admin.
Sets up a local server running the website. Requests should
then be proxied to this address.
"""
import config
import flask
import login_tools
import routes
import logging

app = flask.Flask("netsocadmin")
app.secret_key = config.SECRET_KEY
app.config["SESSION_REFRESH_EACH_REQUEST"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 10  # seconds
app.logger.setLevel(logging.DEBUG)


@app.route('/')
def index():
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
app.add_url_rule('/completeregistration', view_func=routes.Confirmation.as_view('completeregistration'))
app.add_url_rule('/sendconfirmation', view_func=routes.Confirmation.as_view('sendconfirmation'))
app.add_url_rule('/signup', view_func=routes.Signup.as_view('signup'))
app.add_url_rule('/username', view_func=routes.Username.as_view('username'))


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
    app.run(
        threaded=True,
        **config.FLASK_CONFIG,
    )

# lib
import flask
import structlog as logging
from flask.views import View

# local
import config
import login_tools
import register_tools

__all__ = [
    "Login",
    "Logout",
]


class Login(View):
    """
    Route: login
    This route should be reached by a form sending login information to it via a POST request.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.login")
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]

    def dispatch_request(self) -> str:
        try:
            user = flask.request.form["username"].lower()
            # Validate the login request
            login_user = login_tools.LoginUser(user, flask.request.form["password"])
            if not login_tools.is_correct_password(login_user):
                return flask.render_template(
                    "index.html",
                    page="login",
                    error_message="Username or password was incorrect",
                )
            # Initialise the user's directory if running on leela
            if not config.FLASK_CONFIG["debug"]:
                register_tools.initialise_directories(user, flask.request.form["password"])
            # Set the session info to reflect that the user is logged in and redirect back to /
            flask.session[config.LOGGED_IN_KEY] = True
            flask.session["username"] = user
            flask.session["admin"] = login_user.is_admin()
            self.logger.info(f"{flask.session['username']} logged in")
        except login_tools.UserNotInLDAPException:
            return flask.render_template(
                "index.html",
                page="login",
                error_message="Username or password was incorrect"
            )
        return flask.redirect("/")


class Logout(View):
    """
    Route: logout
        This route logs a user out an redirects them back to the index page.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.logout")

    methods = ["GET"]

    def dispatch_request(self):
        # Remove the keys in the session that reflect the user
        flask.session.pop(config.LOGGED_IN_KEY, None)
        if flask.session.get("username"):
            self.logger.info(f"{flask.session['username']} logged out")
            flask.session.pop("username", "")
        return flask.redirect("/")

# stdlib
import logging
# lib
import flask
# local
import config
import login_tools
import register_tools


__all__ = [
    "Login",
    "Logout",
]


class Login(flask.views.View):
    """
    Route: login
    This route should be reached by a form sending login information to it via a POST request.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.login")
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]

    def dispatch_request(self):
        self.logger.debug("Received request")
        # Validate the login request
        if not login_tools.is_correct_password(flask.request.form["username"], flask.request.form["password"]):
            return flask.render_template(
                "index.html",
                error_message="Username or password was incorrect",
            )
        # Initialise the user's directory if running on leela
        if not config.FLASK_CONFIG["debug"]:
            register_tools.initialise_directories(flask.request.form["username"], flask.request.form["password"])
        # Set the session info to reflect that the user is logged in and redirect back to /
        flask.session[config.LOGGED_IN_KEY] = True
        flask.session["username"] = flask.request.form["username"]
        return flask.redirect("/")


class Logout(flask.views.View):
    """
    Route: logout
        This route logs a user out an redirects them back to the index page.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.logout")

    def dispatch_reqests(self):
        self.logger.debug("Received request")
        # Remove the keys in the session that reflect the user
        flask.session.pop(config.LOGGED_IN_KEY, None)
        flask.session.pop("username", "")
        return flask.redirect("/")

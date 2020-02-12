# stdlib
from typing import Tuple

# lib
import flask
import structlog as logging

# local
import login_tools
import register_tools

from .index import ProtectedToolView


class AccountView(ProtectedToolView):
    template_file = "account.html"

    page_title = "Manage Account"

    active = "account"

    logger = logging.getLogger("netsocadmin.account")

    def dispatch_request(self) -> str:
        return self.render()


class AbstractAccountView(AccountView):
    """
    Extend the ProtectedToolView with methods that help abstract some of the work out of the account related views
    """
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]

    def validate(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Given a username and password validate them.
            - Ensure the fields all have value
            - Ensure the username / password combo is correct
        :param username: The username to be validated
        :param password: The password to be validated
        """
        # Check that all passed fields have value
        fields = [username, password]
        if not all(fields):
            return False, "Please specify all fields."
        # Check if correct username supplied
        if not login_tools.is_user_logged_in(username):
            return False, "Please enter your own username"
        # Check that the username / password combination is correct
        login_user = login_tools.LoginUser(username, password)
        if not login_tools.is_correct_password(login_user):
            return False, f"Wrong username or password for user {username}."
        # We good
        return True, ""


class ChangeAccountPassword(AbstractAccountView):
    """
    Route: changeaccountpw
        This route must be accessed via post. It is used to change the user's
        server password.
        This can only be reached if you are logged in.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.changeaccountpw")

    def dispatch_request(self) -> str:
        self.logger.info(f"form: {flask.request.form}")
        # Get the fields necessary
        username = flask.request.form.get("username", "")
        password = flask.request.form.get("password", "")
        new_password = flask.request.form.get("new-password", "")
        # Check that all fields are valid
        valid, msg = self.validate(username, password)
        if not valid:
            self.logger.error(f"invalid username and password: {msg}")
            return self.render(account_pass_error=msg, account_active=True)
        register_tools.update_password(username, new_password)
        self.logger.info(f"successfully changed password for {username}")
        return self.render(success=True, account_active=True)

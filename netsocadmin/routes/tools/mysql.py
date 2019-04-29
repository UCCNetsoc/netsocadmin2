import logging
from typing import Tuple, Union

import flask

import login_tools
import mysql

from .index import ProtectedToolView


class MySQLView(ProtectedToolView):
    template_file = "mysql.html"

    page_title = "Manage MySQL"
    
    active = "mysql"

    def render(self, **data: Union[str, bool]) -> str:
        return super().render(
            databases=mysql.list_dbs(flask.session["username"]),
            limit=64 - len(flask.session["username"] + "_"),
            **data,
        )

    def dispatch_request(self):
        return self.render()


class AbstractDBView(MySQLView):
    """
    Extend the ProtectedToolView with methods that help abstract some of the work out of the db related views
    """
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]

    def validate(self, username: str, password: str, dbname: str = None) -> Tuple[bool, str]:
        """
        Given a username and password, as well as an optional dbname, validate them.
            - Ensure the fields all have value (if dbname is not None check that too)
            - Ensure the username / password combo is correct
        :param username: The username to be validated
        :param password: The password to be validated
        :param dbname: The dbname to be validated (optional)
        """
        # Check that all passed fields have value (ignore dbname if it is None)
        if dbname is None:
            fields = [username, password]
        else:
            fields = [username, password, dbname]
        if not all(fields):
            return False, "Please specify all fields."
        # Check that the username / password combination is correct
        if not login_tools.is_correct_password(username, password):
            return False, f"Wrong username or password for user {username}."
        if dbname is not None and len(flask.session["username"] + "_" + dbname) > 64:
            return False, "Database name too long"
        # We good
        return True, ""


class CreateDB(AbstractDBView):
    """
    Route: createdb
        This route must be accessed via post. It is used to create a new
        database with the name in the request.form.
        This can only be reached if you are logged in.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.createdb")

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        self.logger.debug(f"Form: {flask.request.form}")
        # Get the fields necessary
        username = flask.request.form.get("username", "")
        password = flask.request.form.get("password", "")
        dbname = flask.request.form.get("dbname", "")
        # Check that all fields are valid
        valid, msg = self.validate(username, password, dbname)
        if not valid:
            self.logger.error(f"Invalid create DB request: {msg}")
            return self.render(mysql_create_error=msg, mysql_delete_error="", mysql_active=True)
        # Try to create the database
        try:
            mysql.create_database(username, dbname, False)
        except mysql.DatabaseAccessError as e:
            self.logger.error(f"Database error {e.__cause__}")
            return self.render(mysql_create_error="e.__cause__", mysql_delete_error="", mysql_active=True)
        # Success (probably should do more than just redirect to / ...)
        self.logger.debug(f"Successfully created database for {username} named {dbname}")
        return flask.redirect("/tools/mysql")


class DeleteDB(AbstractDBView):
    """
    Route: deletedb
        This route must be accessed via post. It is used to delete the database
        contained in the request.form. This can only be reached if you are
        logged in.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.deletedb")

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        self.logger.debug(f"Form: {flask.request.form}")
        # Get the fields necessary
        username = flask.request.form.get("username", "")
        password = flask.request.form.get("password", "")
        dbname = flask.request.form.get("dbname", "")
        # Check that all fields are valid
        valid, msg = self.validate(username, password, dbname)
        if not valid:
            self.logger.error(f"Invalid username and password: {msg}")
            return self.render(mysql_delete_error=msg, mysql_create_error="", mysql_active=True)
        # Try to create the database
        try:
            mysql.create_database(username, dbname, True)
        except mysql.DatabaseAccessError as e:
            self.logger.error(f"Database error {e.__cause__}")
            return self.render(mysql_delete_error=e.__cause__, mysql_create_error="", mysql_active=True)
        # Success (probably should do more than just redirect to / ...)
        return flask.redirect("/tools/mysql")


class ResetPassword(AbstractDBView):
    """
    Route: resetpw
        This route must be accessed via post. It is used to reset the user's
        MySQL account password.
        This can only be reached if you are logged in.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.resetpw")

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        self.logger.debug(f"Form: {flask.request.form}")
        # Get the fields necessary
        username = flask.request.form.get("username", "")
        password = flask.request.form.get("password", "")
        # Check that all fields are valid
        valid, msg = self.validate(username, password)
        if not valid:
            self.logger.error(f"Invalid username and password: {msg}")
            return self.render(mysql_pass_error=msg, mysql_active=True)
        mysql.delete_user(username)
        new_password = mysql.create_user(username)
        self.logger.debug("Successfully changed password")
        return self.render(new_mysql_password=new_password, mysql_active=True)

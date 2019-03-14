"""File containing classes that represent all of the routes that are related to the `tools.html` template"""
# python
import ldap3
import logging
import os
import re
from typing import Tuple, Optional, Union
# lib
import flask
from flask.views import View
# local
import backup_tools
import config
import mysql
import help_post
import login_tools
import wordpress_install


__all__ = [
    "Backup",
    "ChangeShell",
    "CreateDB",
    "DeleteDB",
    "Help",
    "ResetPassword",
    "ToolIndex",
    "WordpressInstall",
]


# Super classes
class ToolView(View):
    """
    Super class for all of the routes that render the tools template
    """
    # Decorate all subclasses with the following decorators
    decorators = [login_tools.protected_page]
    # Logger instance (should be defined in each sub class to use correct naming)
    logger: Optional[logging.Logger] = None
    # Specify which method(s) are allowed to be used to access the route
    methods = ["GET"]

    def render(self, **data: Union[str, bool]) -> str:
        """
        Method to render the tools template with the default vars and any extra data as decided by the route
        :param data: Some extra data to be passed to the template
        """
        return flask.render_template(
            "tools.html",
            databases=mysql.list_dbs(flask.session["username"]),
            login_shells=[(k, k.capitalize()) for k in config.SHELL_PATHS],
            monthly_backups=backup_tools.list_backups(flask.session["username"], "monthly"),
            show_logout_button=login_tools.is_logged_in(),
            username=flask.session["username"],
            weekly_backups=backup_tools.list_backups(flask.session["username"], "weekly"),
            wordpress_exists=wordpress_install.wordpress_exists(f"/home/users/{flask.session['username']}"),
            wordpress_link=f"http://{flask.session['username']}.netsoc.co/wordpress/wp-admin/index.php",
            **data,
        )


class DBView(ToolView):
    """
    Extend the ToolView with methods that help abstract some of the work out of the db related views
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
        # We good
        return True, ""


# Actual View Classes
class Backup(ToolView):
    """
    Route: /backup/{username}/{timeframe}/{backup_date}
        This route returns the requested backup.

    :param username: The server username of the user needing their backup.
    :param timeframe: The timeframe of the requested backup.
        Can be either "weekly", or "monthly".
    :param backup_date: the date of the requested backup.
        Must be in the form YYYY-MM-DD.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.backup")

    def dispatch_request(self, username: str, timeframe: str, backup_date: str) -> str:
        self.logger.debug("Received request")
        # Validate the parameters
        if (not re.match(r"^[a-z0-9-_]+[a-z0-9]$", username) or not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}", backup_date) or
                timeframe not in ["weekly", "monthly"]):
            self.logger.debug(f"Received invalid arguments: {username}, {timeframe}, {backup_date}")
            return flask.abort(400)
        # Retrieve the backup and send it to the user
        backups_base_dir = os.path.join(config.BACKUPS_DIR, username, timeframe)
        return flask.send_from_directory(backups_base_dir, f"{backup_date}.tgz")


class ChangeShell(ToolView):
    """
    Route: /change-shell
        This route will change the user's shell in the LDAP server to the one
        that they request from the dropdown
    """
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]
    # Logger instance
    logger = logging.getLogger("netsocadmin.change-shell")

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        # Ensure the selected shell is in the list of allowed shells
        shell_path = config.SHELL_PATHS.get(flask.request.form.get("shell", ""), None)
        if shell_path is None:
            return self.render(shells_error="Invalid shell selection!", shells_active=True)
        # Attempt to update LDAP for the logged in user to update their loginShell
        ldap_server = ldap3.Server(config.LDAP_HOST, get_info=ldap3.ALL)
        with ldap3.Connection(ldap_server, auto_bind=True, **config.LDAP_AUTH) as conn:
            # Find the user
            username = flask.session["username"]
            # Put member first since it's the most probable
            groups = ["member", "admins", "committee"]
            found = False
            for group in groups:
                success = conn.search(
                    search_base=f"cn={group},dc=netsoc,dc=co",
                    search_filter=f"(&(uid={username}))",
                )
                if success:
                    found = True
                    break
            if not found:
                self.logger.debug(f"User {username} not found. Could not update shell")
                return self.render(shells_error="Could not find your user to update it", shells_active=True)

            # Modify the user now
            success = conn.modify(
                dn=f"cn={username},cn={group},dc=netsoc,dc=co",
                changes={"loginShell": (ldap3.MODIFY_REPLACE, [shell_path])},
            )
            if not success:
                self.logger.error("Error changing shell")
                return self.render(shells_error=conn.last_error, shells_active=True)
            self.logger.debug("Shell changed successfully")
            return self.render(shells_success=True, shells_active=True)


class CreateDB(DBView):
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
            self.logger.error(f"Invalid username and password: {msg}")
            return self.render(mysql_error=msg, mysql_active=True)
        # Try to create the database
        try:
            mysql.create_database(username, dbname, False)
        except mysql.DatabaseAccessError as e:
            self.logger.error(f"Database error {e.__cause__}")
            return self.render(mysql_error=e.__cause__, mysql_active=True)
        # Success (probably should do more than just redirect to / ...)
        self.logger.debug(f"Successfully created database for {username} named {dbname}")
        return flask.redirect("/")


class DeleteDB(DBView):
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
            return self.render(mysql_error=msg, mysql_active=True)
        # Try to create the database
        try:
            mysql.create_database(username, dbname, True)
        except mysql.DatabaseAccessError as e:
            self.logger.error(f"Database error {e.__cause__}")
            return self.render(mysql_error=e.__cause__, mysql_active=True)
        # Success (probably should do more than just redirect to / ...)
        return flask.redirect("/")


class Help(ToolView):
    """
    Route: help
        This takes care of the help section, sending the data off
        to the relevant functions.
        This can only be reached if you are logged in.
    """
    # Specify the method(s) that are allowed to be used to reach this view
    methods = ["POST"]
    # Logger instance
    logger = logging.getLogger("netsocadmin.help")

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        email = flask.request.form.get("email", "")
        subject = flask.request.form.get("subject", "")
        message = flask.request.form.get("message", "")
        # Ensure all fields are populated
        if not all([email, subject, message]):
            self.logger.debug("Not all fields specified")
            return self.render(help_error="Please specify all fields", help_active=True)
        # Send the email
        sent_email = help_post.send_help_email(flask.session["username"], email, subject, message)
        # Try and send to Discord bot
        try:
            sent_discord = help_post.send_help_webhook(flask.session["username"], email, subject, message)
        except Exception as e:
            self.logger.error(f"Failed to send message to discord bot: {str(e)}")
            # in this case, the Discord bot was unreachable. We log this error but
            # continue as success because the email may still be sent. This fix will have
            # to remain until the Discord bot becomes more reliable.
            sent_discord = True
        # Check that at least one form of communication was sent
        if not sent_email and not sent_discord:
            # If not, report an error to the user
            self.logger.error(f"Unable to send email and unable to send to discord bot: {message}")
            return self.render(
                help_error="There was a problem :( Please email netsoc@uccsocieties.ie instead",
                help_active=True,
            )
        # Otherwise when things are okay, report back stating so
        self.logger.debug("Successfully sent help email or contacted discord bot")
        return self.render(help_success=True, help_active=True)


class ResetPassword(DBView):
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
            return self.render(mysql_error=msg, mysql_active=True)
        # Try to create the database
        try:
            mysql.delete_user(username)
            new_password = mysql.create_user(username)
        except mysql.DatabaseAccessError as e:
            self.logger.error(f"Database error {e.__cause__}")
            return self.render(mysql_error=e.__cause__, mysql_active=True)
        else:
            self.logger.debug("Successfully changed password")
            return self.render(new_mysql_password=new_password, mysql_active=True)


class ToolIndex(ToolView):
    """
    Route: tools
        This is the main page where the server tools that users can avail of are
        displayed.
        Note that this should only be shown when a user is logged in.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.tools")

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        return self.render()


class WordpressInstall(ToolView):
    """
    Route: wordpressinstall
        This endpoint only allows a GET method.
        If a user is authenticated and accessed this endpoint, then wordpress is installed to their public_html
        directory.
        This endpoint is pinged via an AJAX request on the clients' side.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.wordpressinstall")

    def dispatch_request(self) -> Tuple[str, int]:
        self.logger.debug("Received request")
        username = flask.session["username"]
        try:
            wordpress_install.get_wordpress(
                f"/home/users/{username}",
                username,
                config.FLASK_CONFIG["debug"]
            )
            self.logger.error(f"Wordpress install successful for {username}")
            return username, 200
        except Exception as e:
            self.logger.error(f"Wordpress install failed for {username} {e}")
            return username, 500

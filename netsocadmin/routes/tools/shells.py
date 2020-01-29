# lib
import flask
import ldap3
import structlog as logging

# local
import config

from .index import ProtectedToolView, ProtectedView


class ShellsView(ProtectedToolView):
    template_file = "shells.html"

    page_title = "Login Shell"

    active = "shells"

    def dispatch_request(self, **data):
        ldap_server = ldap3.Server(config.LDAP_HOST, get_info=ldap3.ALL)
        with ldap3.Connection(ldap_server, auto_bind=True, receive_timeout=5, **config.LDAP_AUTH) as conn:
            username = ldap3.utils.conv.escape_filter_chars(flask.session["username"])
            success = conn.search(
                search_base="dc=netsoc,dc=co",
                search_filter=f"(&(objectClass=account)(uid={username}))",
                attributes=["loginShell"],
            )
            if not success or len(conn.entries) != 1:
                shell = "Bash"
            else:
                shell = conn.entries[0]["loginShell"].value
        inverse_shells = {v: k for k, v in config.SHELL_PATHS.items()}
        return self.render(
            login_shells=[(k, k.capitalize()) for k in config.SHELL_PATHS],
            curr_shell=inverse_shells[shell].capitalize(),
            **data,
        )


class ChangeShell(ProtectedView):
    """
    Route: /change-shell
        This route will change the user's shell in the LDAP server to the one
        that they request from the dropdown
    """
    # Specify which method(s) are allowed to be used to access the route
    methods = ["POST"]
    # Logger instance
    logger = logging.getLogger("netsocadmin.change-shell")

    def dispatch_request(self):
        # Ensure the selected shell is in the list of allowed shells
        shell_path = config.SHELL_PATHS.get(flask.request.args.get("shell", ""), None)
        if shell_path is None:
            return "Invalid shell received", 400
        # Attempt to update LDAP for the logged in user to update their loginShell
        ldap_server = ldap3.Server(config.LDAP_HOST, get_info=ldap3.ALL)
        with ldap3.Connection(ldap_server, auto_bind=True, receive_timeout=5, **config.LDAP_AUTH) as conn:
            # Find the user
            username = flask.session["username"]
            # Put member first since it's the most probable
            groups = ["member", "admins", "committee"]
            found = False
            for group in groups:
                success = conn.search(
                    search_base=f"cn={group},dc=netsoc,dc=co",
                    search_filter=f"(&(objectClass=account)(uid={username}))",
                )
                if success:
                    found = True
                    break
            if not found:
                self.logger.info(f"user {username} not found. Could not update shell")
                return "Invalid user received. Please contact us for assistance", 500

            # Modify the user now
            try:
                success = conn.modify(
                    dn=f"cn={username},cn={group},dc=netsoc,dc=co",
                    changes={"loginShell": (ldap3.MODIFY_REPLACE, [shell_path])},
                )
                if not success:
                    self.logger.error(f"error changing shell for {username}: {conn.last_error}")
                    return "failed to set shell", 500
            except Exception as e:
                self.logger.error(f"error changing shell for {username}: {e}")
                return "failed to set shell", 500
            self.logger.info(f"shell changed successfully for {username} to {shell_path}")
            return "", 200

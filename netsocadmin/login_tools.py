"""
Contains functions which are used during the login and logout process.
"""
# stdlib
import crypt
import functools
import hmac
import typing

# lib
import flask
import ldap3
import structlog as logging

# local
import config

logger = logging.getLogger("netsocadmin.login")
ldap_server = ldap3.Server(config.LDAP_HOST, get_info=ldap3.ALL)


class UserNotInLDAPException(Exception):
    pass


class LoginUser:
    def __init__(self, username: str, password: str):
        self.username = ldap3.utils.conv.escape_filter_chars(username)
        self.password = password
        self.ldap_pass = None
        self.group = 422

    def populate_data(self, conn: ldap3.Connection):
        success = conn.search(
            search_base="dc=netsoc,dc=co",
            search_filter=f"(&(objectClass=account)(uid={self.username}))",
            attributes=["userPassword", "uid", "gidNumber"],
        )
        if len(conn.entries) == 0:
            raise UserNotInLDAPException(f"username {self.username} not found in LDAP")
        if not success or len(conn.entries) != 1:
            raise Exception(f"couldnt search from ldap: {conn.last_error}")
        entry = conn.entries[0]
        self.ldap_pass = entry["userPassword"].value.decode()
        self.group = entry["gidNumber"].value

    def is_pass_correct(self) -> bool:
        if self.ldap_pass.startswith("{crypt}") or self.ldap_pass.startswith("{CRYPT}"):
            # strips off the "{crypt}" prefix
            ldap_pass = self.ldap_pass[len("{crypt}"):]
        return hmac.compare_digest(crypt.crypt(self.password, ldap_pass), ldap_pass)

    def is_admin(self) -> bool:
        return self.group == 420


def admin_only_page(view_func: typing.Callable[..., None]) -> typing.Callable[..., None]:
    """
    admin_only_page is a route function decorator which will check that a user
    is an admin (group ID 420) before allowing the decorated view function to be shown. If the
    user is not an admin, it will redirect them to the index page.
    """
    @functools.wraps(view_func)
    def admin_only_view_func(*args, **kwargs):
        if flask.session["admin"]:
            return view_func(*args, **kwargs)
        return flask.redirect("/?e=d")
    return admin_only_view_func


def protected_page(view_func: typing.Callable[..., None]) -> typing.Callable[..., None]:
    """
    protected_page is a route function decorator which will check that a user
    is logged in before allowing the decorated view function to be shown. If the
    user is not logged in, it will redirect them to the index page.
    """
    @functools.wraps(view_func)
    def protected_view_func(*args, **kwargs):
        if config.LOGGED_IN_KEY not in flask.session or not flask.session[config.LOGGED_IN_KEY]:
            return flask.redirect("/?e=l&r=" + flask.request.path)
        return view_func(*args, **kwargs)
    return protected_view_func


def is_logged_in() -> bool:
    """
    Returns True if the user is currently logged in.
    """
    return config.LOGGED_IN_KEY in flask.session and flask.session[config.LOGGED_IN_KEY]


def is_admin() -> bool:
    return is_logged_in() and flask.session["admin"]


def is_user_logged_in(user: str) -> bool:
    return is_logged_in() and flask.session["username"] == user


def is_correct_password(user: LoginUser) -> bool:
    """
    is_correct_password tells you whether or not a given username + password
    combo are correct
    """
    with ldap3.Connection(ldap_server, auto_bind=True, receive_timeout=5, **config.LDAP_AUTH) as conn:
        try:
            user.populate_data(conn)
        except UserNotInLDAPException:
            logger.info("incorect username supplied",
                        user=user.username)
            return False
        if not user.is_pass_correct():
            logger.info("incorect password supplied",
                        user=user.username)
        return user.is_pass_correct()

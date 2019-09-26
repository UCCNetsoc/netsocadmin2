"""
Contains functions which are used during the login and logout process.
"""
import crypt
import functools
import hmac
import logging
import typing

import flask
import ldap3

import config

logger = logging.getLogger("netsocadmin.login")
ldap_server = ldap3.Server(config.LDAP_HOST, get_info=ldap3.ALL)


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
        if not success or len(conn.entries) != 1:
            raise Exception(f"couldnt search from ldap: {conn.last_error}")
        entry = conn.entries[0]
        self.ldap_pass = entry["userPassword"].value.decode()
        self.group = entry["gidNumber"].value

    def is_pass_correct(self) -> bool:
        if self.ldap_pass.startswith("{crypt}") or self.ldap_pass.startswith("{CRYPT}"):
            # strips off the "{crypt}" prefix
            self.ldap_pass = self.ldap_pass[len("{crypt}"):]
        return hmac.compare_digest(crypt.crypt(self.password, self.ldap_pass), self.ldap_pass)

    def is_admin(self) -> bool:
        return self.group == 420


def protected_page(view_func: typing.Callable[..., None]) -> typing.Callable[..., None]:
    """
    protected_page is a route function decorator which will check that a user
    is logged in before allowing the decorated view function to be shown. If the
    user is not logged in, it will redirect them to the index page.
    """
    @functools.wraps(view_func)
    def protected_view_func(*args, **kwargs):
        if config.LOGGED_IN_KEY not in flask.session or not flask.session[config.LOGGED_IN_KEY]:
            return flask.redirect("/?asdf=lol")
        return view_func(*args, **kwargs)
    return protected_view_func


def is_logged_in():
    """
    Returns True if the user is currently logged in.
    """
    return config.LOGGED_IN_KEY in flask.session and flask.session[config.LOGGED_IN_KEY]


def is_correct_password(user: LoginUser) -> bool:
    """
    is_correct_password tells you whether or not a given username + password
    combo are correct
    """
    logger.debug(f"checking password for '{user.username}''")
    with ldap3.Connection(ldap_server, auto_bind=True, **config.LDAP_AUTH) as conn:
        user.populate_data(conn)
        if not user.is_pass_correct():
            logger.debug(f"password incorrect for '{user.username}'")
        return user.is_pass_correct()


if __name__ == "__main__":
    user = input("username: ")
    password = input("password: ")
    correct = is_correct_password(user, password)
    print("Correct" if correct else "Incorrect")

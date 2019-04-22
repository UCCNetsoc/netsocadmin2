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


def protected_page(view_func: typing.Callable[..., None]) -> typing.Callable[..., None]:
    """
    protected_page is a route function decorator which will check that a user
    is logged in before allowing the decorated view function to be shown. If the
    user is not logged in, it will redirect them to the index page.
    """
    @functools.wraps(view_func)
    def protected_view_func(*args, **kwargs):
        if config.LOGGED_IN_KEY not in flask.session or not flask.session[config.LOGGED_IN_KEY]:
            return flask.render_template("index.html", error_message="Please log in to view this page")
        return view_func(*args, **kwargs)
    return protected_view_func


def is_logged_in():
    """
    Returns True if the user is currently logged in.
    """
    return config.LOGGED_IN_KEY in flask.session and flask.session[config.LOGGED_IN_KEY]


def is_correct_password(username: str, password: str) -> bool:
    """
    is_correct_password tells you whether or not a given password
    is the password has which is on file in the Netsoc MySQL database.
    """
    logger.info("login attempt from {username}")
    with ldap3.Connection(ldap_server, auto_bind=True, **config.LDAP_AUTH) as conn:
        username = ldap3.utils.conv.escape_filter_chars(username)
        success = conn.search(
            search_base="dc=netsoc,dc=co",
            search_filter=f"(&(objectClass=account)(uid={username}))",
            attributes=["userPassword", "uid"],
        )
        if not success or len(conn.entries) != 1:
            return False

        hashed_password = conn.entries[0]["userPassword"].value.decode()
        if hashed_password.startswith("{crypt}") or hashed_password.startswith("{CRYPT}"):
            # strips off the "{crypt}" prefix
            hashed_password = hashed_password[len("{crypt}"):]
        return hmac.compare_digest(crypt.crypt(password, hashed_password), hashed_password)


if __name__ == "__main__":
    user = input("username: ")
    password = input("password: ")
    correct = is_correct_password(user, password)
    print("Correct" if correct else "Incorrect")

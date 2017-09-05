"""
Contains functions which are used during the login and logout process.
"""
import crypt
import flask
import functools
import hmac
import ldap3
import passwords as p
import pymysql
import typing


def protected_page(view_func:typing.Callable[[], None]) -> typing.Callable[[], None]:
    """
    protected_page is a route function decorator which will check that a user
    is logged in before allowing the decorated view function to be shown. If the
    user is not logged in, it will redirect them to the index page.
    """
    @functools.wraps(view_func)
    def protected_view_func(*args, **kwargs):
        if p.LOGGED_IN_KEY not in flask.session or not flask.session[p.LOGGED_IN_KEY]:
            return flask.redirect("/signinup")
        return view_func(*args, **kwargs)
    return protected_view_func
    

def is_correct_password(username:str, password:str) -> bool:
    """
    is_correct_password tells you whether or not a given password
    is the password has which is on file in the Netsoc MySQL database.
    """
    ldap_server = ldap3.Server(p.LDAP_HOST, get_info=ldap3.ALL)
    with ldap3.Connection(
                        ldap_server,
                        user=p.LDAP_USER,
                        password=p.LDAP_KEY,
                        auto_bind=True) as conn:

        success = conn.search(
                    search_base="dc=netsoc,dc=co",
                    search_filter="(&(objectClass=account)(uid=%s))"%(
                            ldap3.utils.conv.escape_filter_chars(username)),
                    attributes=["userPassword", "uid"],)
        if not success or len(conn.entries) != 1:
            return False

        hashed_password = conn.entries[0]["userPassword"].value.decode()
        if hashed_password.startswith("{crypt}"):
            # strips off the "{crypt}" prefix
            hashed_password = hashed_password[len("{crypt}"):]
        return hmac.compare_digest(
            crypt.crypt(password, hashed_password), hashed_password)


if __name__ == "__main__":
    user = input("username: ")
    password = input("password: ")
    correct = is_correct_password(user, password)
    print("Correct" if correct else "Incorrect")

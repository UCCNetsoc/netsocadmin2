"""
Contains functions which are used during the login and logout process.
"""
import crypt
import flask
import functools
import hmac
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
    def protected_view_func():
        if p.LOGGED_IN_KEY not in flask.session or not flask.session[p.LOGGED_IN_KEY]:
            return flask.redirect("/signinup")
        return view_func()
    return protected_view_func
    

def is_correct_password(username:str, password:str) -> bool:
    """
    is_correct_password tells you whether or not a given password
    is the password has which is on file in the Netsoc MySQL database.
    """
    conn = pymysql.connect(
        host=p.SQL_HOST,
        user=p.SQL_USER,
        password=p.SQL_PASS,
        db=p.SQL_DB,)
    with conn.cursor() as c:
        # get the user's on-file hashed password
        c.execute("SELECT password FROM users WHERE uid=%s;", username)
        row = c.fetchone()
        if not row:
            return False

        hashed_password = row[0]
        if hashed_password.startswith("{crypt}"):
            # strips off the "{crypt}" prefix
            hashed_password = hashed_password[len("{crypt}"):]
        return hmac.compare_digest(
            crypt.crypt(password, hashed_password), hashed_password)
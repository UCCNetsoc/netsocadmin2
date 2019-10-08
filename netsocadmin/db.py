"""
Execute this file in order to reset the database file.

Import this file into a python interpreter and call
print_db() in order to examine the contents of the DB.
"""
# lib
import sqlite3

# local
import config

RESET = "DROP TABLE IF EXISTS uris"
CREATE = "CREATE TABLE uris(email TEXT, uri INT)"


def print_db():
    """
    This prints the currently stored email address, token pairs
    which are currently in the database. Intended for use
    within an interactive shell.
    """
    conn, c = None, None
    try:
        conn = sqlite3.connect(config.TOKEN_DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM uris")
        row_pattern = "%64s | %-64s"
        print(row_pattern % ("email", "uri"))
        for row in c.fetchall():
            print(row_pattern % (row[0], row[1]))
    finally:
        if c:
            c.close()
        if conn:
            conn.close()


def reset_db() -> object:
    """
    Resets the database to being empty.
    """
    conn = sqlite3.connect(config.TOKEN_DB_NAME)
    c = conn.cursor()
    c.execute(RESET)
    c.execute(CREATE)


if __name__ == "__main__":
    reset_db()

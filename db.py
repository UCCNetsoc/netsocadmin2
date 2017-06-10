import sqlite3
import passwords as p

RESET = "DROP TABLE IF EXISTS uris"
CREATE = "CREATE TABLE uris(email TEXT, uri INT)"

def print_db():
    conn, c, uri = None, None, None
    try:
        conn = sqlite3.connect(p.DBNAME)
        c = conn.cursor()
        c.execute("SELECT * FROM uris")
        row_pattern = "%64s | %-64s"
        print(row_pattern%("email", "uri"))
        for row in c.fetchall():
            print(row_pattern%(row[0], row[1]))
    finally:
        if c:
            c.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    conn = sqlite3.connect(p.DBNAME)
    c = conn.cursor()
    c.execute(RESET)
    c.execute(CREATE)

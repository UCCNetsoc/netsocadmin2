#!/usr/bin/python3
import argparse
import os
import passwords as p
import pymysql
import pwd
import random
import re
import string
from typing import List

class DatabaseAccessError(Exception):
    """
    DatabaseAccessError should be raised when a DB related operation fails.
    """
    pass
    

class BadUsernameError(Exception):
    """
    BadUsernameError should be raised when an operation fails due to a bad
    username being user.
    """
    pass


class UserError(Exception):
    """
    UserError should be raised when a user related operation fails.
    """
    pass


def _mysql_connection(username:str=p.SQL_USER, password:str=p.SQL_PASS) -> pymysql.connections.Connection:
    """
    _db_connection is a helper method which supplies a connection
    to the MySQL DB logged in as passwords.SQL_USER.

    :returns pymysql.connections.Connection
    """
    return pymysql.connect(
        host=p.SQL_HOST,
        user=username,
        password=password,
        cursorclass=pymysql.cursors.DictCursor)


def list_dbs(user:str) -> List[str]:
    """
    list_dbs lists all of the dbs partaining to "user".

    :returns list of database names as strings or None if the query was
        unsuccesful.
    :raises DatabaseAccessError if the operation fails.
    """
    databases = None
    try:
        con = _mysql_connection()
        with con.cursor() as cur:
            sql = "SHOW DATABASES;"
            cur.execute(sql)
            is_user_db = lambda dbname: dbname.startswith("%s_"%(user))
            databases = list(
                filter(is_user_db, map(
                    lambda row: row["Database"], cur.fetchall())))
    except Exception as e:
        raise DatabaseAccessError("failed to list databases for user '%s'"%(user)) from e
    finally:
        con.close()
    return databases


def create_user(username:str) -> str:
    """
    create_user adds a new user to the MySQL DBMS if and only if
    a user of that name does not already exist.
    
    :param username the requested username to create.
    :raises UserError if the operation fails.
    :returns string the generated password for the new user
    """
    # make sure username is valid
    if not re.match(r"^[a-zA-Z0-9]+$", username):
        raise BadUsernameError("invalid username '%s', must be lowercase letters only"%(username))
    try:
        con = _mysql_connection()
        with con.cursor() as cur:
            # check is username already exists
            sql = "SELECT User FROM mysql.user WHERE User=%s;"
            cur.execute(sql, username)
            if cur.rowcount:
                raise Exception("username %s already exists"%(username))
            
            # create new user
            chars = string.ascii_letters + string.digits
            password = "".join(
                random.choice(chars) for _ in range(random.randint(10, 15)))
            sql = """CREATE USER %s@'%%' IDENTIFIED BY %s;"""
            cur.execute(sql, (username, password,))
            sql = """CREATE USER %s@'localhost' IDENTIFIED BY %s;"""
            cur.execute(sql, (username, password,))

            # grant the user permissions on all databases of the form
            # "<username>_something".
            # Note: the escaping must be done in two parts here becuase
            # PyMySQL will insert quotation marks around the %s which
            # makes the pattern `'username'_%`.
            username_pattern = con.escape("%s"%(username)).strip("'")
            database_pattern = username_pattern + "%%%%"
            sql = """
                GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, REFERENCES,
                INDEX, ALTER, EXECUTE, CREATE ROUTINE, ALTER ROUTINE 
                    ON `{pat}`.* TO %s@'localhost';""".format(pat=database_pattern)
            cur.execute(sql, username)
            sql = """
                GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, REFERENCES,
                INDEX, ALTER, EXECUTE, CREATE ROUTINE, ALTER ROUTINE 
                    ON `{pat}`.* TO %s@'%%';""".format(pat=database_pattern)
            cur.execute(sql, username)
            return password
    except Exception as e:
        raise UserError("failed to create the new user %s"%(username)) from e
    finally:
        con.close()


def delete_user(username:str):
    """
    delete_user removes a username from the MySQL DBMS. If the username does
    not exist, it does nothing.

    :param username the username being deleted.
    :raises UserError if the operation fails.
    """
    # make sure username is valid
    if not re.match(r"[a-z]", username):
        raise BadUsernameError("invalid username '%s', must be lowercase letters only"%(username))
    try:
        con = _mysql_connection()
        with con.cursor() as cur:
            # make sure user exists
            sql = """SELECT * FROM mysql.user WHERE user=%s"""
            cur.execute(sql, username)
            if not cur.rowcount:
                return

            # make sure user isn't an admin user (more checking should be
            # done at function call as well)
            sql = """SHOW GRANTS FOR %s@'localhost'"""
            cur.execute(sql, username)
            is_grant_all = lambda row: row["Grants for %s@localhost"%(username)].startswith("GRANT ALL")
            if any(filter(is_grant_all, cur.fetchall())):
                raise Exception("user '%s' is an admin user"%(username))
            
            sql = """DROP USER %s@'localhost';"""
            cur.execute(sql, username)
            sql = """DROP USER %s@'%%';"""
            cur.execute(sql, username)
            con.commit()
    except Exception as e:
        raise UserError("failed to delete username %s"%(username)) from e
    finally:
        con.close()


def create_database(username:str, dbname:str, delete:bool=False) -> str:
    """
    create_database creates a new database for the given user. If the delete
    argument is True, then it will delete the database specified. Note that
    for a given user-selected name, dbname, the actual database name will
    be "username_dbname". 

    :param username the username of the account which will have permissions
        on the new database.
    :param dbname the user-selected name for the database. See above for details.
    :param delete when this argument is true then the database will be deleted 
        instead of created.
    :returns the database name which can be used in actual queries to the database.
    :raises DatabaseAccessError if the operation fails
    """
    try:
        con = _mysql_connection()
        with con.cursor() as cur:
            # make sure name is legit
            user_dbname = dbname
            if not dbname.startswith("%s_"%(username)):
                user_dbname = "%s_"%(username) + user_dbname
            if not re.match(r"[a-zA-Z0-9]+\_[a-zA-Z0-9]+", user_dbname):
                raise Exception(
                    "database %s is not valid, must use digits, lower or upper letters"%(user_dbname))
            
            # make sure deleting or creating is a valid thing to do
            userdbs = list_dbs(username)
            if user_dbname in userdbs and not delete:
                raise Exception("database name %s already exists"%(user_dbname))
            elif user_dbname not in userdbs and delete:
                raise Exception("database name %s doesn't exist"%(user_dbname))

            # execute the operation
            command = "CREATE" if not delete else "DROP"
            sql ="{command} DATABASE `{name}`;".format(command=command, name=user_dbname)
            cur.execute(sql)
            return user_dbname
    except Exception as e:
        raise DatabaseAccessError("failed to create new database '%s'"%(dbname)) from e
    finally:
        con.close()


def main():
    """
    main parses the arguments which the user has provided and runs the
    correct sub-sommand.
    """
    p = argparse.ArgumentParser(
        description="Easily manage your Netsoc MySQL databases.")
    group = p.add_mutually_exclusive_group()
    group.add_argument("-c", "--createdb",
        help="Create a new database with the specified name.")
    group.add_argument("-d", "--deletedb",
        help="Delete a database with the specified name.")
    group.add_argument("-l", "--listdb",
        action="store_true",
        help="Lists all of your Netsoc MySQL Databases.")
    group.add_argument("-n", "--new",
        action="store_true",
        help="Creates a new MySQL account name for you. Any existing accounts are removed completely.")

    args = p.parse_args()
    if args.createdb:
        # This allows a user to create a database of the form "username_dbname".
        # Whatever name the user gives will therefore be prepended with their
        # username and an underscore.
        user = pwd.getpwuid(os.getuid()).pw_name
        dbname = create_database(user, args.createdb)
        print("The database '%s' has been created"%(dbname))
        exit(0)

    if args.deletedb:
        # This allows a user to delete a database one of their databases. You can
        # either provide a "user_dbname" name or a "dbname" name and it will still
        # work correctly.
        user = pwd.getpwuid(os.getuid()).pw_name
        dbname = create_database(user, args.deletedb, delete=True)
        print("The database '%s' has been deleted"%(dbname))
        exit(0)

    if args.listdb:
        # This lists all of the DBs owned by the currect user
        # Note: it is assumed that the current user's name is the same as
        # their MySQL account username. It is also assumed that all 
        # databases pertaining to this user are prefixed with "<username>_".
        # e.g: for uid "roger", their MySQL username is "roger" all of their
        # databases match "roger_*".
        user = pwd.getpwuid(os.getuid()).pw_name
        dbs = list_dbs(user)
        if dbs:
            print("Your Netsoc MySQL databases:")
            print("\n".join(dbs))
        else:
            print("You have no Netsoc MySQL Databases to show")
        exit(0)

    if args.new:
        # This makes a new MySQL account for the current user, giving them a new
        # password. Note that this doesn't remove any of their old databases
        # or tables. Security consideration: your login name is the same as your
        # MySQL account name (by design) so the account which is being reset
        # must be yours as you can't change your login name without sudo.
        user = pwd.getpwuid(os.getuid()).pw_name
        delete_user(user)
        new_password = create_user(user)
        print("Your new account details:")
        print("Username: '%s'"%user)
        print("Password: '%s'"%new_password)
        exit(0)


if __name__ == "__main__":
    main()
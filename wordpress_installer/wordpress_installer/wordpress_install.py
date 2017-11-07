from jinja2 import Environment, PackageLoader
import requests
import pymysql
import random
import string
import logging
from logging.config import fileConfig

from wordpress_installer import config
from wordpress_installer.file_download_operations import *

"""
This file contains all the functions for setting up wordpress and configuring it.
"""

fileConfig(config.package["logging_config"])
logger = logging.getLogger(__name__)

def _gen_random_password(size=10, chars=string.ascii_uppercase + string.digits):
	"""
	Generates a random 10 character password for a database user.
	"""
	return ''.join(random.choice(chars) for _ in range(size))


def create_wordpress_database(username):
	"""
	Creates a wordpress user, and database.
	Wordpress databases and users all start with wp_ (wordpress databases and users have the same name)
	Drops a user and database if either already exists.
	Creates the database, creates the user, and assigns the user privilages for the database.
	Returns the database configuration for the newly created user and database.
	"""
	logger.debug("Creating wordpress database and user for %s" % (username))

	database_connection = pymysql.connect(**config.db)
	cursor = database_connection.cursor(pymysql.cursors.DictCursor)

	db_user = 'wp_' + username

	if len(username) > 16:
		db_user = db_user[:13]
		logger.debug("Username too long, shortened to %s" % (db_user))


	def _drop_user_if_exists():
		logger.debug("Checking if %s already exists in database" % (db_user))
		query = """SELECT USER FROM mysql.user WHERE USER = '{username}';""".format(username=db_user)
		cursor.execute(query)
		database_connection.commit()
		if len(cursor.fetchall()) > 0:
			logger.debug("%s already exists in database, dropping user" % (db_user))
			query = """DROP USER '{username}';""".format(username=db_user)
			cursor.execute(query)
			database_connection.commit()


	_drop_user_if_exists()

	password = _gen_random_password()

	cursor.execute("""DROP DATABASE IF EXISTS {db_name}; CREATE DATABASE {db_name};""".format(db_name=db_user))
	database_connection.commit()
	logger.debug("Created database")


	cursor.execute("""CREATE USER '{username}' IDENTIFIED BY '{password}';""".format(username=db_user, password=password))
	database_connection.commit()
	logger.debug("Created user")


	cursor.execute("""GRANT ALL PRIVILEGES ON {db_name}.* TO '{username}'""".format(db_name=db_user, username=db_user))
	database_connection.commit()
	logger.debug("Granting privileges to user")


	new_db_conf = {
		"user" 			: db_user,
		"password" 		: password,
		"db" 			: db_user,
		"host"			: config.db["host"]
	}

	return new_db_conf

def create_wordpress_conf(user_dir, db_conf):
	"""
	Used to generate a new wordpress configuration file from a jinja2 template.
	Pulls the configuration keys from the wordpress API and injects them into the template.
	Injects the database configuration returned from create_wordpress_database into database details of the template.
	Writes the newly templated configuration file into the wordpress directory.
	"""
	logger.debug("Generating wordpress configuration")

	env = Environment(loader=PackageLoader('wordpress_installer', '/resources/templates'))
	template = env.get_template('wp-config.php.j2')     

	def get_wordpress_conf_keys():
		logger.debug("Fetching wordpress configuration")
		response = requests.get("https://api.wordpress.org/secret-key/1.1/salt/")
		return response.text

	wordpress_config = template.render(USER_DIR=user_dir,
												DB_NAME=db_conf["db"],
												DB_USER=db_conf["user"],
												DB_PASSWORD=db_conf["password"],
												DB_HOST=db_conf["host"],
												KEYS=get_wordpress_conf_keys())
	logger.debug("Wordpress configuration rendered from template, writing to file")

	with open(user_dir + "/public_html/wordpress/wp-config.php", "w") as fh:
		fh.write(wordpress_config)

def get_wordpress(user_dir, username):
	"""
	Abstracted method for general wordpress installation. 
	Installs wordpress to the public_html directory of a user, given the user's directory and username.
	Compromises of two stages: download stage, and configurations stage.
	Download:
		Downloads the latest wordpress version as a tar compressed file to the users home directory.
		Extracts files from the tar compress and moves them to the ~/<username>/public_html/wordpress
		Deletes the tar compressed wordpress install from the user's home directory.
	Configuration:
		Creates new database and user for wordpress.
		Generates a new wordpress cofiguration, and places it in the wordpress directory created in the download phase.
		Changes owner and group of wordpress directory and child files/directories to the username given, and 'member'
		relatively.
	"""

	logger.debug("Installing WordPress for %s" % (username))

	def download(user_dir):
		try:
			wordpress_latest_url = "https://wordpress.org/latest.tar.gz"
			filename = download_to(wordpress_latest_url, user_dir)
			extract_from_tar(filename, user_dir + "/public_html")
			delete_file(filename)
		except Exception as e:
			logger.warning("An issue has occured while trying to download wordpress\n" + str(e))
			raise Exception("An issue has occured while trying to download wordpress")

	def configure(user_dir, username):
		try:
			new_db_conf = create_wordpress_database(username)
			create_wordpress_conf(user_dir, new_db_conf)
			chown_dir_and_children(user_dir + "/public_html/wordpress", username)
		except Exception as e:
			logger.warning("An issue has occured while trying to configure wordpress\n" + str(e))
			raise Exception("An issue has occured while trying to configure wordpress")

	download(user_dir)
	configure(user_dir, username)
	logger.debug("Installation for %s complete" % (username))

def wordpress_exists(user_dir):
	"""
	Returns true if WordPress is installed to a user's public_html/wordpress directory.
	Checks to see if WordPress exists, by checking to see if the configuration file exists.
	"""
	return file_exists(user_dir + "/public_html/wordpress/wp-config.php")

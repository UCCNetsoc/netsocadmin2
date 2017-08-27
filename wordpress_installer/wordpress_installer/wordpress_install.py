from jinja2 import Environment, PackageLoader
import requests
import pymysql
import random
import string
import logging
from logging.config import fileConfig

from wordpress_installer import config

fileConfig(config.package["logging_config"])
logger = logging.getLogger(__name__)

def _gen_random_password(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def _db_user_exists

def create_wordpress_database(username):
	logging.debug("Creating wordpress database and user for %s" % (username))

	database_connection = pymysql.connect(**config.db)
	cursor = database_connection.cursor(pymysql.cursors.DictCursor)

	db_user = 'wp_' + username

	if len(username) > 16:

		db_user = db_user[:15]

	def _db_user_exists
	
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
	logger.debug("Generating wordpress configuration")

	env = Environment(loader=PackageLoader('wordpress_installer', '/resources/templates'))
	template = env.get_template('wp-config.php.j2')     

	def get_wordpress_conf_keys():
		logging.debug("Fetching wordpress configuration")
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

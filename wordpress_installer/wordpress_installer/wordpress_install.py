from jinja2 import Environment, FileSystemLoader, PackageLoader
import requests
from file_download_operations import download_to, extract_from_tar, delete_file
import pymysql
import config as conf
import random
import string
import logging
from logging.config import fileConfig

fileConfig('logging_config.ini')

logging.getLogger(__name__).addHandler(logging.NullHandler())

def _gen_random_password(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def create_wordpress_database(username):
	database_connection = pymysql.connect(**conf.db)
	cursor = database_connection.cursor(pymysql.cursors.DictCursor)

	db_user = 'wp_' + username

	if len(username) > 16:
		db_user = db_user[:15]

	password = _gen_random_password()

	cursor.execute("""DROP DATABASE IF EXISTS {db_name}; CREATE DATABASE {db_name};""".format(db_name=db_user))
	database_connection.commit()

	cursor.execute("""CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}';""".format(username=db_user, host=conf.db["host"], password=password))
	database_connection.commit()

	cursor.execute("""GRANT ALL PRIVILEGES ON {db_name}.* TO '{username}'@'{host}'""".format(db_name=db_user, username=db_user, host=conf.db["host"]))
	database_connection.commit()

	new_db_conf = {
		"user" 			: db_user,
		"password" 		: password,
		"db" 			: db_user,
		"host"			: conf.db["host"]
	}

	return new_db_conf

def create_wordpress_conf(user_dir, db_conf):
	env = Environment(loader=PackageLoader('wordpress_installer', 'templates'))
	template = env.get_template('wp-config.php.j2')     

	def get_wordpress_conf_keys():
		response = requests.get("https://api.wordpress.org/secret-key/1.1/salt/")
		return response.text

	output_from_parsed_template = template.render(USER_DIR=user_dir,
												DB_NAME=db_conf["db"],
												DB_USER=db_conf["user"],
												DB_PASSWORD=db_conf["password"],
												DB_HOST=db_conf["host"],
												KEYS=get_wordpress_conf_keys())

	with open(user_dir + "/public_html/wordpress/wp-config.php", "w") as fh:
		fh.write(output_from_parsed_template)

def install(user_dir, username):

	wordpress_latest_url = "https://wordpress.org/latest.tar.gz"
	filename = download_to(wordpress_latest_url, user_dir)
	extract_from_tar(filename, user_dir + "/public_html")
	delete_file(filename)

	new_db_conf = create_wordpress_database(username)

	create_wordpress_conf(user_dir, new_db_conf)


install("/home/hassassin", "hassassin")
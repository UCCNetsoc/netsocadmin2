import logging
from logging.config import fileConfig
import sys

from wordpress_installer import config

fileConfig(config.package["logging_config"])
logger = logging.getLogger(__name__)

def get_wordpress(user_dir, username):

	from wordpress_installer.file_download_operations import download_to, extract_from_tar, delete_file
	from wordpress_installer.wordpress_install import create_wordpress_database, create_wordpress_conf

	logger.debug("Installing for %s complete" % (username))

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
		except Exception as e:
			logger.warning("An issue has occured while trying to configure wordpress\n" + str(e))
			raise Exception("An issue has occured while trying to configure wordpress")

	download(user_dir)
	configure(user_dir, username)
	logger.debug("Installation for %s complete" % (username))


if __name__=="__main__":
	print("1: ", sys.argv[1])
	get_wordpress(sys.argv[1], sys.argv[2])


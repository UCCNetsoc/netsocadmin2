import wget
import subprocess
import os
import logging
from logging.config import fileConfig

from wordpress_installer import config

fileConfig(config.package["logging_config"])
logger = logging.getLogger(__name__)

def extract_from_tar(path_to_file, target_dir):
	logger.debug("extracting file %s from tar to %s" % (path_to_file, target_dir))
	split_command = ["tar", "-xzf", path_to_file, "-C", target_dir]
	completed_process = subprocess.call(split_command, stdout=subprocess.PIPE)
	
def download_to(url, path_to_dir):
	logger.debug("downloading file from %s to %s" % (url, path_to_dir))
	filename = wget.download(url, out=path_to_dir, bar=None)
	return filename

def delete_file(path_to_file):
	logger.debug("deleting %s" % (path_to_file)) 
	os.remove(path_to_file)











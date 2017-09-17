import wget
import subprocess
import os
import logging
from logging.config import fileConfig

from wordpress_installer import config

"""
This file contains all the functions that relate to file operations relating to a wordpress install.
Most of the functions carry out methods similar to linux commands, or in some cases, actually carry out linux commands
using the os library.
"""

fileConfig(config.package["logging_config"])
logger = logging.getLogger(__name__)

def extract_from_tar(path_to_file, target_dir):
	"""
	Extracts files from a tar compressed file, and places them into a target directory
	"""
	logger.debug("extracting file %s from tar to %s" % (path_to_file, target_dir))
	split_command = ["tar", "-xzf", path_to_file, "-C", target_dir]
	completed_process = subprocess.call(split_command, stdout=subprocess.PIPE)
	
def download_to(url, path_to_dir):
	"""
	Downloads a file from a given to a target directory.
	Returns the file name if the downloaded file.
	"""
	logger.debug("downloading file from %s to %s" % (url, path_to_dir))
	filename = wget.download(url, out=path_to_dir, bar=None)
	return filename

def delete_file(path_to_file):
	"""
	Deletes a file from a given file path.
	"""
	logger.debug("deleting %s" % (path_to_file)) 
	os.remove(path_to_file)

def chown_dir_and_children(path_to_dir, username):
	"""
	Changes the owner of a given directory, and its children to the given username;
	Also changes the group of the given directory, and its children to 'member'.
	"""
	logger.debug("changing owner and group of directory %s and children" % (path_to_dir)) 
	split_command = ["chown", "-R", username + ":member", path_to_dir]
	completed_process = subprocess.call(split_command, stdout=subprocess.PIPE)













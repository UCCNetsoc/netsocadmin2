import wget
import subprocess
import os
import logging
from logging.config import fileConfig

fileConfig('logging_config.ini')

logging.getLogger(__name__).addHandler(logging.NullHandler())

def extract_from_tar(path_to_file, target_dir):
	logging.debug("extracting file %s from tar to %s" % (path_to_file, target_dir))
	create_dir(target_dir)
	split_command = ["tar", "-xzvf", path_to_file, "-C", target_dir]
	completed_process = subprocess.run(split_command)

def download_to(url, path_to_dir):
	logging.debug("downloading file from %s to %s" % (url, path_to_dir))
	filename = wget.download(url, out=path_to_dir)
	return filename

def delete_file(path_to_file):
	logging.debug("deleting %s" % (path_to_file)) 
	os.remove(path_to_file)

def create_dir(dir_path):
	split_command = ["mkdir", dir_path]
	completed_process = subprocess.run(split_command)






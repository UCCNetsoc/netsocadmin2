import logging
from logging.config import fileConfig
import sys

from wordpress_installer import config
from wordpress_installer.wordpress_install import get_wordpress

"""
This is the main file of the package.
It contains a main method, which takes two arguments, user directory and username.
Uses these arguments to install wordpress into a user's public_html directory.
"""

fileConfig(config.package["logging_config"])
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    print("1: ", sys.argv[1])
    get_wordpress(sys.argv[1], sys.argv[2])

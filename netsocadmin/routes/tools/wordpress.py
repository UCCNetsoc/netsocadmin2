import logging
from typing import Tuple

import flask

import config
import wordpress_install

from .index import ProtectedToolView


class WordpressView(ProtectedToolView):
    template_file = "wordpress.html"

    page_title = "Install WordPress"

    def dispatch_request(self):
        return self.render(
            wordpress_exists=wordpress_install.wordpress_exists(f"/home/users/{flask.session['username']}"),
            wordpress_link=f"http://{flask.session['username']}.netsoc.co/wordpress/wp-admin/index.php",
        )


class WordpressInstall(ProtectedToolView):
    """
    Route: wordpressinstall
        This endpoint only allows a GET method.
        If a user is authenticated and accessed this endpoint, then wordpress is installed to their public_html
        directory.
        This endpoint is pinged via an AJAX request on the clients' side.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.wordpressinstall")

    def dispatch_request(self) -> Tuple[str, int]:
        self.logger.debug("Received request")
        username = flask.session["username"]
        try:
            wordpress_install.get_wordpress(
                f"/home/users/{username}",
                username,
                config.FLASK_CONFIG["debug"]
            )
            self.logger.error(f"Wordpress install successful for {username}")
            return username, 200
        except Exception as e:
            self.logger.error(f"Wordpress install failed for {username} {e}")
            return username, 500

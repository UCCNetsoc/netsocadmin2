# stdlib
import logging
import os
# lib
import flask
import markdown
from flask.views import View
# local
import config
import login_tools


__all__ = [
    "Tutorials",
]


class Tutorials(View):
    """
    Route: /tutorials
        This route will render the tutorials page. Note that the markdown tutorial files are read when the application
        starts-up.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.tutorials")

    def __init__(self):
        self.tutorials = []
        self.populate_tutorials()

    def render(self, error=False) -> str:
        if error:
            kw = {"error": "No tutorials to show!"}
        else:
            kw = {"tutorials": self.tutorials}
        return flask.render_template(
            "tutorials.html",
            show_logout_button=login_tools.is_logged_in(),
            **kw,
        )

    def populate_tutorials(self):
        """
        Opens the tutorials folder and parses all of the markdown tutorials contained within.
        """
        self.logger.debug("Populating tutorials")
        for file in filter(lambda f: f.endswith(".md"), os.listdir(config.TUTORIAL_FOLDER)):
            with open(os.path.join(config.TUTORIAL_FOLDER, file)) as f:
                # Render the markdown file
                content = markdown.markdown(f.read())
                # Render the content and attach it to the tutorials list
                self.tutorials.append(flask.Markup(content))

    def dispatch_request(self) -> str:
        self.logger.debug("Received request")
        # Re-populate the tutorials if we're in debug mode
        if config.FLASK_CONFIG["debug"]:
            self.tutorials = []
            self.populate_tutorials()
        # Now check if we have tutorials
        return self.render(len(self.tutorials) == 0)

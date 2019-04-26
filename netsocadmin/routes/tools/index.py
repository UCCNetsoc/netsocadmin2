"""File containing classes that represent all of the routes that are related to the `tools.html` template"""

# python
import logging
from typing import Optional, Union

# lib
import flask
from flask.views import View

# local
import login_tools


class ProtectedView(View):
    # Decorate all subclasses with the following decorators
    decorators = [login_tools.protected_page]
    # Specify which method(s) are allowed to be used to access the route
    methods = ["GET"]


# Super classes
class ToolView(ProtectedView):
    """
    Super class for all of the routes that render the tools template
    """
    # Logger instance (should be defined in each sub class to use correct naming)
    logger: Optional[logging.Logger] = None
    # What template file this view uses
    template_file: Optional[str] = None

    page_title = ""

    def render(self, **data: Union[str, bool]) -> str:
        """
        Method to render the tools template with the default vars and any extra data as decided by the route
        :param data: Some extra data to be passed to the template
        """
        return flask.render_template(
            self.template_file,
            is_logged_in=login_tools.is_logged_in(),
            username=flask.session["username"],
            page_title=self.page_title,
            **data,
        )


class ToolIndex(ToolView):
    """
    Route: tools
        This is the main page where the server tools that users can avail of are
        displayed.
        Note that this should only be shown when a user is logged in.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.tools")

    template_file = "tools.html"

    page_title = "Welcome to Netsoc Admin   "

    def dispatch_request(self) -> str:
        self.logger.debug("Received request for tools")
        return self.render()

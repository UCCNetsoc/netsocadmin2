"""File containing classes that represent all of the routes that are related to the `tools.html` template"""

# python
import structlog as logging

# lib
from flask.views import View

# local
import login_tools

from ..view import TemplateView


class ProtectedView(View):
    """
    Super class for all of the protected routes that dont render a template
    """
    # Decorate all subclasses with the following decorators
    decorators = [login_tools.protected_page]
    # Specify the default method(s) that are allowed to be used to access the route
    # This can be overriden on a per view basis
    methods = ["GET"]


class ProtectedToolView(TemplateView):
    """
    Super class for all of the protected routes that render the tools template
    """
    # Decorate all subclasses with the following decorators
    decorators = [login_tools.protected_page]
    # Specify the default method(s) that are allowed to be used to access the route
    # This can be overriden on a per view basis
    methods = ["GET"]


class ToolIndex(ProtectedToolView):
    """
    Route: tools
        This is the main page where the server tools that users can avail of are
        displayed.
        Note that this should only be shown when a user is logged in.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.tools")

    template_file = "tools.html"

    page_title = "Netsoc Admin"

    active = "home"

    def dispatch_request(self) -> str:
        return self.render()

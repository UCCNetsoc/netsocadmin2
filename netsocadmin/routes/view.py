# python
import logging
from typing import Optional, Union

# libs
import flask
from flask.views import View

# local
import login_tools


class TemplateView(View):
    # Logger instance (should be defined in each sub class to use correct naming)
    logger: Optional[logging.Logger] = None
    # What template file this view uses
    template_file: Optional[str] = None

    page_title = ""

    active = ""

    def render(self, **data: Union[str, bool]) -> str:
        """
        Method to render the tools template with the default vars and any extra data as decided by the route
        :param data: Some extra data to be passed to the template
        """
        return flask.render_template(
            self.template_file,
            is_logged_in=login_tools.is_logged_in(),
            is_admin=login_tools.is_admin(),
            username=flask.session["username"] if "username" in flask.session else None,
            page_title=self.page_title,
            active=self.active,
            **data,
        )

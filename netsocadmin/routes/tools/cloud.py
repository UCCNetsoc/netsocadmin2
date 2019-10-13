# python
import logging
from typing import Tuple, Union
# libs
import flask
# local
import login_tools
from .index import ProtectedToolView


class CloudView(ProtectedToolView):
    """
    Templete view for cloud
    """
    template_file = "cloud.html"
    page_title = "Manage VMs"
    active = "cloud"
    logger = logging.getLogger("netsocadmin.cloud")

    def render(self, **data: Union[str, bool]) -> str:
        try:
            return super().render(
                project=["my_project"],
                limit=64 - len(flask.session["username"] + "_"),
                **data,
            )
        except Exception as e:
            self.logger.error(f"error loading database view: {e}")
            return super().render(
                databases=["error fetching databases"],
                limit=64 - len(flask.session["username"] + "_"),
                **data,
            )

    def dispatch_request(self):
        return self.render()


class CloudAdminView(ProtectedToolView):
    """
    Templete view for cloud admin
    """
    template_file = "cloud_admin.html"
    page_title = "Manage VMs for ADMINS"
    active = "cloud_admin"
    logger = logging.getLogger("netsocadmin.cloud_admin")

    def render(self, **data: Union[str, bool]) -> str:
        try:
            return super().render(
                project=["my_project"],
                limit=64 - len(flask.session["username"] + "_"),
                **data,
            )
        except Exception as e:
            self.logger.error(f"error loading database view: {e}")
            return super().render(
                databases=["error fetching databases"],
                limit=64 - len(flask.session["username"] + "_"),
                **data,
            )

    def dispatch_request(self):
        return self.render()
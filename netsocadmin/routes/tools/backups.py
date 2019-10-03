import structlog as logging
import os
import re

import flask

import backup_tools
import config

from .index import ProtectedToolView


class BackupsView(ProtectedToolView):
    template_file = "backups.html"

    page_title = "Manage Backups"

    active = "backups"

    def dispatch_request(self):
        return self.render(
            monthly_backups=backup_tools.list_backups(flask.session["username"], "monthly"),
            weekly_backups=backup_tools.list_backups(flask.session["username"], "weekly"),
        )


class Backup(ProtectedToolView):
    """
    Route: /backup/{username}/{timeframe}/{backup_date}
        This route returns the requested backup.

    :param username: The server username of the user needing their backup.
    :param timeframe: The timeframe of the requested backup.
        Can be either "weekly", or "monthly".
    :param backup_date: the date of the requested backup.
        Must be in the form YYYY-MM-DD.
    """
    # Logger instance
    logger = logging.getLogger("netsocadmin.backup")

    def dispatch_request(self, username: str, timeframe: str, backup_date: str) -> str:
        # Validate the parameters
        if not re.match(config.VALID_USERNAME, username) \
            or not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}", backup_date) \
                or timeframe not in ["weekly", "monthly"]:
            return flask.abort(400)
        # Retrieve the backup and send it to the user
        backups_base_dir = os.path.join(config.BACKUPS_DIR, username, timeframe)
        return flask.send_from_directory(backups_base_dir, f"{backup_date}.tgz")

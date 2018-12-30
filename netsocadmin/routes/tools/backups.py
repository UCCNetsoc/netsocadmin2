from .index import ToolView
import logging
import re
import flask
import os
import backup_tools


class BackupsView(ToolView):
    template_file = "backups.html"

    def dispatch_request(self):
        return self.render(
            monthly_backups=backup_tools.list_backups(flask.session["username"], "monthly"),
            weekly_backups=backup_tools.list_backups(flask.session["username"], "weekly"),
        )


class Backup(ToolView):
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
        self.logger.debug("Received request")
        # Validate the parameters
        if (not re.match(r"[a-z]+$", username) or not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}", backup_date) or
                timeframe not in ["weekly", "monthly"]):
            self.logger.debug(f"Received invalid arguments: {username}, {timeframe}, {backup_date}")
            return flask.abort(400)
        # Retrieve the backup and send it to the user
        backups_base_dir = os.path.join(backup_tools.BACKUPS_DIR, username, timeframe)
        return flask.send_from_directory(backups_base_dir, f"{backup_date}.tgz")

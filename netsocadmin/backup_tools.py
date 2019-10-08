"""
This file contains funtions which are used to manage a user's backups.
"""
# stdlib
import os
import re
import typing

# local
import config


def list_backups(username: str, timeframe: str) -> typing.List[str]:
    backups_base_dir = os.path.join(config.BACKUPS_DIR, username, timeframe)
    if not os.path.exists(backups_base_dir):
        os.makedirs(backups_base_dir)
    all_backups = sorted(
        [
            b.strip(".tgz")
            for b in os.listdir(backups_base_dir)
            if re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\.tgz", b)
        ],
        reverse=True,
    )
    return all_backups

"""
This file contains funtions which are used to manage a user's backups.
"""
import os
import passwords as p
import re
import typing


BACKUPS_DIR = p.BACKUPS_DIR


def list_backups(username:str, timeframe:str) -> typing.List[str]:
    backups_base_dir = os.path.join(BACKUPS_DIR, username, timeframe)
    all_backups = [b.strip(".tgz") for b in os.listdir(backups_base_dir) if 
            re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\.tgz", b)]
    return all_backups
"""Imports from all the files in the directory and makes the imports available to other parts of the system"""
from .tools import (
    Backup,
    ChangeShell,
    CreateDB,
    DeleteDB,
    Help,
    ResetPassword,
    ToolIndex,
    WordpressInstall,
)
from .tutorials import Tutorials

__all__ = [
    # Tools routes
    'Backup',
    'ChangeShell',
    'CreateDB',
    'DeleteDB',
    'Help',
    'ResetPassword',
    'ToolIndex',
    'WordpressInstall',

    # Tutorials
    'Tutorials',
]

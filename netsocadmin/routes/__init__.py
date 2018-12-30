"""Imports from all the files in the directory and makes the imports available to other parts of the system"""
from .login import Login, Logout
from .signup import CompleteSignup, Confirmation, Signup, Username
from .sudo import CompleteSudo, Sudo
from .tools.backups import (
    BackupsView,
    Backup,
)
from .tools.shells import (
    ShellsView,
    ChangeShell,
)
from .tools.mysql import (
    MySQLView,
    DeleteDB,
    CreateDB,
    ResetPassword,
)
from .tools.wordpress import (
    WordpressView,
    WordpressInstall,
)
from .tools.help import (
    HelpView,
    Help,
)
from .tools.index import (
    ToolIndex,
)
from .tutorials import Tutorials

__all__ = [
    # Login / Logout
    "Login",
    "Logout",

    # Signup
    "CompleteSignup",
    "Confirmation",
    "Signup",
    "Username",

    # Sudo
    "CompleteSudo",
    "Sudo",

    # Tools
    "ToolIndex",
    "Backup",
    "BackupsView",
    "ChangeShell",
    "ShellsView",
    "MySQLView",
    "CreateDB",
    "DeleteDB",
    "ResetPassword",
    "Help",
    "HelpView",
    "WordpressInstall",
    "WordpressView",
    # Tutorials
    "Tutorials",
]

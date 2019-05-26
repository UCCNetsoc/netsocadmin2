"""Imports from all the files in the directory and makes the imports available to other parts of the system"""
from .login import Login, Logout
from .signup import CompleteSignup, Confirmation, Signup, Username
from .tools.backups import Backup, BackupsView
from .tools.help import Help, HelpView
from .tools.index import ToolIndex
from .tools.mysql import CreateDB, DeleteDB, MySQLView, ResetPassword
from .tools.shells import ChangeShell, ShellsView
from .tools.sudo import CompleteSudo, Sudo
from .tools.wordpress import WordpressInstall, WordpressView
from .tutorials import Tutorials
from .view import TemplateView

__all__ = [
    "TemplateView",
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

"""Imports from all the files in the directory and makes the imports available to other parts of the system"""
from .exception import ExceptionView
from .login import Login, Logout
from .signup import CompleteSignup, ResetPassword, Forgot, Confirmation, Signup, Username
from .tools.backups import Backup, BackupsView
from .tools.help import Help, HelpView
from .tools.index import ToolIndex
from .tools.mysql import ChangeMySQLPassword, CreateDB, DeleteDB, MySQLView
from .tools.account import ChangeAccountPassword, AccountView
from .tools.shells import ChangeShell, ShellsView
from .tools.sudo import CompleteSudo, Sudo
from .tools.wordpress import WordpressInstall, WordpressView
from .tutorials import Tutorials
from .view import TemplateView

__all__ = [
    "TemplateView",
    "ExceptionView",
    # Login / Logout
    "Login",
    "Logout",

    # Signup
    "CompleteSignup",
    "ResetPassword",
    "Forgot",
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
    "ChangeMySQLPassword",
    "AccountView",
    "ChangeAccountPassword",
    "Help",
    "HelpView",
    "WordpressInstall",
    "WordpressView",
    # Tutorials
    "Tutorials",
]

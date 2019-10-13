from flask.views import View

import login_tools


class ExceptionView(View):
    decorators = [login_tools.protected_page, login_tools.admin_only_page]
    methods = ["GET"]

    def dispatch_request(self):
        raise Exception("its borger time")

# lib
import flask
import pythonjsonlogger.jsonlogger
from structlog import configure as conf
from structlog import processors, stdlib, threadlocal


class JsonFormatter(pythonjsonlogger.jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(JsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        try:
            log_record['request_path'] = flask.request.path
            log_record['request_method'] = flask.request.method
            log_record['request_id'] = flask.g.request_id if not None else 'FUCK'
            log_record['ip_address'] = flask.request.headers.get("X-Real-Ip", flask.request.remote_addr)
        except RuntimeError:
            pass
        try:
            if "username" in flask.session:
                log_record["username"] = flask.session["username"]
        except RuntimeError:
            pass


def configure():
    conf(
        context_class=threadlocal.wrap_dict(dict),
        logger_factory=stdlib.LoggerFactory(),
        wrapper_class=stdlib.BoundLogger,
        processors=[
            stdlib.PositionalArgumentsFormatter(),
            processors.TimeStamper(fmt="iso"),
            processors.StackInfoRenderer(),
            processors.format_exc_info,
            processors.UnicodeDecoder(),
            stdlib.render_to_log_kwargs,
        ]
    )

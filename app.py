from datetime import date, datetime

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config, validate_runtime_config
from database.db import init_db_or_exit
from routes.auth_routes import auth_bp
from routes.task_routes import task_bp
from utils.csrf import csrf_protect


def create_app():
    validate_runtime_config()

    application = Flask(__name__)
    application.config.from_object(Config)
    application.secret_key = Config.SECRET_KEY

    if Config.TRUST_PROXY:
        application.wsgi_app = ProxyFix(
            application.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )

    application.register_blueprint(auth_bp)
    application.register_blueprint(task_bp)
    csrf_protect(application)

    @application.template_filter("format_date")
    def format_date(value):
        if isinstance(value, datetime):
            return value.strftime("%b %d")
        if isinstance(value, date):
            return value.strftime("%b %d")
        if not value:
            return ""
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").strftime("%b %d")
        except ValueError:
            return str(value)

    init_db_or_exit()
    return application


app = create_app()


if __name__ == "__main__":
    app.run(host=Config.APP_HOST, port=Config.APP_PORT, debug=Config.DEBUG)

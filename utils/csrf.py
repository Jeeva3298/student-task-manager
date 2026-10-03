import hmac
import secrets

from flask import flash, redirect, request, session, url_for

CSRF_SESSION_KEY = "csrf_token"


class CSRFError(Exception):
    pass


def get_csrf_token():
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_hex(32)
        session[CSRF_SESSION_KEY] = token
    return token


def validate_csrf():
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return
    if request.path == "/health":
        return

    expected = session.get(CSRF_SESSION_KEY)
    submitted = request.form.get("csrf_token")
    if not expected or not submitted or not hmac.compare_digest(str(expected), str(submitted)):
        raise CSRFError()


def csrf_protect(app):
    app.jinja_env.globals["csrf_token"] = get_csrf_token

    @app.before_request
    def _check_csrf():
        validate_csrf()

    @app.errorhandler(CSRFError)
    def _csrf_failed(_error):
        flash("Your session expired. Please try again.", "error")
        if session.get("user_id"):
            return redirect(url_for("task.dashboard"))
        return redirect(url_for("auth.login"))

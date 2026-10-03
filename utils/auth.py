import re
from functools import wraps

from flask import flash, g, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_task_by_id, get_user_by_id

# pbkdf2 works on macOS Python 3.9; default scrypt requires hashlib.scrypt.
PASSWORD_HASH_METHOD = "pbkdf2:sha256"
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password):
    return generate_password_hash(password, method=PASSWORD_HASH_METHOD)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def valid_email(email):
    return bool(EMAIL_PATTERN.match(email or ""))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        user = get_user_by_id(session["user_id"])
        if user is None:
            session.clear()
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        g.user = user
        return view(*args, **kwargs)

    return wrapped


def current_user():
    if getattr(g, "user", None) is not None:
        return g.user
    if "user_id" not in session:
        return None
    return get_user_by_id(session["user_id"])


def get_owned_task(task_id):
    task = get_task_by_id(task_id)
    if task is None:
        return None, "missing"
    if task["user_id"] != session["user_id"]:
        return None, "unauthorized"
    return task, None

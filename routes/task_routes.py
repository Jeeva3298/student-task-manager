from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from database.db import complete_task as complete_task_in_db
from database.db import create_task, delete_task as delete_task_in_db
from database.db import get_tasks_for_user, update_task
from utils.auth import current_user, get_owned_task, login_required

PRIORITIES = ("Low", "Medium", "High")
STATUSES = ("Pending", "Completed")

task_bp = Blueprint("task", __name__)


def validate_task_fields(title, due_date, priority):
    if not title or not due_date or not priority:
        return "Title, due date, and priority are required."
    if priority not in PRIORITIES:
        return "Select a valid priority."
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        return "Enter a valid due date."
    return None


@task_bp.route("/health")
def health():
    return jsonify({"status": "healthy"})


@task_bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    tasks = get_tasks_for_user(session["user_id"])
    total = len(tasks)
    completed = sum(1 for task in tasks if task["status"] == "Completed")
    pending = total - completed
    return render_template(
        "dashboard.html",
        user=user,
        tasks=tasks,
        total=total,
        pending=pending,
        completed=completed,
    )


@task_bp.route("/add-task", methods=["GET", "POST"])
@login_required
def add_task():
    user = current_user()
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        due_date = (request.form.get("due_date") or "").strip()
        priority = request.form.get("priority") or ""

        error = validate_task_fields(title, due_date, priority)
        if error:
            flash(error, "error")
            return render_template("add_task.html", user=user)

        create_task(session["user_id"], title, description, due_date, priority)
        flash("Task created.", "success")
        return redirect(url_for("task.dashboard"))

    return render_template("add_task.html", user=user)


@task_bp.route("/edit-task/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    user = current_user()
    task, error = get_owned_task(task_id)
    if error == "missing":
        flash("Task not found.", "error")
        return redirect(url_for("task.dashboard"))
    if error == "unauthorized":
        flash("You are not authorized to access this task.", "error")
        return redirect(url_for("task.dashboard"))

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        due_date = (request.form.get("due_date") or "").strip()
        priority = request.form.get("priority") or ""
        status = request.form.get("status") or ""

        field_error = validate_task_fields(title, due_date, priority)
        if field_error:
            flash(field_error, "error")
            return render_template("edit_task.html", user=user, task=task)

        if status not in STATUSES:
            flash("Select a valid status.", "error")
            return render_template("edit_task.html", user=user, task=task)

        update_task(
            title,
            description,
            due_date,
            priority,
            status,
            task_id,
            session["user_id"],
        )
        flash("Task updated.", "success")
        return redirect(url_for("task.dashboard"))

    return render_template("edit_task.html", user=user, task=task)


@task_bp.route("/complete-task/<int:task_id>", methods=["POST"])
@login_required
def complete_task(task_id):
    task, error = get_owned_task(task_id)
    if error == "missing":
        flash("Task not found.", "error")
        return redirect(url_for("task.dashboard"))
    if error == "unauthorized":
        flash("You are not authorized to access this task.", "error")
        return redirect(url_for("task.dashboard"))

    complete_task_in_db(task_id, session["user_id"])
    flash("Task marked as completed.", "success")
    return redirect(url_for("task.dashboard"))


@task_bp.route("/delete-task/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task, error = get_owned_task(task_id)
    if error == "missing":
        flash("Task not found.", "error")
        return redirect(url_for("task.dashboard"))
    if error == "unauthorized":
        flash("You are not authorized to access this task.", "error")
        return redirect(url_for("task.dashboard"))

    delete_task_in_db(task_id, session["user_id"])
    flash("Task deleted.", "success")
    return redirect(url_for("task.dashboard"))

"""
routes/auth.py - Login and logout routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login with username/password."""
    if "user" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM USERS WHERE Username=? AND Password=?",
            (username, password),
        ).fetchone()
        conn.close()

        if user:
            session["user"] = {
                "id":       user["UserID"],
                "username": user["Username"],
                "role":     user["Role"],
            }
            flash(f"Welcome back, {user['Username']}!", "success")
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Clear session and redirect to login."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))

import os
import sqlite3
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
DB_NAME = "complaints.db"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me")

CATEGORIES = [
    "Classroom", "Hostel", "Wi-Fi / Internet", "Laboratory",
    "Cleanliness", "Water Supply", "Electricity", "Other"
]
STATUSES = ["Pending", "In Progress", "Resolved"]


def get_db():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE NOT NULL,
                student_name TEXT NOT NULL,
                email TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                feedback TEXT,
                created_at TEXT NOT NULL
            )
        """)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please log in as administrator first.", "warning")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["GET", "POST"])
def submit_complaint():
    if request.method == "POST":
        name = request.form.get("student_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        category = request.form.get("category", "")
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()

        if not all([name, email, category, location, description]):
            flash("Please complete every field.", "danger")
            return redirect(url_for("submit_complaint"))
        if category not in CATEGORIES:
            abort(400)

        ticket_id = "SC-" + secrets.token_hex(3).upper()
        with get_db() as db:
            db.execute("""
                INSERT INTO complaints
                (ticket_id, student_name, email, category, location, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)
            """, (ticket_id, name, email, category, location, description,
                  datetime.now().strftime("%d %b %Y, %I:%M %p")))

        return render_template("submitted.html", ticket_id=ticket_id)

    return render_template("submit.html", categories=CATEGORIES)


@app.route("/track", methods=["GET", "POST"])
def track():
    complaint = None
    if request.method == "POST":
        ticket_id = request.form.get("ticket_id", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        with get_db() as db:
            complaint = db.execute("""
                SELECT * FROM complaints WHERE ticket_id = ? AND email = ?
            """, (ticket_id, email)).fetchone()
        if complaint is None:
            flash("No matching complaint found. Check your ticket ID and email.", "danger")
    return render_template("track.html", complaint=complaint)


@app.route("/feedback", methods=["POST"])
def feedback():
    ticket_id = request.form.get("ticket_id", "").strip().upper()
    email = request.form.get("email", "").strip().lower()
    message = request.form.get("feedback", "").strip()
    if not message:
        flash("Please enter your feedback.", "warning")
        return redirect(url_for("track"))
    with get_db() as db:
        db.execute("""
            UPDATE complaints SET feedback = ?
            WHERE ticket_id = ? AND email = ? AND status = 'Resolved'
        """, (message, ticket_id, email))
    flash("Thank you for your feedback!", "success")
    return redirect(url_for("track"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if secrets.compare_digest(password, ADMIN_PASSWORD):
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect administrator password.", "danger")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    with get_db() as db:
        complaints = db.execute(
            "SELECT * FROM complaints ORDER BY id DESC"
        ).fetchall()
    counts = {
        "total": len(complaints),
        "pending": sum(c["status"] == "Pending" for c in complaints),
        "progress": sum(c["status"] == "In Progress" for c in complaints),
        "resolved": sum(c["status"] == "Resolved" for c in complaints),
    }
    return render_template("admin.html", complaints=complaints,
                           counts=counts, statuses=STATUSES)


@app.route("/admin/update/<ticket_id>", methods=["POST"])
@admin_required
def update_status(ticket_id):
    status = request.form.get("status", "")
    if status not in STATUSES:
        abort(400)
    with get_db() as db:
        db.execute("UPDATE complaints SET status = ? WHERE ticket_id = ?",
                   (status, ticket_id))
    flash(f"Complaint {ticket_id} updated to {status}.", "success")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)

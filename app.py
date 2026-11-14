import os
import sqlite3
import secrets
import smtplib
from werkzeug.utils import secure_filename
from datetime import datetime
from email.message import EmailMessage
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
DB_NAME = "complaints.db"

# Complaint photo upload settings
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_PHOTO_SIZE
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )
def save_complaint_photo(file):
    if not file or file.filename == "":
        return None

    if not allowed_file(file.filename):
        raise ValueError("Please upload a JPG, JPEG, or PNG image.")

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[1].lower()

    unique_filename = f"{secrets.token_hex(8)}.{extension}"

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    file.save(
        os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
    )

    return unique_filename
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

        db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT '',
                is_read INTEGER NOT NULL DEFAULT 0,
                recipient_type TEXT NOT NULL DEFAULT 'student'
            )
        """)
        columns = {
            row["name"]
            for row in db.execute(
                "PRAGMA table_info(complaints)"
            ).fetchall()
        }

        if "photo_filename" not in columns:
            db.execute(
                "ALTER TABLE complaints ADD COLUMN photo_filename TEXT"
            )

        # Add any missing columns to an older notifications table.
        columns = {
            row["name"]
            for row in db.execute(
                "PRAGMA table_info(notifications)"
            ).fetchall()
        }

        required_columns = {
            "ticket_id": "TEXT NOT NULL DEFAULT ''",
            "email": "TEXT NOT NULL DEFAULT ''",
            "message": "TEXT NOT NULL DEFAULT ''",
            "created_at": "TEXT NOT NULL DEFAULT ''",
            "is_read": "INTEGER NOT NULL DEFAULT 0",
            "recipient_type": "TEXT NOT NULL DEFAULT 'student'"
        }

        for column, definition in required_columns.items():
            if column not in columns:
                db.execute(
                    f"ALTER TABLE notifications ADD COLUMN {column} {definition}"
                )



def create_notification(db, recipient_type, ticket_id, email, message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    columns = {
        row["name"]
        for row in db.execute(
            "PRAGMA table_info(notifications)"
        ).fetchall()
    }

    if "craeted_at" in columns:
        db.execute("""
            INSERT INTO notifications
            (ticket_id, email, message, created_at,
             craeted_at, is_read, recipient_type)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (
            ticket_id, email, message,
            current_time, current_time, recipient_type
        ))
    else:
        db.execute("""
            INSERT INTO notifications
            (ticket_id, email, message, created_at,
             is_read, recipient_type)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (
            ticket_id, email, message,
            current_time, recipient_type
        ))



def send_email_notification(recipient, subject, body, ticket_id):
    smtp_host = os.environ.get("SMTP_HOST")
    sender = os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USERNAME")
    if not smtp_host or not sender:
        app.logger.warning(
            "Email notification for %s not sent; configure SMTP_HOST and SMTP_FROM.",
            ticket_id,
        )
        return False

    try:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = recipient
        message.set_content(body)

        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            username = os.environ.get("SMTP_USERNAME")
            password = os.environ.get("SMTP_PASSWORD")
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
    except (OSError, ValueError, smtplib.SMTPException):
        app.logger.exception("Email notification delivery failed for %s.", ticket_id)
        return False
    return True


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
        photo = request.files.get("complaint_photo")

        

        if not all([name, email, category, location, description]):
            flash("Please complete every field.", "danger")
            return redirect(url_for("submit_complaint"))
        if category not in CATEGORIES:
            abort(400)
        try:
            photo_filename = save_complaint_photo(photo)
        except ValueError as error:
            flash(str(error), "danger")
            return redirect(url_for("submit_complaint"))

        ticket_id = "SC-" + secrets.token_hex(3).upper()
        with get_db() as db:
            db.execute("""
                INSERT INTO complaints
                (ticket_id, student_name, email, category, location, description, photo_filename, status, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
            """, (ticket_id, name, email, category, location, description,
      photo_filename, datetime.now().strftime("%d %b %Y, %I:%M %p")))
            student_message = (
                f"Your complaint {ticket_id} has been submitted successfully. "
                "Current status: Pending."
            )
            create_notification(db, "student", ticket_id, email, student_message)
            create_notification(
                db,
                "admin",
                ticket_id,
                "",
                f"New complaint {ticket_id} submitted by {name} ({category}).",
            )

        send_email_notification(
            email,
            f"Complaint {ticket_id} received",
            f"{student_message}\n\nYou can track it on the Smart Campus website using "
            "your ticket ID and the email address used during submission.",
            ticket_id,
        )
        admin_email = os.environ.get("ADMIN_NOTIFICATION_EMAIL")
        if admin_email:
            send_email_notification(
                admin_email,
                f"New campus complaint: {ticket_id}",
                f"A new complaint was submitted by {name}.\n"
                f"Category: {category}\nLocation: {location}\nTicket: {ticket_id}",
                ticket_id,
            )

        return render_template("submitted.html", ticket_id=ticket_id)

    return render_template("submit.html", categories=CATEGORIES)


@app.route("/track", methods=["GET", "POST"])
def track():
    complaint = None
    notifications = []
    if request.method == "POST":
        ticket_id = request.form.get("ticket_id", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        with get_db() as db:
            complaint = db.execute("""
                SELECT * FROM complaints WHERE ticket_id = ? AND email = ?
            """, (ticket_id, email)).fetchone()
            if complaint:
                notifications = db.execute("""
                    SELECT message, created_at
                    FROM notifications
                    WHERE recipient_type = 'student' AND ticket_id = ? AND email = ?
                    ORDER BY id DESC
                """, (ticket_id, email)).fetchall()
        if complaint is None:
            flash("No matching complaint found. Check your ticket ID and email.", "danger")
    return render_template("track.html", complaint=complaint, notifications=notifications)


@app.route("/feedback", methods=["POST"])
def feedback():
    ticket_id = request.form.get("ticket_id", "").strip().upper()
    email = request.form.get("email", "").strip().lower()
    message = request.form.get("feedback", "").strip()
    if not message:
        flash("Please enter your feedback.", "warning")
        return redirect(url_for("track"))
    with get_db() as db:
        complaint = db.execute("""
            SELECT student_name, status FROM complaints
            WHERE ticket_id = ? AND email = ?
        """, (ticket_id, email)).fetchone()
        if complaint is None or complaint["status"] != "Resolved":
            flash("Feedback is only available for a resolved complaint.", "danger")
            return redirect(url_for("track"))
        db.execute("""
            UPDATE complaints SET feedback = ?
            WHERE ticket_id = ? AND email = ? AND status = 'Resolved'
        """, (message, ticket_id, email))
        admin_message = f"Student feedback received for {ticket_id}."
        create_notification(db, "admin", ticket_id, "", admin_message)

    admin_email = os.environ.get("ADMIN_NOTIFICATION_EMAIL")
    if admin_email:
        send_email_notification(
            admin_email,
            f"Student feedback received: {ticket_id}",
            f"Student {complaint['student_name']} submitted feedback for complaint "
            f"{ticket_id}:\n\n{message}",
            ticket_id,
        )
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
        admin_notifications = db.execute("""
            SELECT id, ticket_id, message, created_at, is_read
            FROM notifications
            WHERE recipient_type = 'admin'
            ORDER BY id DESC
            LIMIT 25
        """).fetchall()
        unread_notifications = db.execute("""
            SELECT COUNT(*) FROM notifications
            WHERE recipient_type = 'admin' AND is_read = 0
        """).fetchone()[0]
    counts = {
        "total": len(complaints),
        "pending": sum(c["status"] == "Pending" for c in complaints),
        "progress": sum(c["status"] == "In Progress" for c in complaints),
        "resolved": sum(c["status"] == "Resolved" for c in complaints),
    }
    return render_template("admin.html", complaints=complaints,
                           counts=counts, statuses=STATUSES,
                           admin_notifications=admin_notifications,
                           unread_notifications=unread_notifications)


@app.route("/admin/update/<ticket_id>", methods=["POST"])
@admin_required
def update_status(ticket_id):
    status = request.form.get("status", "")
    if status not in STATUSES:
        abort(400)
    with get_db() as db:
        complaint = db.execute(
            "SELECT email, status FROM complaints WHERE ticket_id = ?",
            (ticket_id,),
        ).fetchone()
        if complaint is None:
            abort(404)
        previous_status = complaint["status"]
        if previous_status != status:
            db.execute("UPDATE complaints SET status = ? WHERE ticket_id = ?",
                       (status, ticket_id))
            status_message = f"Your complaint {ticket_id} status changed to {status}."
            create_notification(db, "student", ticket_id, complaint["email"], status_message)

    if previous_status != status:
        send_email_notification(
            complaint["email"],
            f"Complaint {ticket_id} status updated",
            f"Your complaint status changed from {previous_status} to {status}.\n"
            f"Ticket: {ticket_id}",
            ticket_id,
        )
        flash(f"Complaint {ticket_id} updated to {status}.", "success")
    else:
        flash(f"Complaint {ticket_id} is already {status}.", "warning")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/notifications/read", methods=["POST"])
@admin_required
def mark_admin_notifications_read():
    with get_db() as db:
        db.execute("""
            UPDATE notifications SET is_read = 1
            WHERE recipient_type = 'admin' AND is_read = 0
        """)
    flash("Admin notifications marked as read.", "success")
    return redirect(url_for("admin_dashboard"))


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)

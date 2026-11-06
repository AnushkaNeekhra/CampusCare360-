# Smart Campus – Student Complaint & Assistance System

A beginner-friendly academic prototype built with Python, Flask, HTML, CSS and SQLite.

## 1. Install the requirements

Install Python 3.10 or newer and VS Code. Open this project folder in VS Code.

Open the terminal in VS Code and run:

```bash
python -m venv venv
```

Activate the environment:

**Windows**
```bash
venv\\Scripts\\activate
```

**macOS / Linux**
```bash
source venv/bin/activate
```

Install Flask:

```bash
pip install -r requirements.txt
```

## 2. Run the website

```bash
python app.py
```

Open this address in your browser:

http://127.0.0.1:5000

The SQLite database `complaints.db` is created automatically the first time the app starts.

## 3. Try the project

1. Select **Submit Complaint** and enter sample data.
2. Save the ticket ID shown after submission.
3. Select **Track** and enter the ticket ID plus the same email address.
4. Open **Admin** and log in.
5. Starter demo password: `change-me`.
6. Change the complaint status and save.
7. Return to Track to see the updated status.
8. Once marked Resolved, submit feedback.

## 4. Change the administrator password

The starter password is for local demonstration only.

Windows PowerShell:
```powershell
$env:ADMIN_PASSWORD="YourStrongDemoPassword"
$env:SECRET_KEY="replace-with-a-long-random-secret"
python app.py
```

macOS / Linux:
```bash
export ADMIN_PASSWORD="YourStrongDemoPassword"
export SECRET_KEY="replace-with-a-long-random-secret"
python app.py
```

## 5. Project structure

```text
smart_campus_project/
├── app.py
├── requirements.txt
├── README.md
├── complaints.db       (created automatically after first run)
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── submit.html
│   ├── submitted.html
│   ├── track.html
│   ├── admin_login.html
│   └── admin.html
└── static/
    └── style.css
```

## 6. Important academic and safety notes

- This is a local academic prototype, not a production university system.
- Do not use real student personal information in a public demo.
- Before real deployment, add CSRF protection, stronger authentication, role management, HTTPS, input validation, rate limiting, backups and privacy controls.
- The starter app uses a simple shared admin password so a beginner can understand the workflow. It is not suitable for real institutional use.
- Explain honestly which features are implemented and which are future enhancements.

# Student Task Manager

A simple three-tier student task manager built with HTML/CSS/JavaScript, Flask, and MySQL. The app is intentionally small so it can later be deployed on AWS as a Multi-AZ three-tier web application with an Application Load Balancer, Auto Scaling, and Amazon RDS.

## Features

- Register and log in
- View a personal dashboard
- Create, edit, complete, and delete tasks
- Session-based authentication
- Per-user task isolation

## Project structure

```
student-task-manager/
├── app.py
├── config.py
├── requirements.txt
├── .env
├── README.md
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py
│   └── task_routes.py
├── database/
│   ├── __init__.py
│   └── db.py
├── utils/
│   ├── __init__.py
│   ├── auth.py
│   └── csrf.py
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── add_task.html
│   └── edit_task.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── script.js
```

`templates/base.html` is a shared layout used by the pages above. Database credentials stay in `.env`.

## Local setup

1. Install Python 3.10+ and MySQL.
2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Set environment variables (do not hardcode production credentials):

```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=student_task_manager
export DB_PORT=3306
export SECRET_KEY=change-this-secret
export PORT=5001
export FLASK_DEBUG=true
export INIT_CREATE_DATABASE=false
export TRUST_PROXY=false
export SESSION_COOKIE_SECURE=false
export DB_SSL=false
```

Create the MySQL/RDS database yourself (for example `stm`). The app creates the `users` and `tasks` tables if they are missing. It does **not** create the database unless you set `INIT_CREATE_DATABASE=true` (local only; RDS app users usually cannot `CREATE DATABASE`).

4. Start the app:

```bash
python app.py
```

Production-style local run (also used on EC2):

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
```

Open http://127.0.0.1:5001 (port 5000 is often taken by macOS AirPlay).

## Routes

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | Redirects to dashboard or login |
| GET/POST | `/login` | Login |
| GET/POST | `/register` | Registration |
| GET | `/dashboard` | Task dashboard |
| GET/POST | `/add-task` | Create a task |
| GET/POST | `/edit-task/<task_id>` | Update a task |
| POST | `/complete-task/<task_id>` | Mark a task completed |
| POST | `/delete-task/<task_id>` | Delete a task |
| GET/POST | `/logout` | Clear the session |
| GET | `/health` | Load balancer health check |

Health check response:

```json
{"status": "healthy"}
```

## Database

Database name: `student_task_manager`

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    priority ENUM('Low', 'Medium', 'High') NOT NULL DEFAULT 'Medium',
    status ENUM('Pending', 'Completed') NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

Passwords are stored with `werkzeug.security.generate_password_hash()`. SQL uses parameterized queries.

## AWS notes

The application is designed to stay compatible with this architecture:

```
Internet -> ALB -> EC2 (AZ A) / EC2 (AZ B) -> Amazon RDS MySQL
```

- Listens on `0.0.0.0`
- Port is configurable with `PORT`
- Run with Gunicorn on EC2: `gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app`
- Set `TRUST_PROXY=true` behind an Application Load Balancer
- Set `SESSION_COOKIE_SECURE=true` and `PREFERRED_URL_SCHEME=https` when the ALB uses HTTPS
- Set `DB_HOST` to the RDS endpoint (not localhost)
- Set `DB_SSL=true` (and optionally `DB_SSL_CA`) if RDS requires TLS
- Use the same strong `SECRET_KEY` on every Auto Scaling instance
- Set `FLASK_DEBUG=false` in production
- Database settings come from environment variables, so local MySQL can be replaced with Amazon RDS without changing application logic
- Persistent user and task data is stored in MySQL, not on the EC2 filesystem
- Flask sessions are cookie-based; use the same `SECRET_KEY` on every instance
- `/health` is intended for the Application Load Balancer health check

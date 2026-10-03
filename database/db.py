import mysql.connector
from mysql.connector import errorcode

from config import Config


def _connect_kwargs(include_database=True):
    kwargs = {
        "host": Config.DB_HOST,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "port": Config.DB_PORT,
        "autocommit": False,
        "charset": "utf8mb4",
        "use_unicode": True,
        "connection_timeout": 10,
    }
    if include_database:
        kwargs["database"] = Config.DB_NAME
    if Config.DB_SSL:
        kwargs["ssl_disabled"] = False
        if Config.DB_SSL_CA:
            kwargs["ssl_ca"] = Config.DB_SSL_CA
    return kwargs


def get_db():
    return mysql.connector.connect(**_connect_kwargs(include_database=True))


def _create_tables(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            due_date DATE NOT NULL,
            priority ENUM('Low', 'Medium', 'High') NOT NULL DEFAULT 'Medium',
            status ENUM('Pending', 'Completed') NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )


def init_db():
    if Config.INIT_CREATE_DATABASE:
        connection = mysql.connector.connect(**_connect_kwargs(include_database=False))
        cursor = connection.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.execute(f"USE `{Config.DB_NAME}`")
        _create_tables(cursor)
        connection.commit()
        cursor.close()
        connection.close()
        return

    connection = get_db()
    cursor = connection.cursor()
    _create_tables(cursor)
    connection.commit()
    cursor.close()
    connection.close()


def query_db(sql, params=None, fetchone=False, fetchall=False, commit=False):
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        if commit:
            connection.commit()
            result = cursor.lastrowid
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_user_by_email(email):
    return query_db(
        "SELECT * FROM users WHERE email = %s",
        (email,),
        fetchone=True,
    )


def get_user_by_id(user_id):
    return query_db(
        "SELECT id, name, email FROM users WHERE id = %s",
        (user_id,),
        fetchone=True,
    )


def create_user(name, email, password_hash):
    return query_db(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
        (name, email, password_hash),
        commit=True,
    )


def get_tasks_for_user(user_id):
    return query_db(
        """
        SELECT * FROM tasks
        WHERE user_id = %s
        ORDER BY FIELD(status, 'Pending', 'Completed'), due_date ASC, id DESC
        """,
        (user_id,),
        fetchall=True,
    )


def get_task_by_id(task_id):
    return query_db("SELECT * FROM tasks WHERE id = %s", (task_id,), fetchone=True)


def create_task(user_id, title, description, due_date, priority):
    return query_db(
        """
        INSERT INTO tasks (user_id, title, description, due_date, priority, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (user_id, title, description, due_date, priority, "Pending"),
        commit=True,
    )


def update_task(title, description, due_date, priority, status, task_id, user_id):
    return query_db(
        """
        UPDATE tasks
        SET title = %s, description = %s, due_date = %s, priority = %s, status = %s
        WHERE id = %s AND user_id = %s
        """,
        (title, description, due_date, priority, status, task_id, user_id),
        commit=True,
    )


def complete_task(task_id, user_id):
    return query_db(
        "UPDATE tasks SET status = %s WHERE id = %s AND user_id = %s",
        ("Completed", task_id, user_id),
        commit=True,
    )


def delete_task(task_id, user_id):
    return query_db(
        "DELETE FROM tasks WHERE id = %s AND user_id = %s",
        (task_id, user_id),
        commit=True,
    )


def init_db_or_exit():
    try:
        init_db()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise SystemExit(
                "MySQL access denied. Check DB_USER and DB_PASSWORD environment variables."
            ) from err
        if err.errno == errorcode.CR_CONN_HOST_ERROR:
            raise SystemExit(
                "Could not connect to MySQL. Check DB_HOST, DB_PORT, and that MySQL is running."
            ) from err
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            raise SystemExit(
                f"Database '{Config.DB_NAME}' does not exist. Create it in MySQL/RDS, "
                "or set INIT_CREATE_DATABASE=true for local development only."
            ) from err
        raise

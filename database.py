import sqlite3
import os
from flask import g

def get_db(app=None):
    from flask import current_app
    if app is None:
        app = current_app
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        db = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                avatar_color TEXT DEFAULT '#6366f1',
                groq_api_key TEXT DEFAULT '',
                is_employee INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                slug TEXT UNIQUE NOT NULL,
                is_published INTEGER DEFAULT 0,
                allow_multiple_responses INTEGER DEFAULT 1,
                show_progress_bar INTEGER DEFAULT 1,
                success_message TEXT DEFAULT 'Thank you for your response!',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,
                is_required INTEGER DEFAULT 0,
                options TEXT DEFAULT '[]',
                placeholder TEXT DEFAULT '',
                order_index INTEGER DEFAULT 0,
                logic_rules TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_id INTEGER NOT NULL,
                respondent_email TEXT DEFAULT '',
                respondent_ip TEXT DEFAULT '',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completion_time INTEGER DEFAULT 0,
                FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_value TEXT DEFAULT '',
                FOREIGN KEY (response_id) REFERENCES responses(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ai_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                report_type TEXT DEFAULT 'analysis',
                content TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                file_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                department TEXT DEFAULT '',
                email TEXT DEFAULT '',
                manager_id INTEGER,
                FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS sent_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                recipients TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sent_email_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sent_email_id INTEGER NOT NULL,
                recipient_email TEXT NOT NULL,
                recipient_name TEXT NOT NULL,
                personalized_body TEXT NOT NULL,
                status TEXT DEFAULT 'Sent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sent_email_id) REFERENCES sent_emails(id) ON DELETE CASCADE
            );
        ''')
        
        # Self-healing migration to add logic_rules column to questions table if it doesn't exist
        try:
            db.execute("ALTER TABLE questions ADD COLUMN logic_rules TEXT DEFAULT '[]'")
        except sqlite3.OperationalError:
            pass
            
        # Migration to add is_employee column to users table
        try:
            db.execute("ALTER TABLE users ADD COLUMN is_employee INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Migration to add email column to employees table
        try:
            db.execute("ALTER TABLE employees ADD COLUMN email TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

        # Migration to add SMTP fields to users table
        for col, col_type in [
            ('smtp_server', "TEXT DEFAULT ''"),
            ('smtp_port', "INTEGER DEFAULT 587"),
            ('smtp_user', "TEXT DEFAULT ''"),
            ('smtp_password', "TEXT DEFAULT ''"),
            ('smtp_sender_name', "TEXT DEFAULT ''"),
            ('smtp_sender_email', "TEXT DEFAULT ''"),
            ('smtp_security', "TEXT DEFAULT 'TLS'")
        ]:
            try:
                db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
            
        db.commit()
        db.close()

    app.teardown_appcontext(close_db)

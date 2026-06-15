from flask import Flask
from database import init_db
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.forms import forms_bp
from routes.responses import responses_bp
from routes.analytics import analytics_bp
from routes.settings import settings_bp
from routes.public import public_bp
from routes.api import api_bp
import os
import secrets

# Load .env file manually (no external dependency needed)
def _load_env_file(path):
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip()
                    # Always overwrite to ensure auto-reloader picks up .env changes
                    if key:
                        os.environ[key] = value
    except FileNotFoundError:
        pass

_load_env_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload
    app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'instance', 'smartforms.db')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)

    with app.app_context():
        init_db(app)

    from routes.hr_announcements import hr_announcements_bp
    from routes.hr_documents import hr_documents_bp
    from routes.hr_orgchart import hr_orgchart_bp
    from routes.hr_mailer import hr_mailer_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(forms_bp)
    app.register_blueprint(responses_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp)
    
    app.register_blueprint(hr_announcements_bp)
    app.register_blueprint(hr_documents_bp)
    app.register_blueprint(hr_orgchart_bp)
    app.register_blueprint(hr_mailer_bp)

    return app

app = create_app()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG') == '1'
    app.run(debug=debug, host='0.0.0.0', port=5000)

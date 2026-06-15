import re
import json
import os
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash, jsonify
from database import get_db
from helpers import login_required, employee_required, get_current_user, get_avatar_initials
from ai_service import draft_email

hr_mailer_bp = Blueprint('hr_mailer', __name__, url_prefix='/hr/mailer')

def get_smtp_config(user):
    # Retrieve SMTP configuration from database user fields
    server = (user['smtp_server'] or '').strip()
    port = user['smtp_port'] or 587
    username = (user['smtp_user'] or '').strip()
    password = (user['smtp_password'] or '').strip()
    sender_name = (user['smtp_sender_name'] or '').strip()
    sender_email = (user['smtp_sender_email'] or '').strip()
    security = (user['smtp_security'] or 'TLS').strip()

    # Fallback to environment variables if not set in database
    if not server:
        server = os.environ.get('SMTP_SERVER', '').strip()
        port_env = os.environ.get('SMTP_PORT', '587').strip()
        try:
            port = int(port_env) if port_env else 587
        except ValueError:
            port = 587
        username = os.environ.get('SMTP_USERNAME', '').strip()
        password = os.environ.get('SMTP_PASSWORD', '').strip()
        sender_name = os.environ.get('SMTP_SENDER_NAME', '').strip()
        sender_email = os.environ.get('SMTP_SENDER_EMAIL', '').strip()
        security = os.environ.get('SMTP_SECURITY', 'TLS').strip()

    # Fallbacks if sender fields still empty
    if not sender_email:
        if username and '@' in username:
            sender_email = username
        else:
            sender_email = user['email']

    if not sender_name:
        sender_name = user['name']

    return {
        'server': server,
        'port': port,
        'username': username,
        'password': password,
        'sender_name': sender_name,
        'sender_email': sender_email,
        'security': security
    }

def send_campaign_bg(app, sent_email_id, smtp_config, recipient_details):
    with app.app_context():
        # Establish connection to SMTP
        server = None
        connection_error = None
        try:
            if smtp_config['security'] == 'SSL':
                server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'], timeout=15)
            else:
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=15)
                server.ehlo()
                if smtp_config['security'] == 'TLS':
                    server.starttls()
                    server.ehlo()
            
            if smtp_config['username'] and smtp_config['password']:
                server.login(smtp_config['username'], smtp_config['password'])
        except Exception as e:
            connection_error = str(e)

        from database import get_db
        db = get_db(app)

        if connection_error:
            # Mark all as failed due to connection error
            for r in recipient_details:
                db.execute(
                    'UPDATE sent_email_recipients SET status = ? WHERE id = ?',
                    (f'Failed: Connection error: {connection_error}', r['id'])
                )
            db.commit()
            return

        # Send personalized emails to each recipient
        for r in recipient_details:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = Header(r['subject'], 'utf-8')
                
                sender_header = f"{Header(smtp_config['sender_name'], 'utf-8').encode()} <{smtp_config['sender_email']}>"
                msg['From'] = sender_header
                msg['To'] = r['email']
                
                part = MIMEText(r['body'], 'plain', 'utf-8')
                msg.attach(part)
                
                server.sendmail(smtp_config['sender_email'], [r['email']], msg.as_string())
                
                db.execute(
                    'UPDATE sent_email_recipients SET status = ? WHERE id = ?',
                    ('Sent', r['id'])
                )
            except Exception as e:
                db.execute(
                    'UPDATE sent_email_recipients SET status = ? WHERE id = ?',
                    (f'Failed: {str(e)}', r['id'])
                )
            db.commit()

        try:
            server.quit()
        except Exception:
            pass

def parse_first_name(email_addr: str) -> str:
    """Extract a professional first name from an email address using heuristics."""
    email_addr = email_addr.strip().lower()
    if not email_addr or '@' not in email_addr:
        return "Team Member"
    
    name_part = email_addr.split('@')[0]
    # Split by standard separators
    first_part = name_part.split('.')[0].split('_')[0].split('-')[0]
    # Strip any trailing digits
    first_name_raw = re.sub(r'\d+$', '', first_part)
    first_name = first_name_raw.capitalize()
    
    # Custom/common name overrides or mappings
    if first_name.lower().startswith('nithinkata') or first_name.lower() == 'nithinkata':
        first_name = 'Nithin'
    elif first_name.lower().startswith('aravind'):
        first_name = 'Aravind'
        
    return first_name or "Team Member"

@hr_mailer_bp.route('/', methods=['GET'])
@employee_required
def index():
    db = get_db(current_app)
    user = get_current_user()
    initials = get_avatar_initials(user['name']) if user else 'U'
    
    employees = db.execute('SELECT * FROM employees ORDER BY name').fetchall()
    
    return render_template('hr/mailer.html',
        user=user,
        initials=initials,
        employees=employees
    )

@hr_mailer_bp.route('/draft_ai', methods=['POST'])
@employee_required
def draft_ai():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'success': False, 'error': 'Prompt is required.'}), 400
        
    user = get_current_user()
    api_key = (user['groq_api_key'] or '').strip() or os.environ.get('GEMINI_API_KEY', '').strip()
    
    try:
        result = draft_email(api_key, prompt)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@hr_mailer_bp.route('/send', methods=['POST'])
@employee_required
def send_mailer():
    db = get_db(current_app)
    user = get_current_user()
    
    # Check SMTP configuration
    smtp_config = get_smtp_config(user)
    if not smtp_config['server']:
        flash('SMTP Server is not configured. Please configure it in your Settings or environment file to send real emails.', 'error')
        return redirect(url_for('hr_mailer.index'))
        
    subject = request.form.get('subject', '').strip()
    body = request.form.get('body', '')
    
    selected_emp_ids = request.form.getlist('employees[]')
    custom_emails_raw = request.form.get('custom_recipients', '').strip()
    
    if not subject:
        flash('Subject is required.', 'error')
        return redirect(url_for('hr_mailer.index'))
    if not body:
        flash('Email body is required.', 'error')
        return redirect(url_for('hr_mailer.index'))
        
    # Gather recipients
    recipients = {}  # email -> first_name
    
    # 1. Add selected employees
    if selected_emp_ids:
        placeholders = ','.join('?' for _ in selected_emp_ids)
        query = f"SELECT name, email FROM employees WHERE id IN ({placeholders})"
        emps = db.execute(query, selected_emp_ids).fetchall()
        for emp in emps:
            emp_email = (emp['email'] or '').strip()
            if emp_email:
                first_name = emp['name'].strip().split()[0] if emp['name'] else "Team Member"
                recipients[emp_email.lower()] = first_name
                
    # 2. Add custom recipients
    if custom_emails_raw:
        email_candidates = re.split(r'[;,\n\r]+', custom_emails_raw)
        for email in email_candidates:
            email = email.strip()
            if not email or '@' not in email:
                continue
            email_lower = email.lower()
            if email_lower not in recipients:
                matching_emp = db.execute('SELECT name FROM employees WHERE LOWER(email) = ?', (email_lower,)).fetchone()
                if matching_emp:
                    first_name = matching_emp['name'].strip().split()[0]
                else:
                    first_name = parse_first_name(email_lower)
                recipients[email_lower] = first_name

    if not recipients:
        flash('Please specify at least one recipient (either select employees or type custom emails).', 'error')
        return redirect(url_for('hr_mailer.index'))

    # Store campaign and individual recipient records in Pending status
    recipients_list_str = ', '.join(recipients.keys())
    try:
        cursor = db.execute(
            'INSERT INTO sent_emails (sender_id, subject, body, recipients) VALUES (?, ?, ?, ?)',
            (session['user_id'], subject, body, recipients_list_str)
        )
        sent_email_id = cursor.lastrowid
        
        recipient_details = []
        for email, first_name in recipients.items():
            pers_subject = subject.replace('{name}', first_name).replace('[Name]', first_name).replace('[name]', first_name)
            
            pers_body = body
            has_placeholder = any(p in pers_body for p in ['{name}', '[Name]', '[name]'])
            if not has_placeholder:
                pers_body = f"Dear {first_name},\n\n" + pers_body
            else:
                pers_body = pers_body.replace('{name}', first_name).replace('[Name]', first_name).replace('[name]', first_name)
                
            rec_cursor = db.execute(
                'INSERT INTO sent_email_recipients (sent_email_id, recipient_email, recipient_name, personalized_body, status) VALUES (?, ?, ?, ?, ?)',
                (sent_email_id, email, first_name, pers_body, 'Pending')
            )
            recipient_details.append({
                'id': rec_cursor.lastrowid,
                'email': email,
                'name': first_name,
                'subject': pers_subject,
                'body': pers_body
            })
            
        db.commit()
        
        # Start background thread to send the campaign
        app_obj = current_app._get_current_object()
        thread = threading.Thread(
            target=send_campaign_bg,
            args=(app_obj, sent_email_id, smtp_config, recipient_details)
        )
        thread.daemon = True
        thread.start()
        
        flash(f'Bulk email campaign "{subject}" started successfully in the background for {len(recipients)} recipient(s).', 'success')
        return redirect(url_for('hr_mailer.detail', id=sent_email_id))
        
    except Exception as e:
        flash(f'Error starting bulk mailer campaign: {str(e)}', 'error')
        return redirect(url_for('hr_mailer.index'))

@hr_mailer_bp.route('/history', methods=['GET'])
@employee_required
def history():
    db = get_db(current_app)
    user = get_current_user()
    initials = get_avatar_initials(user['name']) if user else 'U'
    
    campaigns = db.execute('''
        SELECT se.*, datetime(se.created_at, 'localtime') as local_created_at, u.name as sender_name,
               (SELECT COUNT(*) FROM sent_email_recipients WHERE sent_email_id = se.id) as recipient_count
        FROM sent_emails se
        JOIN users u ON se.sender_id = u.id
        ORDER BY se.created_at DESC
    ''').fetchall()
    
    return render_template('hr/mailer_history.html',
        user=user,
        initials=initials,
        campaigns=campaigns
    )

@hr_mailer_bp.route('/detail/<int:id>', methods=['GET'])
@employee_required
def detail(id):
    db = get_db(current_app)
    user = get_current_user()
    initials = get_avatar_initials(user['name']) if user else 'U'
    
    campaign = db.execute('''
        SELECT se.*, datetime(se.created_at, 'localtime') as local_created_at, u.name as sender_name
        FROM sent_emails se
        JOIN users u ON se.sender_id = u.id
        WHERE se.id = ?
    ''', (id,)).fetchone()
    
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('hr_mailer.history'))
        
    recipients = db.execute('''
        SELECT * FROM sent_email_recipients 
        WHERE sent_email_id = ? 
        ORDER BY recipient_name
    ''', (id,)).fetchall()
    
    return render_template('hr/mailer_detail.html',
        user=user,
        initials=initials,
        campaign=campaign,
        recipients=recipients
    )

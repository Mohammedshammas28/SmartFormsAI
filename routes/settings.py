from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_db
from helpers import login_required, get_current_user, get_avatar_initials, hash_password, verify_password
from flask import current_app
import os

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def index():
    db = get_db(current_app)
    user = get_current_user()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'profile':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            
            if not name or len(name) < 2:
                flash('Name must be at least 2 characters.', 'error')
            elif not email or '@' not in email:
                flash('Valid email required.', 'error')
            else:
                existing = db.execute('SELECT id FROM users WHERE email = ? AND id != ?',
                                      (email, session['user_id'])).fetchone()
                if existing:
                    flash('Email already in use.', 'error')
                else:
                    db.execute('UPDATE users SET name = ?, email = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                               (name, email, session['user_id']))
                    db.commit()
                    session['user_name'] = name
                    session['user_email'] = email
                    flash('Profile updated successfully.', 'success')
        
        elif action == 'password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')
            
            if not verify_password(current_pw, user['password_hash']):
                flash('Current password is incorrect.', 'error')
            elif len(new_pw) < 6:
                flash('New password must be at least 6 characters.', 'error')
            elif new_pw != confirm_pw:
                flash('Passwords do not match.', 'error')
            else:
                new_hash = hash_password(new_pw)
                db.execute('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                           (new_hash, session['user_id']))
                db.commit()
                flash('Password changed successfully.', 'success')
        
        elif action == 'api_key':
            groq_key = request.form.get('groq_api_key', '').strip()
            db.execute('UPDATE users SET groq_api_key = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                       (groq_key, session['user_id']))
            db.commit()
            flash('API key saved successfully.', 'success')
        
        elif action == 'smtp_config':
            smtp_server = request.form.get('smtp_server', '').strip()
            smtp_port = request.form.get('smtp_port', '587').strip()
            smtp_user = request.form.get('smtp_user', '').strip()
            smtp_password = request.form.get('smtp_password', '').strip()
            smtp_sender_name = request.form.get('smtp_sender_name', '').strip()
            smtp_sender_email = request.form.get('smtp_sender_email', '').strip().lower()
            smtp_security = request.form.get('smtp_security', 'TLS').strip()
            
            try:
                smtp_port_val = int(smtp_port)
            except ValueError:
                smtp_port_val = 587
                
            db.execute('''
                UPDATE users 
                SET smtp_server = ?, smtp_port = ?, smtp_user = ?, smtp_password = ?, 
                    smtp_sender_name = ?, smtp_sender_email = ?, smtp_security = ?, 
                    updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (smtp_server, smtp_port_val, smtp_user, smtp_password, 
                  smtp_sender_name, smtp_sender_email, smtp_security, session['user_id']))
            db.commit()
            flash('SMTP configuration saved successfully.', 'success')
        
        return redirect(url_for('settings.index'))
    
    user = get_current_user()
    initials = get_avatar_initials(user['name']) if user else 'U'
    env_gemini_key = bool(os.environ.get('GEMINI_API_KEY', ''))
    user_has_key = bool((user['groq_api_key'] or '').strip()) if user else False
    # Determine AI status label
    if user_has_key or env_gemini_key:
        ai_status = 'gemini'
    else:
        ai_status = 'template'
    return render_template('settings/index.html', user=user, initials=initials,
                           env_gemini_key=env_gemini_key, ai_status=ai_status)

@settings_bp.route('/settings/test_smtp', methods=['POST'])
@login_required
def test_smtp():
    data = request.get_json() or {}
    smtp_server = data.get('smtp_server', '').strip()
    smtp_port = data.get('smtp_port', '587').strip()
    smtp_user = data.get('smtp_user', '').strip()
    smtp_password = data.get('smtp_password', '').strip()
    smtp_security = data.get('smtp_security', 'TLS').strip()
    
    if not smtp_server:
        return jsonify({'success': False, 'error': 'SMTP server is required.'}), 400
        
    try:
        port = int(smtp_port)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid SMTP port.'}), 400
        
    import smtplib
    try:
        if smtp_security == 'SSL':
            server = smtplib.SMTP_SSL(smtp_server, port, timeout=7)
        else:
            server = smtplib.SMTP(smtp_server, port, timeout=7)
            server.ehlo()
            if smtp_security == 'TLS':
                server.starttls()
                server.ehlo()
                
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
            
        server.quit()
        return jsonify({'success': True, 'message': 'SMTP connection and login successful!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

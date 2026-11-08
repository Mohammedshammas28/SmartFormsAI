from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, send_from_directory, flash
from database import get_db
from helpers import login_required, employee_required, get_current_user, get_avatar_initials
import os
import werkzeug.utils

hr_documents_bp = Blueprint('hr_documents', __name__, url_prefix='/hr/documents')

@hr_documents_bp.route('/', methods=['GET', 'POST'])
@employee_required
def index():
    db = get_db(current_app)
    user = get_current_user()
    initials = get_avatar_initials(user['name']) if user else 'U'
    
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
    os.makedirs(upload_dir, exist_ok=True)
    
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            flash('Document title is required.', 'error')
        elif 'document' not in request.files:
            flash('No document uploaded.', 'error')
        else:
            file = request.files['document']
            if file.filename == '':
                flash('No file selected.', 'error')
            else:
                try:
                    filename = werkzeug.utils.secure_filename(file.filename)
                    file_path = os.path.join(upload_dir, filename)
                    file.save(file_path)
                    
                    db.execute('INSERT INTO documents (user_id, title, file_name) VALUES (?, ?, ?)',
                               (session['user_id'], title, filename))
                    db.commit()
                    flash('Document uploaded successfully.', 'success')
                    return redirect(url_for('hr_documents.index'))
                except Exception as e:
                    flash(f'Error uploading document: {str(e)}', 'error')

    documents = db.execute('''
        SELECT d.*, datetime(d.created_at, 'localtime') as local_created_at, u.name as uploader_name 
        FROM documents d
        JOIN users u ON d.user_id = u.id
        ORDER BY d.created_at DESC
    ''').fetchall()

    return render_template('hr/documents.html',
        user=user,
        initials=initials,
        documents=documents
    )

@hr_documents_bp.route('/download/<filename>')
@employee_required
def download(filename):
    clean_name = werkzeug.utils.secure_filename(filename)
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
    target_path = os.path.join(upload_dir, clean_name)
    if not os.path.exists(target_path):
        fallback_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'documents')
        if os.path.exists(os.path.join(fallback_dir, clean_name)):
            upload_dir = fallback_dir
    return send_from_directory(upload_dir, clean_name, as_attachment=True)

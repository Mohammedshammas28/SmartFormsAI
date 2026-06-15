from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, flash
from database import get_db
from helpers import login_required, employee_required, get_current_user, get_avatar_initials

hr_orgchart_bp = Blueprint('hr_orgchart', __name__, url_prefix='/hr/orgchart')

@hr_orgchart_bp.route('/')
@employee_required
def index():
    db = get_db(current_app)
    user = get_current_user()
    initials = get_avatar_initials(user['name']) if user else 'U'
    
    employees = db.execute('SELECT * FROM employees ORDER BY name').fetchall()
    
    return render_template('hr/orgchart.html',
        user=user,
        initials=initials,
        employees=employees
    )

@hr_orgchart_bp.route('/add', methods=['POST'])
@employee_required
def add_employee():
    db = get_db(current_app)
    name = request.form.get('name')
    position = request.form.get('position')
    department = request.form.get('department')
    email = request.form.get('email', '').strip()
    manager_id = request.form.get('manager_id')
    
    if not manager_id:
        manager_id = None
        
    if name and position:
        db.execute('INSERT INTO employees (name, position, department, email, manager_id) VALUES (?, ?, ?, ?, ?)',
                   (name, position, department, email, manager_id))
        db.commit()
        flash('Employee added successfully.', 'success')
    else:
        flash('Name and position are required.', 'error')
        
    return redirect(url_for('hr_orgchart.index'))

@hr_orgchart_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@employee_required
def edit_employee(id):
    db = get_db(current_app)
    if request.method == 'POST':
        name = request.form.get('name')
        position = request.form.get('position')
        department = request.form.get('department')
        email = request.form.get('email', '').strip()
        manager_id = request.form.get('manager_id')
        
        if not manager_id or str(manager_id) == str(id): # Prevent self-management
            manager_id = None
            
        if name and position:
            db.execute('UPDATE employees SET name=?, position=?, department=?, email=?, manager_id=? WHERE id=?',
                       (name, position, department, email, manager_id, id))
            db.commit()
            flash('Employee updated successfully.', 'success')
            return redirect(url_for('hr_orgchart.index'))
            
    employee = db.execute('SELECT * FROM employees WHERE id = ?', (id,)).fetchone()
    employees = db.execute('SELECT * FROM employees WHERE id != ? ORDER BY name', (id,)).fetchall()
    user = get_current_user()
    initials = get_avatar_initials(user['name']) if user else 'U'
    
    return render_template('hr/edit_employee.html',
        user=user,
        initials=initials,
        employee=employee,
        employees=employees
    )

@hr_orgchart_bp.route('/delete/<int:id>', methods=['POST'])
@employee_required
def delete_employee(id):
    db = get_db(current_app)
    db.execute('DELETE FROM employees WHERE id = ?', (id,))
    db.commit()
    flash('Employee deleted successfully.', 'success')
    return redirect(url_for('hr_orgchart.index'))

@hr_orgchart_bp.route('/api/data')
@employee_required
def api_data():
    db = get_db(current_app)
    employees = db.execute('SELECT * FROM employees').fetchall()
    
    data = []
    for emp in employees:
        data.append({
            'id': str(emp['id']),
            'name': emp['name'],
            'position': emp['position'],
            'department': emp['department'],
            'email': emp['email'] if 'email' in emp.keys() else '',
            'manager_id': str(emp['manager_id']) if emp['manager_id'] else ''
        })
    return jsonify(data)

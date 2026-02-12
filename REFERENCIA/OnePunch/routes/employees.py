"""
Employee Management Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.company import Company
from models.employee import Employee, EmployeeRole

employees_bp = Blueprint('employees', __name__)

def get_user_company():
    """Helper to get current user's company"""
    user_id = get_jwt_identity()
    try:
        uid = int(user_id)
        user = User.query.get(uid)
        if not user or not user.company:
            return None, None
        return user, user.company
    except Exception:
        return None, None

@employees_bp.route('/', methods=['GET'])
@jwt_required()
def get_employees():
    """Get all employees for the company"""
    user, company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
        
    employees = Employee.query.filter_by(company_id=company.id).all()
    return jsonify({
        'employees': [e.to_dict() for e in employees]
    })

@employees_bp.route('/', methods=['POST'])
@jwt_required()
def add_employee():
    """Add a new employee"""
    user, company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
        
    data = request.get_json()
    
    # Validation
    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
        
    try:
        new_employee = Employee(
            company_id=company.id,
            name=data['name'],
            email=data.get('email'),
            phone=data.get('phone'),
            role=EmployeeRole(data.get('role', 'general')),
            department=data.get('department'),
            is_available=data.get('is_available', True),
            can_receive_calls=data.get('can_receive_calls', True),
            can_receive_messages=data.get('can_receive_messages', True)
        )
        
        db.session.add(new_employee)
        db.session.commit()
        
        return jsonify({
            'message': 'Employee added successfully',
            'employee': new_employee.to_dict()
        }), 201
        
    except ValueError:
        return jsonify({'error': 'Invalid role'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employees_bp.route('/<int:employee_id>', methods=['PUT'])
@jwt_required()
def update_employee(employee_id):
    """Update an employee"""
    user, company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
        
    employee = Employee.query.filter_by(id=employee_id, company_id=company.id).first()
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
        
    data = request.get_json()
    
    try:
        if 'name' in data:
            employee.name = data['name']
        if 'email' in data:
            employee.email = data['email']
        if 'phone' in data:
            employee.phone = data['phone']
        if 'role' in data:
            employee.role = EmployeeRole(data['role'])
        if 'department' in data:
            employee.department = data['department']
        if 'is_available' in data:
            employee.is_available = data['is_available']
        if 'can_receive_calls' in data:
            employee.can_receive_calls = data['can_receive_calls']
        if 'can_receive_messages' in data:
            employee.can_receive_messages = data['can_receive_messages']
            
        db.session.commit()
        
        return jsonify({
            'message': 'Employee updated successfully',
            'employee': employee.to_dict()
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid role'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employees_bp.route('/<int:employee_id>', methods=['DELETE'])
@jwt_required()
def delete_employee(employee_id):
    """Delete an employee"""
    user, company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
        
    employee = Employee.query.filter_by(id=employee_id, company_id=company.id).first()
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
        
    try:
        db.session.delete(employee)
        db.session.commit()
        return jsonify({'message': 'Employee deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

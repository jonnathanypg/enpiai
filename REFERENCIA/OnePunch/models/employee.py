"""
Employee Model - Company team members
"""
from datetime import datetime
from enum import Enum
from extensions import db


class EmployeeRole(str, Enum):
    OWNER = 'owner'
    MANAGER = 'manager'
    SALES = 'sales'
    SUPPORT = 'support'
    ADMIN = 'admin'
    GENERAL = 'general'


class Employee(db.Model):
    """Company employee/team member"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Personal Info
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    whatsapp = db.Column(db.String(50), nullable=True)
    
    # Role & Department
    role = db.Column(db.Enum(EmployeeRole), default=EmployeeRole.GENERAL)
    department = db.Column(db.String(100), nullable=True)
    
    # Availability
    is_available = db.Column(db.Boolean, default=True)
    availability_hours = db.Column(db.JSON, default=dict)  # {"mon": {"start": "09:00", "end": "17:00"}, ...}
    
    # Agent can contact this employee
    can_receive_calls = db.Column(db.Boolean, default=True)
    can_receive_messages = db.Column(db.Boolean, default=True)
    can_receive_escalations = db.Column(db.Boolean, default=True)
    
    # Specializations (topics this employee handles)
    specializations = db.Column(db.JSON, default=list)  # ["billing", "technical", "sales"]
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    company = db.relationship('Company', back_populates='employees')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'whatsapp': self.whatsapp,
            'role': self.role.value,
            'department': self.department,
            'is_available': self.is_available,
            'availability_hours': self.availability_hours,
            'can_receive_calls': self.can_receive_calls,
            'can_receive_messages': self.can_receive_messages,
            'can_receive_escalations': self.can_receive_escalations,
            'specializations': self.specializations,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Employee {self.name}>'

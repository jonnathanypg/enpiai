"""
Customer Service - Business Logic for Customer Management
"""
from models.customer import Customer
from extensions import db
from sqlalchemy import or_

class CustomerService:
    @staticmethod
    def get_customer(company_id, email=None, phone=None):
        """
        Find a customer by email or phone within a company.
        """
        query = Customer.query.filter_by(company_id=company_id)
        
        if email and phone:
            return query.filter(or_(Customer.email == email, Customer.phone == phone)).first()
        elif email:
            return query.filter_by(email=email).first()
        elif phone:
            return query.filter_by(phone=phone).first()
        return None

    @staticmethod
    def lookup_by_term(company_id, term):
        """
        Flexible search by term (email, phone, or name)
        """
        term = f"%{term}%"
        return Customer.query.filter_by(company_id=company_id).filter(
            or_(
                Customer.email.like(term),
                Customer.phone.like(term),
                Customer.first_name.like(term),
                Customer.last_name.like(term)
            )
        ).limit(5).all()

    @staticmethod
    def upsert_customer(company_id, data):
        """
        Create or Update a customer.
        """
        email = data.get('email')
        phone = data.get('phone')
        
        customer = CustomerService.get_customer(company_id, email, phone)
        
        if not customer:
            customer = Customer(company_id=company_id)
            db.session.add(customer)
        
        # Update fields
        if 'first_name' in data: customer.first_name = data['first_name']
        if 'last_name' in data: customer.last_name = data['last_name']
        if 'email' in data: customer.email = data['email']
        if 'phone' in data: customer.phone = data['phone']
        if 'ident_number' in data: customer.ident_number = data['ident_number']
        if 'city' in data: customer.city = data['city']
        if 'country' in data: customer.country = data['country']
        if 'metadata' in data: customer.customer_metadata = data['metadata']
        
        db.session.commit()
        return customer

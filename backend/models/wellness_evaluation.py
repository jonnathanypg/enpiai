"""
Wellness Evaluation Model - Core Herbalife business feature.
Stores evaluation results (health data, goals, BMI) linked to leads or customers.

Migration Path: Health data is PII — will be encrypted as sovereign blobs.
Anonymized aggregates feed training pipelines for wellness recommendation models.
"""
from datetime import datetime
from extensions import db
from services.encryption_service import EncryptedString, EncryptedJSON


class WellnessEvaluation(db.Model):
    """Wellness evaluation results — the key tool for Herbalife distributors"""
    __tablename__ = 'wellness_evaluations'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)

    # Link to lead or customer (one must be set)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)

    # Personal Data (PHI — encrypted at rest)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    height_cm = db.Column(db.Float, nullable=True)   # Not encrypted to allow BMI calculation
    weight_kg = db.Column(db.Float, nullable=True)   # Not encrypted to allow BMI calculation

    # Calculated
    bmi = db.Column(db.Float, nullable=True)

    # Vital signs (from reference diagnosticador)
    blood_pressure = db.Column(EncryptedString(50), nullable=True)   # e.g. "120/80"
    pulse = db.Column(db.Integer, nullable=True)                     # bpm
    energy_level = db.Column(db.Integer, nullable=True)              # 1-10 scale

    # Symptoms (list of checked symptom labels) — encrypted at rest
    symptoms = db.Column(EncryptedJSON, nullable=True)   # e.g. ["Headache", "Fatigue"]

    # Health & Lifestyle (PHI — encrypted at rest)
    health_conditions = db.Column(EncryptedJSON, nullable=True)   # e.g. ["diabetes", "hypertension"]
    medications = db.Column(EncryptedString(2000), nullable=True)
    allergies = db.Column(EncryptedJSON, nullable=True)

    # Activity Level
    activity_level = db.Column(db.String(50), nullable=True)  # sedentary, light, moderate, active, very_active
    exercise_frequency = db.Column(db.String(100), nullable=True)  # e.g. "3 times per week"

    # Diet
    meals_per_day = db.Column(db.Integer, nullable=True)
    water_intake_liters = db.Column(db.Float, nullable=True)
    diet_description = db.Column(db.Text, nullable=True)

    # Goals
    primary_goal = db.Column(db.String(100), nullable=True)  # weight_loss, energy, nutrition, muscle_gain
    target_weight_kg = db.Column(db.Float, nullable=True)
    motivation = db.Column(db.Text, nullable=True)

    # Sleep
    sleep_hours = db.Column(db.Float, nullable=True)
    sleep_quality = db.Column(db.String(50), nullable=True)  # poor, fair, good, excellent

    # Observations / free-text notes
    observations = db.Column(db.Text, nullable=True)

    # Source
    source = db.Column(db.String(50), default='web_form')  # web_form, conversational, manual

    # AI-generated outputs
    diagnosis = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    recommended_products = db.Column(db.JSON, default=list)

    # PDF report path
    pdf_report_path = db.Column(db.String(500), nullable=True)

    # Relationships
    distributor = db.relationship('Distributor', back_populates='wellness_evaluations')
    lead = db.relationship('Lead', back_populates='wellness_evaluations')
    customer = db.relationship('Customer', back_populates='wellness_evaluations')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_bmi(self):
        """Calculate BMI from height and weight"""
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = self.height_cm / 100
            self.bmi = round(self.weight_kg / (height_m ** 2), 1)
            return self.bmi
        return None

    def get_bmi_category(self):
        """Return BMI category in Spanish"""
        if not self.bmi:
            return None
        if self.bmi < 18.5:
            return 'Bajo peso'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Sobrepeso'
        else:
            return 'Obesidad'

    def _resolve_contact_info(self):
        """Resolve name and email from linked lead or customer."""
        name = None
        email = None
        try:
            if self.lead_id and self.lead:
                first = self.lead.first_name or ''
                last = self.lead.last_name or ''
                name = f"{first} {last}".strip() or None
                email = self.lead.email
            elif self.customer_id and self.customer:
                first = self.customer.first_name or ''
                last = self.customer.last_name or ''
                name = f"{first} {last}".strip() or None
                email = self.customer.email
        except Exception:
            pass
        return name, email

    def to_dict(self):
        contact_name, contact_email = self._resolve_contact_info()
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'lead_id': self.lead_id,
            'customer_id': self.customer_id,
            'contact_name': contact_name,
            'first_name': contact_name,
            'email': contact_email,
            'age': self.age,
            'gender': self.gender,
            'height_cm': self.height_cm,
            'weight_kg': self.weight_kg,
            'bmi': self.bmi,
            'bmi_category': self.get_bmi_category(),
            'blood_pressure': self.blood_pressure,
            'pulse': self.pulse,
            'energy_level': self.energy_level,
            'symptoms': self.symptoms,
            'health_conditions': self.health_conditions,
            'medications': self.medications,
            'allergies': self.allergies,
            'activity_level': self.activity_level,
            'exercise_frequency': self.exercise_frequency,
            'meals_per_day': self.meals_per_day,
            'water_intake_liters': self.water_intake_liters,
            'diet_description': self.diet_description,
            'primary_goal': self.primary_goal,
            'target_weight_kg': self.target_weight_kg,
            'motivation': self.motivation,
            'sleep_hours': self.sleep_hours,
            'sleep_quality': self.sleep_quality,
            'observations': self.observations,
            'source': self.source,
            'diagnosis': self.diagnosis,
            'recommendations': self.recommendations,
            'recommended_products': self.recommended_products,
            'pdf_report_path': self.pdf_report_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<WellnessEvaluation {self.id}>'

import sys
import logging
from app import create_app
from services.ai_diagnostic_service import generate_diagnosis

logging.basicConfig(level=logging.DEBUG)

app = create_app()
with app.app_context():
    result = generate_diagnosis(
        age=35,
        weight_kg=68,
        height_cm=162,
        blood_pressure="120/80",
        pulse=72,
        energy_level=5,
        symptoms=["Tos persistente"],
        language="es"
    )
    print("\nFINAL RESULT:", result)

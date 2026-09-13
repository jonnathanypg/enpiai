"""
AI Diagnostic Service — Generates wellness diagnoses and recommendations
using the LLM SkillAdapter (multi-provider failover) with robust fallback.
"""
import logging
from typing import Dict, Any, Optional, List
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------
SYSTEM_DIAGNOSIS_ALL = (
    "Eres un especialista experto en nutrición celular, metabolismo y bienestar integral para distribuidores independientes de Herbalife. "
    "Tu labor es generar una evaluación clara, profesional, motivadora y empática basada estrictamente en los datos del encuestado. "
    "Debes estructurar tu respuesta en dos secciones claras:\n"
    "1. DIAGNOSTICO: Análisis del IMC, estado metabólico, nivel de energía, sueño y síntomas reportados.\n"
    "2. RECOMENDACIONES: Hábitos diarios, ingesta de agua, actividad física y sugerencia de productos clave (como Batido Fórmula 1, Té Concentrado de Hierbas, Aloe Vera, Proteína Personalizada PPP, Colágeno).\n"
    "Concluye siempre invitando a coordinar el plan directamente con su Coach de Bienestar. "
    "IMPORTANTE: Responde en {language_name}."
)

PROMPT_EVALUATION = """
Analiza los siguientes datos de la persona y genera su diagnóstico y plan nutricional recomendado:

**Datos Personales:**
- Edad: {age} años | Género: {gender}
- Altura: {height} m | Peso: {weight} kg | IMC: {bmi} ({bmi_category})
- Presión: {blood_pressure} | Pulso: {pulse} bpm
- Nivel de Energía: {energy_level}/10
- Actividad Física: {activity_level} | Frecuencia: {exercise_frequency}
- Comidas al día: {meals_per_day} | Consumo de Agua: {water_intake} L/día
- Sueño: {sleep_hours}h (Calidad: {sleep_quality})
- Objetivo Principal: {primary_goal}
{target_weight_text}

**Molestias / Síntomas reportados:**
{symptoms_text}

**Observaciones:**
{observations}

Genera un diagnóstico preciso y recomendaciones personalizadas que generen valor, claridad y motivación para comenzar un plan de bienestar.
"""

LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "pt": "Portuguese",
}


class AIDiagnosticService:
    """Service class for generating AI wellness diagnoses and recommendations"""

    @classmethod
    def _generate_fallback(cls, data: Dict[str, Any], lang: str = "es") -> Dict[str, Any]:
        """Generate high-quality rule-based diagnosis & recommendations when LLM is unavailable."""
        age = data.get('age', 30)
        gender = data.get('gender', 'persona')
        bmi = data.get('bmi', 22.0)
        category = data.get('bmi_category', 'normal')
        goal = data.get('primary_goal') or 'mejorar salud y vitalidad'
        energy = data.get('energy_level', 6)
        water = data.get('water_intake_liters', 1.5)
        symptoms = data.get('symptoms') or []

        symptoms_str = ", ".join(symptoms) if isinstance(symptoms, list) and symptoms else "sin síntomas críticos"

        if lang == 'en':
            diagnosis = (
                f"Based on your profile (Age: {age}, BMI: {bmi} - {category}), your current metabolism shows "
                f"an energy rating of {energy}/10 and reported factors including {symptoms_str}. "
                f"Your primary goal to {goal} requires balancing macronutrient intake, optimizing hydration, "
                f"and stabilizing cellular energy throughout the day."
            )
            recommendations = (
                f"1. Nutrition: Replace breakfast with a nutrient-dense Formula 1 Shake + Protein Drink Mix (24g protein).\n"
                f"2. Hydration & Energy: Increase water intake to at least 2.5L daily, supported by Herbal Tea Concentrate & Aloe Vera.\n"
                f"3. Daily Habit: Maintain consistent sleep and active movement. Your wellness coach will personalize your step-by-step program."
            )
            products = [
                {"name": "Formula 1 Nutritional Shake Mix", "reason": "Complete balanced cellular nutrition"},
                {"name": "Herbal Tea Concentrate", "reason": "Thermogenic metabolism & antioxidant support"},
                {"name": "Herbal Aloe Concentrate", "reason": "Digestive health & nutrient absorption"}
            ]
        else:
            cat_es = {
                'underweight': 'Bajo Peso',
                'normal': 'Peso Saludable / Normal',
                'overweight': 'Sobrepeso',
                'obese': 'Obesidad'
            }.get(category, 'Normal')

            diagnosis = (
                f"De acuerdo con tu evaluación (Edad: {age} años, IMC: {bmi} correspondiente a '{cat_es}'), "
                f"tu nivel de energía actual se sitúa en {energy}/10 con factores clave como {symptoms_str}. "
                f"Para alcanzar tu objetivo de '{goal}', tu metabolismo requiere un ajuste en la ingesta proteica "
                f"y una depuración digestiva para maximizar la absorción de nutrientes."
            )
            recommendations = (
                f"1. Desayuno Nutritivo: Inicia tu día con un Batido Nutricional Fórmula 1 + Proteína Personalizada (24g de proteína de alta biodisponibilidad).\n"
                f"2. Hidratación & Energía: Eleva tu consumo de agua a 2.5L diarios incorporando Té Concentrado de Hierbas y Herbal Aloe para acelerar tu metabolismo y desinflamar.\n"
                f"3. Plan Guiado: Tu Coach de Bienestar revisará estos parámetros para estructurar tu plan exacto de comidas y seguimiento semanal."
            )
            products = [
                {"name": "Batido Nutricional Fórmula 1", "reason": "Nutrición celular completa con solo 200 kcal"},
                {"name": "Té Concentrado de Hierbas (Termogénico)", "reason": "Quema de grasa y energía natural"},
                {"name": "Herbal Aloe Concentrado Mango/Original", "reason": "Salud digestiva, limpieza y bienestar intestinal"},
                {"name": "Proteína en Polvo Personalizada (PPP)", "reason": "Mantiene masa muscular y saciedad prolongada"}
            ]

        return {
            "diagnosis": diagnosis,
            "recommendations": recommendations,
            "recommended_products": products
        }

    @classmethod
    def generate_diagnosis(cls, evaluation=None, distributor=None, **kwargs) -> Dict[str, Any]:
        """
        Generate wellness diagnosis and recommendations.
        Accepts either an evaluation model instance or keyword arguments.
        """
        data = {}
        if evaluation is not None:
            if hasattr(evaluation, 'to_dict'):
                data = evaluation.to_dict()
            elif isinstance(evaluation, dict):
                data = dict(evaluation)
            else:
                data = {
                    'age': getattr(evaluation, 'age', None),
                    'gender': getattr(evaluation, 'gender', None),
                    'height_cm': getattr(evaluation, 'height_cm', None),
                    'weight_kg': getattr(evaluation, 'weight_kg', None),
                    'bmi': getattr(evaluation, 'bmi', None),
                    'bmi_category': getattr(evaluation, 'get_bmi_category', lambda: 'normal')(),
                    'blood_pressure': getattr(evaluation, 'blood_pressure', None),
                    'pulse': getattr(evaluation, 'pulse', None),
                    'energy_level': getattr(evaluation, 'energy_level', None),
                    'symptoms': getattr(evaluation, 'symptoms', None),
                    'primary_goal': getattr(evaluation, 'primary_goal', None),
                    'target_weight_kg': getattr(evaluation, 'target_weight_kg', None),
                    'activity_level': getattr(evaluation, 'activity_level', None),
                    'exercise_frequency': getattr(evaluation, 'exercise_frequency', None),
                    'meals_per_day': getattr(evaluation, 'meals_per_day', None),
                    'water_intake_liters': getattr(evaluation, 'water_intake_liters', None),
                    'sleep_hours': getattr(evaluation, 'sleep_hours', None),
                    'sleep_quality': getattr(evaluation, 'sleep_quality', None),
                    'observations': getattr(evaluation, 'observations', None),
                    'language': getattr(evaluation, 'language', 'es'),
                }
        
        # Override with kwargs
        for k, v in kwargs.items():
            if v is not None:
                data[k] = v

        # Normalize defaults
        age = data.get('age') or 30
        weight_kg = float(data.get('weight_kg') or 70.0)
        height_cm = float(data.get('height_cm') or 170.0)
        height_m = height_cm / 100.0 if height_cm > 0 else 1.70
        bmi = data.get('bmi') or (round(weight_kg / (height_m ** 2), 1) if height_m > 0 else 22.0)
        data['bmi'] = bmi
        
        if not data.get('bmi_category'):
            if bmi < 18.5:
                data['bmi_category'] = 'underweight'
            elif bmi < 25.0:
                data['bmi_category'] = 'normal'
            elif bmi < 30.0:
                data['bmi_category'] = 'overweight'
            else:
                data['bmi_category'] = 'obese'

        lang = data.get('language') or (getattr(distributor, 'language', 'es') if distributor else 'es')
        language_name = LANGUAGE_MAP.get(lang, "Spanish")

        symptoms = data.get('symptoms') or []
        symptoms_text = "\n".join(f"- {s}" for s in symptoms) if isinstance(symptoms, list) and symptoms else "- Ninguno reportado"
        
        target_weight = data.get('target_weight_kg')
        target_weight_text = f"- Peso Objetivo: {target_weight} kg" if target_weight else ""

        sys_prompt = SYSTEM_DIAGNOSIS_ALL.format(language_name=language_name)
        user_prompt = PROMPT_EVALUATION.format(
            age=age,
            gender=data.get('gender', 'N/A'),
            height=height_m,
            weight=weight_kg,
            bmi=bmi,
            bmi_category=data.get('bmi_category'),
            blood_pressure=data.get('blood_pressure') or 'Normal',
            pulse=data.get('pulse') or 72,
            energy_level=data.get('energy_level') or 6,
            activity_level=data.get('activity_level') or 'Moderado',
            exercise_frequency=data.get('exercise_frequency') or '2-3 veces/sem',
            meals_per_day=data.get('meals_per_day') or 3,
            water_intake=data.get('water_intake_liters') or 1.5,
            sleep_hours=data.get('sleep_hours') or 7,
            sleep_quality=data.get('sleep_quality') or 'Buena',
            primary_goal=data.get('primary_goal') or 'Bienestar General',
            target_weight_text=target_weight_text,
            symptoms_text=symptoms_text,
            observations=data.get('observations') or 'Sin observaciones adicionales'
        )

        diagnosis = ""
        recommendations = ""
        products = []

        try:
            logger.info("Calling LLM for wellness diagnosis (lang=%s, age=%s, bmi=%s)", lang, age, bmi)
            llm_output = llm_service.generate(
                prompt=user_prompt,
                system_prompt=sys_prompt,
                temperature=0.7,
                max_tokens=1200
            )

            if llm_output and len(llm_output.strip()) > 40:
                # Parse sections if present
                if "RECOMENDACIONES" in llm_output.upper() or "RECOMMENDATIONS" in llm_output.upper():
                    parts = llm_output.split("2." if "2." in llm_output else "RECOMEND")
                    diagnosis = parts[0].replace("1.", "").replace("DIAGNOSTICO:", "").replace("DIAGNÓSTICO:", "").strip()
                    recommendations = ("RECOMEND" + parts[1]).strip() if len(parts) > 1 else llm_output
                else:
                    diagnosis = llm_output
                    recommendations = "Sigue las pautas de hidratación y nutrición celular acordadas con tu Coach."

                products = [
                    {"name": "Batido Nutricional Fórmula 1", "reason": "Nutrición celular completa con proteínas y vitaminas"},
                    {"name": "Té Concentrado de Hierbas", "reason": "Energía natural y soporte termogénico"},
                    {"name": "Herbal Aloe Concentrado", "reason": "Salud digestiva y absorción óptima de nutrientes"},
                    {"name": "Proteína Personalizada en Polvo (PPP)", "reason": "Aporte proteico para saciedad y tono muscular"}
                ]
        except Exception as e:
            logger.error("LLM diagnosis generation failed, using intelligent fallback: %s", e)

        # Apply fallback if LLM output was empty or failed
        if not diagnosis:
            fallback = cls._generate_fallback(data, lang=lang)
            diagnosis = fallback['diagnosis']
            recommendations = fallback['recommendations']
            products = fallback['recommended_products']

        result = {
            "diagnosis": diagnosis,
            "recommendations": recommendations,
            "recommended_products": products
        }

        # If an evaluation model instance was passed, update its fields directly
        if evaluation is not None and hasattr(evaluation, 'diagnosis'):
            evaluation.diagnosis = diagnosis
            evaluation.recommendations = recommendations
            evaluation.recommended_products = products

        return result


# Standalone function for backward compatibility
def generate_diagnosis(*args, **kwargs) -> Dict[str, Any]:
    return AIDiagnosticService.generate_diagnosis(*args, **kwargs)

# Singleton instance
ai_diagnostic_service = AIDiagnosticService()


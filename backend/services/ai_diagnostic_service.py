"""
AI Diagnostic Service — Generates wellness diagnoses and recommendations
using the LLM SkillAdapter (multi-provider failover).

Ported from REFERENCIA/diagnosticador/ai/openaiAPI.js and adapted for
Python + Flask context.

Migration Path: Prompts can be stored in RAG vector DB so each distributor can
customize tone/products. The LLM call itself is provider-agnostic via SkillAdapter.
"""
import logging
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt templates — {placeholders} are filled at call time.
# ---------------------------------------------------------------------------

SYSTEM_DIAGNOSIS = (
    "You are an expert in wellness and nutrition specialized in preliminary "
    "assessments for independent Herbalife distributors. "
    "Provide the diagnosis as a continuous paragraph without bullet points, "
    "lists, or headers. Conclude with a clear recommendation to consult the "
    "prospect's wellness coach or independent Herbalife distributor. "
    "Use the exact data provided — do not invent or modify any values. "
    "IMPORTANT: Respond in {language_name}."
)

SYSTEM_RECOMMENDATIONS = (
    "You are a wellness and Herbalife expert. Provide recommendations in a "
    "single, continuous paragraph — no bullet points, lists, or headers. "
    "Include specific Herbalife product suggestions when relevant. "
    "Finish with a positive and motivating note. "
    "IMPORTANT: Respond in {language_name}."
)

PROMPT_DIAGNOSIS = """
Analyze the following respondent data and provide a detailed diagnosis:

**Respondent Data:**
- Age: {age} years
- Weight: {weight} kg
- Height: {height} m
- BMI: {bmi}
- Blood Pressure: {blood_pressure}
- Pulse: {pulse} bpm
- Energy Level: {energy_level}/10

**Reported Symptoms:**
{symptoms_text}

**Additional Observations:**
{observations}

Include in your diagnosis:
1. Analysis of reported symptoms
2. Possible related conditions
3. Identified risk factors
"""

PROMPT_RECOMMENDATIONS = """
Based on the following diagnosis, provide specific, personalized, and actionable recommendations:

Diagnosis: {diagnosis}

Consider the following when providing recommendations:
1. Base them strictly on the diagnosis and information provided.
2. Address the importance of positive lifestyle, nutrition, and dietary changes.
3. Include recommended eating habits, suggested physical activities, and recommended Herbalife products.
4. Recommend specific Herbalife products for the respondent's needs.
5. The recommendation should create urgency and incentivize the purchase of Herbalife products — be clear and direct.

Present everything in a summarized, compact, personalized, clear, and understandable paragraph.
"""

# ---------------------------------------------------------------------------
# Language map
# ---------------------------------------------------------------------------
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "pt": "Portuguese",
}


def generate_diagnosis(
    *,
    age: int,
    weight_kg: float,
    height_cm: float,
    blood_pressure: str = "N/A",
    pulse: int = 72,
    energy_level: int = 5,
    symptoms: list[str] | None = None,
    observations: str = "",
    language: str = "es",
) -> dict:
    """
    Call the LLM to generate a wellness diagnosis + recommendations.

    Returns:
        dict with keys ``diagnosis`` and ``recommendations`` (plain text).
    """
    height_m = height_cm / 100 if height_cm > 0 else 1
    bmi = round(weight_kg / (height_m ** 2), 2) if height_m > 0 else 0

    symptoms_text = "\n".join(f"- {s}" for s in (symptoms or [])) or "- None reported"
    language_name = LANGUAGE_MAP.get(language, "Spanish")

    # ---- Call 1: Diagnosis ----
    diag_system = SYSTEM_DIAGNOSIS.format(language_name=language_name)
    diag_prompt = PROMPT_DIAGNOSIS.format(
        age=age,
        weight=weight_kg,
        height=height_m,
        bmi=bmi,
        blood_pressure=blood_pressure,
        pulse=pulse,
        energy_level=energy_level,
        symptoms_text=symptoms_text,
        observations=observations or "None",
    )

    logger.info("Generating AI diagnosis (lang=%s, syms=%d)…", language, len(symptoms or []))
    try:
        diagnosis = llm_service.generate(
            prompt=diag_prompt,
            system_prompt=diag_system,
            temperature=0.7,
            max_tokens=800,
        )
    except Exception as e:
        logger.error("AI Diagnosis LLM call failed: %s", e, exc_info=True)
        diagnosis = ""

    if not diagnosis:
        logger.warning("AI Diagnosis returned empty string — check LLM API keys and quota.")

    # ---- Call 2: Recommendations ----
    rec_system = SYSTEM_RECOMMENDATIONS.format(language_name=language_name)
    rec_prompt = PROMPT_RECOMMENDATIONS.format(diagnosis=diagnosis or "No diagnosis available.")

    logger.info("Generating AI recommendations…")
    try:
        recommendations = llm_service.generate(
            prompt=rec_prompt,
            system_prompt=rec_system,
            temperature=0.7,
            max_tokens=800,
        )
    except Exception as e:
        logger.error("AI Recommendations LLM call failed: %s", e, exc_info=True)
        recommendations = ""

    if not recommendations:
        logger.warning("AI Recommendations returned empty string — check LLM API keys and quota.")

    return {
        "diagnosis": diagnosis,
        "recommendations": recommendations,
    }

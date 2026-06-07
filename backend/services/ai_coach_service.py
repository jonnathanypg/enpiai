"""
AI Coach Service - Generates motivational, coaching, and roadmap checks for distributors.
Personalized by success ladder level, country, and rules, with music reprogram playlist links.
"""
import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
from extensions import db
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

# Success Ladder Levels metadata
LEVEL_STEPS = {
    "Distribuidor Independiente": {
        "progress": 10,
        "tasks": ["talk_5_people", "take_product", "exercise_15", "listen_eduardo_salazar", "read_manual_1"],
        "books": ["Los Secretos de la Mente Millonaria - T. Harv Eker", "El Manual de Carreras Herbalife"]
    },
    "Consultor Mayor": {
        "progress": 20,
        "tasks": ["talk_5_people", "take_product", "exercise_15", "listen_eduardo_salazar", "read_manual_1"],
        "books": ["Piense y Hágase Rico - Napoleon Hill", "Manual de Carreras de Herbalife"]
    },
    "Constructor del Éxito": {
        "progress": 30,
        "tasks": ["talk_5_people", "take_product", "exercise_20", "listen_eduardo_salazar", "read_manual_2"],
        "books": ["El Hombre más Rico de Babilonia - George S. Clason"]
    },
    "Productor Calificado": {
        "progress": 40,
        "tasks": ["talk_8_people", "take_product", "exercise_20", "listen_eduardo_salazar", "read_manual_2"],
        "books": ["Cómo ganar amigos e influir sobre las personas - Dale Carnegie"]
    },
    "Supervisor": {
        "progress": 55,
        "tasks": ["talk_10_people", "take_product", "exercise_30", "listen_coaching_audio", "followup_3_leads"],
        "books": ["Padre Rico, Padre Pobre - Robert Kiyosaki", "El Vendedor más Grande del Mundo - Og Mandino"]
    },
    "Equipo del Mundo": {
        "progress": 65,
        "tasks": ["talk_12_people", "take_product", "exercise_30", "listen_coaching_audio", "followup_5_leads"],
        "books": ["Las 21 Leyes Irrefutables del Liderazgo - John C. Maxwell"]
    },
    "Equipo del Mundo Activo": {
        "progress": 75,
        "tasks": ["talk_15_people", "take_product", "exercise_30", "listen_leadership_audio", "followup_5_leads", "train_member_1"],
        "books": ["El Líder que no tenía cargo - Robin Sharma"]
    },
    "GET": {
        "progress": 85,
        "tasks": ["talk_15_people", "take_product", "exercise_45", "listen_leadership_audio", "followup_8_leads", "train_member_1"],
        "books": ["Los 7 Hábitos de la Gente Altamente Efectiva - Stephen Covey"]
    },
    "Equipo de Millonarios": {
        "progress": 92,
        "tasks": ["talk_20_people", "take_product", "exercise_45", "listen_leadership_audio", "followup_10_leads", "train_member_2"],
        "books": ["El Liderazgo al estilo de los Navy SEALs - Jocko Willink"]
    },
    "Equipo del Presidente": {
        "progress": 100,
        "tasks": ["talk_20_people", "take_product", "exercise_60", "listen_leadership_audio", "followup_10_leads", "train_member_2"],
        "books": ["Piense y Hágase Rico - Napoleon Hill", "Liderazgo Avanzado - John C. Maxwell"]
    },
    "Club del Chairman": {
        "progress": 100,
        "tasks": ["talk_20_people", "take_product", "exercise_60", "listen_leadership_audio", "followup_10_leads", "train_member_2"],
        "books": ["Las Leyes del Éxito - Napoleon Hill"]
    },
    "Círculo del Fundador": {
        "progress": 100,
        "tasks": ["talk_20_people", "take_product", "exercise_60", "listen_leadership_audio", "followup_10_leads", "train_member_2"],
        "books": ["Las Leyes del Éxito - Napoleon Hill"]
    }
}

# Task Metadata for translations / labels
TASK_METADATA = {
    "talk_5_people": {"es": "Hablar con 5 personas sobre el producto o negocio", "en": "Talk to 5 people about products or business"},
    "talk_8_people": {"es": "Hablar con 8 personas sobre el producto o negocio", "en": "Talk to 8 people about products or business"},
    "talk_10_people": {"es": "Hablar con 10 personas sobre el producto o negocio", "en": "Talk to 10 people about products or business"},
    "talk_12_people": {"es": "Hablar con 12 personas sobre el producto o negocio", "en": "Talk to 12 people about products or business"},
    "talk_15_people": {"es": "Hablar con 15 personas sobre el producto o negocio", "en": "Talk to 15 people about products or business"},
    "talk_20_people": {"es": "Hablar con 20 personas sobre el producto o negocio", "en": "Talk to 20 people about products or business"},
    "take_product": {"es": "Tomar los productos de Herbalife hoy", "en": "Take Herbalife products today"},
    "exercise_15": {"es": "Hacer 15 minutos de ejercicio", "en": "Do 15 minutes of exercise"},
    "exercise_20": {"es": "Hacer 20 minutos de ejercicio", "en": "Do 20 minutes of exercise"},
    "exercise_30": {"es": "Hacer 30 minutos de ejercicio", "en": "Do 30 minutes of exercise"},
    "exercise_45": {"es": "Hacer 45 minutos de ejercicio", "en": "Do 45 minutes of exercise"},
    "exercise_60": {"es": "Hacer 60 minutos de ejercicio", "en": "Do 60 minutes of exercise"},
    "listen_eduardo_salazar": {"es": "Escuchar una lección de Eduardo Salazar (MentalidadHBL)", "en": "Listen to an Eduardo Salazar lesson (MentalidadHBL)"},
    "listen_coaching_audio": {"es": "Escuchar audiolibros de mentalidad o metafísica (Metafísica HBL)", "en": "Listen to mindset or metaphysics audiobooks (Metafísica HBL)"},
    "listen_leadership_audio": {"es": "Escuchar audios de liderazgo avanzado o ventas", "en": "Listen to advanced leadership or sales audiobooks"},
    "read_manual_1": {"es": "Estudiar 1 página del Manual de Carreras de Herbalife", "en": "Study 1 page of the Herbalife Career Manual"},
    "read_manual_2": {"es": "Estudiar 2 páginas del Manual de Carreras (Venta y Seguimiento)", "en": "Study 2 pages of the Career Manual (Sales and Follow-up)"},
    "followup_3_leads": {"es": "Hacer seguimiento a 3 prospectos o clientes", "en": "Follow up with 3 leads or customers"},
    "followup_5_leads": {"es": "Hacer seguimiento a 5 prospectos o clientes", "en": "Follow up with 5 leads or customers"},
    "followup_8_leads": {"es": "Hacer seguimiento a 8 prospectos o clientes", "en": "Follow up with 8 leads or customers"},
    "followup_10_leads": {"es": "Hacer seguimiento a 10 prospectos o clientes", "en": "Follow up with 10 leads or customers"},
    "train_member_1": {"es": "Dar mentoría o capacitación a 1 miembro de tu equipo", "en": "Mentor or train 1 member of your team"},
    "train_member_2": {"es": "Dar mentoría o capacitación a 2 miembros de tu equipo", "en": "Mentor or train 2 members of your team"},
}

PRESIDENT_TIPS = [
    {"author": "Juan (Equipo del Presidente)", "tip": "Enfócate en construir una base sólida de 20 clientes preferentes activos. Esa es la base de tus regalías."},
    {"author": "María (Círculo de Fundadores)", "tip": "El secreto en Herbalife no es solo reclutar, sino enseñar a tu gente a duplicarse. Si tú sabes hacer una evaluación de bienestar, enseña a tus distribuidores en sus primeras 48 horas."},
    {"author": "Carlos (Equipo GET)", "tip": "Nunca te saltes tu propia disciplina diaria. El club de nutrición o tu flujo web solo funciona si eres constante en las invitaciones. Mínimo 10 invitaciones al día."},
    {"author": "Ana (Equipo de Millonarios)", "tip": "El seguimiento no es para molestar, es para cuidar. Llama a tu cliente en el día 1, 3, 7 y 21. Si tienen resultados con el producto, se convertirán en distribuidores."},
]

class AICoachService:
    @staticmethod
    def get_level_metadata(level: str) -> Dict[str, Any]:
        """Gets tasks, progress, and books for a specific level."""
        return LEVEL_STEPS.get(level, LEVEL_STEPS["Distribuidor Independiente"])

    @staticmethod
    def generate_daily_tasks_checklist(level: str) -> Dict[str, bool]:
        """Generates initial false status checklist for all tasks in a level."""
        meta = LEVEL_STEPS.get(level, LEVEL_STEPS["Distribuidor Independiente"])
        return {task: False for task in meta["tasks"]}

    @staticmethod
    def generate_daily_coach_message(distributor_name: str, language: str = 'es', level: str = 'Distribuidor Independiente', tasks_status: Dict[str, bool] = None) -> str:
        """
        Generates the Morning Coach message (Message 1 of 3) containing motivation and challenges.
        """
        meta = LEVEL_STEPS.get(level, LEVEL_STEPS["Distribuidor Independiente"])
        tasks_list = meta["tasks"]
        books_list = meta["books"]
        
        # Select playlist depending on language
        music_url = "https://www.youtube.com/@billionairesound" if language == 'es' else "https://www.youtube.com/@billionairesplaylist"
        eduardo_salazar_url = "https://www.youtube.com/@MentalidadHBL"
        metafisica_url = "https://www.youtube.com/@audiolibrosdemetafisica"

        # Format tasks text
        tasks_text = ""
        lang_key = 'es' if language == 'es' else 'en'
        for i, t in enumerate(tasks_list, 1):
            label = TASK_METADATA.get(t, {}).get(lang_key, t)
            tasks_text += f"{i}. {label}\n"

        system_prompt = (
            "Eres un Coach Experto en Negocios de Herbalife con más de 10 años de éxito. "
            "Tu misión es guiar a Distribuidores Independientes para que alcancen el siguiente nivel en el Plan de Marketing. "
            "Entiendes profundamente el valor de los Puntos de Volumen (VPs), las Evaluaciones de Bienestar, "
            "el seguimiento a Clientes y la importancia de la duplicación. "
            "Hoy enviarás el MENSAJE DE LA MAÑANA. Debe ser motivador, inspirador, empujarlos a la acción "
            "e incluir los retos que tienen para hoy."
        )

        prompt = (
            f"Distribuidor: {distributor_name}\n"
            f"Nivel actual en la Escalera del Éxito: {level}\n"
            f"Retos del Día:\n{tasks_text}\n"
            f"Libro recomendado del nivel: {', '.join(books_list)}\n"
            f"Música del día para enfoque: {music_url}\n"
            f"Canal recomendado para audiolibros y lecciones de Eduardo Salazar: {eduardo_salazar_url}\n"
            f"Canal recomendado para romper límites mentales (Metafísica): {metafisica_url}\n"
            f"Genera un mensaje matutino muy enérgico y estructurado. Debe mencionar los retos del día "
            f"y sugerir escuchar una lección o música motivacional para reprogramar el termostato financiero."
        )

        try:
            message = llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.85,
                max_tokens=4000
            )
            return message.strip()
        except Exception as e:
            logger.error(f"Error generating morning coach message: {e}")
            return (
                f"🦁 *COACH ENPIAI - RETO DIARIO MATUTINO*\n\n"
                f"¡Buen día, {distributor_name}! Hoy es un gran día para avanzar en la escalera hacia el Equipo del Presidente.\n\n"
                f"*Tus retos para hoy ({level}):*\n{tasks_text}\n"
                f"🎧 Reprograma tu mente hoy con música de enfoque en: {music_url} o estudia en {eduardo_salazar_url}.\n\n"
                f"¡Sal a hablar con la gente y vamos por el 100%! 🔥"
            )

    @staticmethod
    def generate_midday_coach_message(distributor_name: str, language: str = 'es', level: str = 'Distribuidor Independiente', country: str = 'Ecuador') -> str:
        """
        Generates the Mid-day Coach message (Message 2 of 3) containing a specific tip from President's Team and localization checks.
        """
        tip_data = random.choice(PRESIDENT_TIPS)
        
        system_prompt = (
            "Eres un Mentor Coach de Herbalife. Tu objetivo es enviar el MENSAJE DEL MEDIODÍA (2:00 PM) "
            "al distribuidor para ver cómo va con sus retos, aportándole valor con un consejo de un Equipo del Presidente "
            "y personalizando el mensaje al país/región para recordarle seguir las normas éticas locales."
        )

        prompt = (
            f"Distribuidor: {distributor_name}\n"
            f"Nivel actual: {level}\n"
            f"País: {country}\n"
            f"Consejo del Equipo del Presidente: '{tip_data['tip']}' por {tip_data['author']}\n"
            f"Redacta un mensaje de mediodía breve pero de gran impacto. Pregúntale amablemente cómo van sus retos de la mañana, "
            f"dale el consejo de {tip_data['author']} y recuérdale con orgullo que en {country} trabajamos bajo "
            f"las reglas de oro de Herbalife (sin hacer afirmaciones médicas falsas sobre curación de enfermedades)."
        )

        try:
            message = llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=2000
            )
            return message.strip()
        except Exception as e:
            logger.error(f"Error generating midday coach message: {e}")
            return (
                f"🦁 *COACH ENPIAI - SEGUIMIENTO DE MEDIODÍA*\n\n"
                f"¡Hola {distributor_name}! ¿Cómo van tus retos del día? 💪\n\n"
                f"Aquí tienes un tip de *{tip_data['author']}* para hoy:\n"
                f"_\"{tip_data['tip']}\"_\n\n"
                f"Recuerda que en {country} compartimos bienestar con ética y profesionalismo. ¡A por la tarde! 🚀"
            )

    @staticmethod
    def generate_evening_coach_message(distributor_name: str, language: str = 'es', level: str = 'Distribuidor Independiente', tasks_status: Dict[str, bool] = None) -> str:
        """
        Generates the Evening Coach message (Message 3 of 3) prompting the distributor to check off challenges.
        """
        meta = LEVEL_STEPS.get(level, LEVEL_STEPS["Distribuidor Independiente"])
        tasks_list = meta["tasks"]
        
        lang_key = 'es' if language == 'es' else 'en'
        tasks_bullets = ""
        for i, t in enumerate(tasks_list, 1):
            label = TASK_METADATA.get(t, {}).get(lang_key, t)
            status = "✅" if tasks_status and tasks_status.get(t) else "❌"
            tasks_bullets += f"- {label} {status}\n"

        system_prompt = (
            "Eres un Coach Herbalife. Envías el MENSAJE DE CIERRE DEL DÍA (8:00 PM) para revisar y actualizar "
            "el progreso del distribuidor en el plan 0 a 100 hacia el Equipo del Presidente. "
            "Debes incentivarlo a responder indicando qué retos completó hoy para poder actualizar su progreso."
        )

        prompt = (
            f"Distribuidor: {distributor_name}\n"
            f"Nivel: {level}\n"
            f"Estado actual de los retos:\n{tasks_bullets}\n"
            f"Escribe un mensaje de cierre de jornada. Felicítalo por el esfuerzo, y pídele que responda "
            f"por chat indicando el número o nombre del reto que completó hoy (ejemplo: 'completé tomar producto, hablé con 5 personas') "
            f"para que puedas marcárselos como cumplidos y ver cómo sube su termostato del éxito."
        )

        try:
            message = llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.75,
                max_tokens=2000
            )
            return message.strip()
        except Exception as e:
            logger.error(f"Error generating evening coach message: {e}")
            return (
                f"🦁 *COACH ENPIAI - EVALUACIÓN DE LA JORNADA*\n\n"
                f"¡Felicidades por terminar tu día, {distributor_name}!\n\n"
                f"Aquí está el balance de tus retos:\n{tasks_bullets}\n"
                f"Por favor, *respóndeme a este mensaje* indicando cuáles lograste completar hoy para poder actualizar tu progreso en tu panel del 0 al 100. ¡El éxito es diario! 📈✨"
            )

    @staticmethod
    def run_roadmap_research(distributor_id: int) -> Dict[str, Any]:
        """
        Roadmap Researcher Agent:
        Analyzes the distributor's state and database context, simulates checking with registered
        President's Team members, and provides recommendations/milestones to add to the roadmap.
        """
        db.session.rollback() # Database Stability Rule
        from models.distributor import Distributor
        from models.lead import Lead
        from models.customer import Customer

        dist = Distributor.query.get(distributor_id)
        if not dist:
            return {"error": "Distributor not found"}

        # Gather real statistics
        leads_count = Lead.query.filter_by(distributor_id=dist.id).count()
        customers_count = Customer.query.filter_by(distributor_id=dist.id).count()
        level = dist.herbalife_level or "Distribuidor Independiente"
        country = dist.country or "No especificado"

        # Lookup registered Presidents in system (if any, otherwise simulate tips based on standard knowledge)
        presidents_in_system = Distributor.query.filter(
            Distributor.herbalife_level.in_(["Equipo del Presidente", "Club del Chairman", "Círculo del Fundador"])
        ).limit(3).all()

        presidents_info = ""
        if presidents_in_system:
            presidents_info = "Equipos del Presidente registrados en la plataforma: " + ", ".join([p.name for p in presidents_in_system])
        else:
            presidents_info = "No hay otros Presidentes registrados en este servidor local; utilizando base de conocimiento global de President's Team."

        system_prompt = (
            "Eres el Agente Investigador y Validador del Roadmap de Coach EnpiAI. "
            "Tu función es analizar la información actual de un distribuidor, consultar de forma simulada con los Equipos de Presidente "
            "registrados en la plataforma, y proveer un plan estratégico con 3 hitos clave "
            "específicos para ayudar al distribuidor a avanzar en el roadmap del 0 al 100 en su nivel actual."
        )

        prompt = (
            f"Distribuidor: {dist.name}\n"
            f"Nivel actual: {level}\n"
            f"País de operación: {country}\n"
            f"Métricas actuales: {leads_count} prospectos registrados en CRM, {customers_count} clientes.\n"
            f"Contexto de Presidentes: {presidents_info}\n"
            f"Basado en este perfil, redacta un informe corto e inspirador con 3 hitos recomendados para agregar al roadmap de {dist.name}. "
            f"Alinea los consejos al mercado de {country} y las reglas comerciales de Herbalife. Provee los pasos prácticos."
        )

        try:
            advice = llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=4000
            )
            return {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "current_level": level,
                "current_progress": LEVEL_STEPS.get(level, {}).get("progress", 0),
                "analysis": advice.strip()
            }
        except Exception as e:
            logger.error(f"Error running roadmap research: {e}")
            return {
                "success": False,
                "error": str(e)
            }

ai_coach_service = AICoachService()

"""
Response Humanizer Service
Intercepts and rewrites virtual assistant responses to make them feel natural,
concise, and conversational, avoiding message bombardment and repetitiveness.

Migration Path: Local small LLMs (e.g. Llama/Gemma fine-tuned) running on client nodes.
"""
import logging
from models.conversation import Message, MessageRole

logger = logging.getLogger(__name__)

class ResponseHumanizer:
    """
    Socioeconomic / conversational alignment agent.
    Acts as a middleware before sending messages to the client.
    """

    @classmethod
    def humanize(cls, planned_response: str, conversation, distributor) -> str:
        """
        Rewrite planned assistant response using LLM based on recent conversation context.
        """
        from extensions import db
        try:
            db.session.rollback()
        except Exception:
            pass

        # 1. Fetch recent message history (last 5 messages) for context
        recent_messages = []
        try:
            # Query last 5 messages ordered chronologically
            msgs = Message.query.filter_by(conversation_id=conversation.id)\
                                .order_by(Message.created_at.desc())\
                                .limit(5).all()
            msgs.reverse()
            for m in msgs:
                role_name = "Usuario" if m.role == MessageRole.USER else "Asistente (Tú)"
                recent_messages.append(f"{role_name}: {m.content}")
        except Exception as e:
            logger.warning(f"Failed to fetch conversation history for humanizer: {e}")

        history_context = "\n".join(recent_messages) if recent_messages else "No hay historial previo."

        # 2. Build the humanizer prompts
        system_prompt = (
            "Eres el Agente Humanizador en una plataforma multi-agente para distribuidores de bienestar.\n"
            "Tu único trabajo es tomar una respuesta planificada por el asistente virtual y reescribirla "
            "para que suene como un mensaje de WhatsApp enviado por un humano real (cercano, natural y breve).\n\n"
            "REGLAS CRÍTICAS:\n"
            "1. BREVEDAD ABSOLUTA: El mensaje debe ser lo más corto posible (idealmente 1 o 2 frases cortas, menos de 180 caracteres).\n"
            "2. EVITA REDUNDANCIAS: Si en el historial reciente ya saludaste, te presentaste (ej. 'Soy Lady...'), o pediste su nombre, NO lo repitas en este mensaje.\n"
            "3. NO FORMATEES EN EXCESO: Prohibido usar listas largas, viñetas, o múltiples párrafos. Si hay opciones, simplifícalas al máximo.\n"
            "4. MANTÉN ENLACES CLAVE: Si la respuesta planificada contiene un enlace crucial (como el link de la evaluación: https://...), DEBES conservar el enlace exactamente igual en tu respuesta, pero hazlo fluir de forma de conversación natural.\n"
            "5. TONO CERCANO Y CÁLIDO: Usa un español latinoamericano neutro, amable y natural, usando como máximo un emoji amistoso.\n"
            "6. RESPUESTA DIRECTA: Devuelve ÚNICAMENTE el texto humanizado que se enviará al usuario, sin introducciones, explicaciones, ni comillas."
        )

        prompt = (
            f"HISTORIAL DE CONVERSACIÓN RECIENTE:\n"
            f"{history_context}\n\n"
            f"RESPUESTA PLANIFICADA POR EL ASISTENTE (A REESCRIBIR):\n"
            f"\"{planned_response}\"\n\n"
            f"Escribe la versión humanizada corta y natural:"
        )

        try:
            from services.llm_service import llm_service
            provider = distributor.llm_provider or 'openai'
            from config import get_config
            cfg = get_config()
            model = distributor.llm_model or cfg.DEFAULT_LLM_MODEL

            humanized = llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=provider,
                model=model,
                temperature=0.7,
                max_tokens=2000
            )

            result = humanized.strip()
            
            # Clean up potential leading/trailing quotes sometimes returned by LLMs
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1].strip()

            # Basic validation: ensure we didn't strip crucial HTTP links
            if "http" in planned_response and "http" not in result:
                logger.warning("Humanizer stripped a URL from response. Falling back to original planned response.")
                return planned_response

            # If result is empty or too short, fallback
            if not result or len(result) < 3:
                return planned_response

            logger.info(f"[HUMANIZER] Original: '{planned_response[:80]}...' -> Humanized: '{result}'")
            return result

        except Exception as err:
            logger.error(f"Error in ResponseHumanizer: {err}")
            return planned_response

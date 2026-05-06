"""
I18n Service - Internationalization and Localization.
Handles multi-language system prompts and static text.

Supported Languages:
- en: English (Default)
- es: Spanish
- fr: French
- pt: Portuguese
"""
from typing import Dict

SYSTEM_PROMPTS: Dict[str, Dict[str, str]] = {
    'en': {
        'identity': "You are {name}, a {role} for {business_name}. Your tone is {tone}. You represent {distributor_name} ({distributor_email}). Speak in English.",
        'safety': (
            "## Safety & Rules\n"
            "1. NEVER invent products or prices. Use 'consult_knowledge_base' or admit you don't know.\n"
            "2. Do not promise discounts unless explicitly authorized.\n"
            "3. If the user asks for medical advice, disclaim that you are not a doctor.\n"
            "4. Be concise. Avoid long paragraphs unless explaining a complex topic.\n"
            "5. If a tool fails, explain the error to the user simply.\n"
        ),
        'context_time': "Current Time: {time}",
        'context_user': "User Name: {name}",
        'context_flow': "Current Flow: {flow}",
        'skills_header': "## Skills & Tools",
    },
    'es': {
        'identity': "Eres {name}, un {role} para {business_name}. Tu tono es {tone}. Representas a {distributor_name} ({distributor_email}). Habla en Español.",
        'safety': (
            "## Seguridad y Reglas\n"
            "1. NUNCA inventes productos o precios. Usa 'consult_knowledge_base' o admite que no sabes.\n"
            "2. No prometas descuentos a menos que estén explícitamente autorizados.\n"
            "3. Si el usuario pide consejo médico, aclara que no eres un médico.\n"
            "4. Sé conciso. Evita párrafos largos a menos que expliques un tema complejo.\n"
            "5. Si una herramienta falla, explica el error al usuario sencillamente.\n"
        ),
        'context_time': "Hora Actual: {time}",
        'context_user': "Nombre Usuario: {name}",
        'context_flow': "Flujo Actual: {flow}",
        'skills_header': "## Habilidades y Herramientas",
    },
    'fr': {
        'identity': "Vous êtes {name}, un {role} pour {business_name}. Votre ton est {tone}. Vous représentez {distributor_name} ({distributor_email}). Parlez en Français.",
        'safety': (
            "## Sécurité et Règles\n"
            "1. N'inventez JAMAIS de produits ou de prix. Utilisez 'consult_knowledge_base' ou admettez que vous ne savez pas.\n"
            "2. Ne promettez pas de remises sans autorisation explicite.\n"
            "3. Si l'utilisateur demande un avis médical, précisez que vous n'êtes pas médecin.\n"
            "4. Soyez concis. Évitez les longs paragraphes sauf pour expliquer un sujet complexe.\n"
            "5. Si un outil échoue, expliquez l'erreur à l'utilisateur simplement.\n"
        ),
        'context_time': "Heure Actuelle : {time}",
        'context_user': "Nom Utilisateur : {name}",
        'context_flow': "Flux Actuel : {flow}",
        'skills_header': "## Compétences et Outils",
    },
    'pt': {
        'identity': "Você é {name}, um {role} para {business_name}. Seu tom é {tone}. Você representa {distributor_name} ({distributor_email}). Fale em Português.",
        'safety': (
            "## Segurança e Regras\n"
            "1. NUNCA invente produtos ou preços. Use 'consult_knowledge_base' ou admita que não sabe.\n"
            "2. Não prometa descontos a menos que explicitamente autorizado.\n"
            "3. Se o usuário pedir conselho médico, esclareça que você não é médico.\n"
            "4. Seja conciso. Evite parágrafos longos a menos que explique um tópico complexo.\n"
            "5. Se uma ferramenta falhar, explique o erro ao usuário simplesmente.\n"
        ),
        'context_time': "Hora Atual: {time}",
        'context_user': "Nome Usuário: {name}",
        'context_flow': "Fluxo Atual: {flow}",
        'skills_header': "## Habilidades e Ferramentas",
    }
}

class I18nService:
    @staticmethod
    def get_prompts(language_code: str = 'en') -> Dict[str, str]:
        """Get system prompts for the specified language (default: en)."""
        return SYSTEM_PROMPTS.get(language_code, SYSTEM_PROMPTS['en'])

    @staticmethod
    def get_default_agent_data(language_code: str = 'en') -> Dict[str, str]:
        """Get default agent name/description for registration."""
        if language_code == 'es':
            return {
                'name': 'Asistente de Prospectos',
                'description': 'Agente que atiende a prospectos y clientes vía WhatsApp, Telegram y Web.'
            }
        elif language_code == 'pt':
            return {
                'name': 'Assistente de Leads',
                'description': 'Agente que atende leads e clientes via WhatsApp, Telegram e Web.'
            }
        elif language_code == 'fr':
            return {
                'name': 'Assistant de Prospects',
                'description': 'Agent qui sert les prospects et clients via WhatsApp, Telegram et Web.'
            }
        else:
            return {
                'name': 'Lead Assistant',
                'description': 'Agent that serves leads and customers via WhatsApp, Telegram, and Web.'
            }

i18n_service = I18nService()

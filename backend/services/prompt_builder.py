from typing import List, Dict, Any, Optional
from skills import BaseSkill
from services.i18n_service import i18n_service

class SystemPromptBuilder:
    """
    Constructs the system prompt for the AI agent dynamically,
    inspired by OpenClaw's modular system prompt.
    """
    
    def __init__(self, agent_config: Dict[str, Any], distributor: Any):
        self.agent_config = agent_config
        self.distributor = distributor
        self.parts: List[str] = []
        self.skills: List[BaseSkill] = []

    def add_identity(self):
        """Adds the core identity and persona."""
        name = self.agent_config.get('name', 'Herbalife Assistant')
        role = self.agent_config.get('role', 'Virtual Assistant')
        tone = self.agent_config.get('tone', 'Professional and friendly')
        
        # Resolve language (default to English if not set)
        lang = getattr(self.distributor, 'language', 'en') or 'en'
        prompts = i18n_service.get_prompts(lang)
        
        identity = prompts['identity'].format(
            name=name,
            role=role,
            business_name=self.distributor.business_name,
            tone=tone,
            distributor_name=self.distributor.name,
            distributor_email=self.distributor.email
        )
        
        self.parts.append("## Identity")
        self.parts.append(identity)
        return self

    def add_safety_rules(self):
        """Adds critical safety and operational rules."""
        lang = getattr(self.distributor, 'language', 'en') or 'en'
        prompts = i18n_service.get_prompts(lang)
        
        self.parts.append(prompts['safety'])
        return self

    def add_skills(self, skills: List[BaseSkill]):
        """Adds skill-specific instructions and registers them."""
        self.skills.extend(skills)
        
        lang = getattr(self.distributor, 'language', 'en') or 'en'
        prompts = i18n_service.get_prompts(lang)
        
        self.parts.append(prompts['skills_header'])
        for skill in skills:
            addition = skill.get_system_prompt_addition()
            if addition:
                self.parts.append(f"### {skill.name.title()}: {addition}")
        return self

    def add_context(self, context_data: Dict[str, Any]):
        """Adds dynamic context (user info, time, sentiment/identity hints, etc.)."""
        self.parts.append("## Context")
        
        lang = getattr(self.distributor, 'language', 'en') or 'en'
        prompts = i18n_service.get_prompts(lang)
        
        # Time
        if 'current_time' in context_data:
            self.parts.append(prompts['context_time'].format(time=context_data['current_time']))
            
        # User Info
        if 'contact_name' in context_data:
            self.parts.append(prompts['context_user'].format(name=context_data['contact_name']))
            
        if 'contact_phone' in context_data:
            self.parts.append(f"Teléfono Usuario: {context_data['contact_phone']}")
            
        # Extra Context (Flow, etc.)
        if 'flow_context' in context_data:
            self.parts.append(prompts['context_flow'].format(flow=context_data['flow_context']))

        # Phase 9: Sentiment & Identity Hints
        if context_data.get('agent_hints'):
            self.parts.append(f"## Intelligence Hints\n{context_data['agent_hints']}")
            
        # Anonymous Lead Mandate
        if context_data.get('is_anonymous'):
            self.parts.append("## MANDATO DE CAPTURA\nEstás hablando con un usuario anónimo. Tu objetivo principal y mandatorio es solicitarle su nombre "
                              "(y su número de teléfono si no estás en WhatsApp) antes de registrarlo. Ofrece asistencia amable y resuelve sus dudas iniciales, "
                              "pero SIEMPRE invítalo a identificarse. Una vez que te dé sus datos, **USA INMEDIATAMENTE** la herramienta `register_lead` "
                              "para registrarlo en el sistema y continuar la conversación llamándolo por su nombre.")
            
        return self

    def build(self) -> str:
        """Assembles the final system prompt string."""
        return "\n\n".join(self.parts)

from typing import List
from langchain_core.tools import StructuredTool
from flask import g
from .base_skill import BaseSkill

class WellnessSkill(BaseSkill):
    def __init__(self):
        self._name = "wellness"
        self._description = "Provide wellness evaluation links."

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.wellness_evaluation_link,
                name="wellness_evaluation_link",
                description="Returns the link for the public wellness evaluation form."
            ),
            StructuredTool.from_function(
                func=self.get_last_wellness_evaluation,
                name="get_last_wellness_evaluation",
                description="Retrieves the full details and AI diagnosis of the user's latest wellness evaluation."
            )
        ]

    def wellness_evaluation_link(self) -> str:
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: No distributor context found."
            
        dist_id = distributor.herbalife_id or str(distributor.id)
        url = f"https://enpi.click/evaluate/{dist_id}"
        return f"Aquí tienes el link para tu evaluación de bienestar: {url}"

    def get_last_wellness_evaluation(self) -> str:
        from models.wellness_evaluation import WellnessEvaluation
        from models.lead import Lead
        from models.customer import Customer
        from extensions import db, ctx
        import json

        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        conversation_id = getattr(ctx, 'current_conversation_id', None)
        
        if not distributor or not conversation_id:
            return "Error: context missing"

        # Find the lead or customer associated with the current conversation
        from models.conversation import Conversation
        conv = Conversation.query.get(conversation_id)
        if not conv:
            return "Error: conversation not found"

        evaluation = None
        if conv.lead_id:
            evaluation = WellnessEvaluation.query.filter_by(lead_id=conv.lead_id).order_by(WellnessEvaluation.created_at.desc()).first()
        elif conv.customer_id:
            evaluation = WellnessEvaluation.query.filter_by(customer_id=conv.customer_id).order_by(WellnessEvaluation.created_at.desc()).first()

        if not evaluation:
            return "No se encontró ninguna evaluación de bienestar previa para este contacto."

        return json.dumps(evaluation.to_dict())

    def get_system_prompt_addition(self) -> str:
        return "Use 'wellness_evaluation_link' when a user wants to start a health assessment. Use 'get_last_wellness_evaluation' if the user asks for details, summaries, or explanations about their previous results."

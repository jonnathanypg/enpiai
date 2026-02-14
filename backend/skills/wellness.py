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
            )
        ]

    def wellness_evaluation_link(self) -> str:
        distributor = getattr(g, 'current_company', None)
        if not distributor:
            return "Error: No distributor context found."
            
        url = f"https://platform.enpiai.com/wellness/{distributor.id}"
        return f"Here is the link for your wellness evaluation: {url}"

    def get_system_prompt_addition(self) -> str:
        return "Use 'wellness_evaluation_link' when a user wants to start a health assessment."

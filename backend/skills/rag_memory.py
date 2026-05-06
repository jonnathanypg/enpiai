from typing import List
from langchain_core.tools import StructuredTool
from flask import g
from .base_skill import BaseSkill
from services.rag_service import rag_service

class RAGSkill(BaseSkill):
    def __init__(self):
        self._name = "knowledge_base"
        self._description = "Consult the company's internal knowledge base."

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.consult_knowledge_base,
                name="consult_knowledge_base",
                description="Consult internal knowledge base (PDFs, docs) for info about services, products, prices."
            )
        ]

    def consult_knowledge_base(self, query: str) -> str:
        distributor = getattr(g, 'current_company', None)
        if not distributor:
            return "Error: No distributor context found."
            
        results = rag_service.query(query, distributor.id, top_k=3)
        
        if not results:
            return "No information found in the knowledge base."
            
        context_text = "\n\n".join([r['text'] for r in results])
        return f"Information from knowledge base:\n{context_text}"

    def get_system_prompt_addition(self) -> str:
        return "Use 'consult_knowledge_base' to answer questions about products, services, or company policies using the internal docs."

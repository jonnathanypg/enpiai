from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable
from langchain_core.tools import StructuredTool

class BaseSkill(ABC):
    """
    Abstract base class for all EnpiAI Skills.
    A Skill is a collection of tools (capabilities) and their associated prompts/docs.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the skill (e.g., 'calendar', 'rag')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of what this skill does."""
        pass

    @abstractmethod
    def get_tools(self) -> List[StructuredTool]:
        """Returns the list of LangChain tools provided by this skill."""
        pass

    def get_system_prompt_addition(self) -> str:
        """
        Optional: Returns text to be added to the system prompt when this skill is active.
        Useful for specific instructions (e.g., 'When using the calendar...')
        """
        return ""

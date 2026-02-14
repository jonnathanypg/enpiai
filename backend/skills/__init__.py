import importlib
import pkgutil
import inspect
import logging
from typing import Any, Dict, List, Type
from .base_skill import BaseSkill

logger = logging.getLogger(__name__)

class SkillRegistry:
    """
    Registry to discover, load, and manage skills dynamically.
    """
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._loaded = False

    def load_skills(self, package_name: str = 'skills'):
        """
        Discovers and loads all skill classes from the specified package.
        """
        if self._loaded:
            return

        logger.info(f"Loading skills from package: {package_name}")
        
        # Import the package to get its path
        try:
            package = importlib.import_module(package_name)
        except ImportError as e:
            logger.error(f"Could not import skills package {package_name}: {e}")
            return

        # Iterate over modules in the package
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            full_module_name = f"{package_name}.{module_name}"
            try:
                module = importlib.import_module(full_module_name)
                
                # Find BaseSkill subclasses
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseSkill) and 
                        obj is not BaseSkill):
                        
                        # Instantiate and register
                        try:
                            skill_instance = obj()
                            self.register_skill(skill_instance)
                        except Exception as e:
                            logger.error(f"Failed to instantiate skill {name}: {e}")
                            
            except ImportError as e:
                logger.error(f"Failed to import module {full_module_name}: {e}")

        self._loaded = True
        logger.info(f"Loaded {len(self._skills)} skills: {list(self._skills.keys())}")

    def register_skill(self, skill: BaseSkill):
        if skill.name in self._skills:
            logger.warning(f"Overwriting existing skill: {skill.name}")
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> BaseSkill:
        return self._skills.get(name)

    def get_all_skills(self) -> List[BaseSkill]:
        return list(self._skills.values())

    def get_all_tools(self) -> List[Any]:
        """Aggregate tools from all loaded skills."""
        tools = []
        for skill in self._skills.values():
            tools.extend(skill.get_tools())
        return tools

    def get_combined_system_prompts(self) -> str:
        """Aggregate system prompt additions from all loaded skills."""
        prompts = []
        for skill in self._skills.values():
            addition = skill.get_system_prompt_addition()
            if addition:
                prompts.append(f"### {skill.name.title()} Instructions\n{addition}")
        return "\n\n".join(prompts)

# Global Registry Instance
_registry = SkillRegistry()

def get_registry() -> SkillRegistry:
    if not _registry._loaded:
        _registry.load_skills()
    return _registry

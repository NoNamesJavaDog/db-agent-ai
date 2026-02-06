"""
Skill Registry - Central registry for managing skills.
"""
import logging
from typing import Dict, List, Optional

from .models import Skill
from .loader import load_all_skills, load_skill_by_name

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Central registry for managing skills.

    Provides methods for loading, listing, and retrieving skills.
    """

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._loaded = False

    def load(self) -> None:
        """Load all skills from filesystem."""
        self._skills = load_all_skills()
        self._loaded = True
        logger.info(f"Loaded {len(self._skills)} skills")

    def reload(self) -> None:
        """Reload all skills from filesystem."""
        self._skills.clear()
        self.load()

    def get(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name.

        Args:
            name: Skill name

        Returns:
            Skill or None if not found
        """
        if not self._loaded:
            self.load()

        # First check cached skills
        if name in self._skills:
            return self._skills[name]

        # Try to load dynamically (for newly added skills)
        skill = load_skill_by_name(name)
        if skill:
            self._skills[name] = skill
            return skill

        return None

    def list_all(self) -> List[Skill]:
        """
        List all loaded skills.

        Returns:
            List of all skills
        """
        if not self._loaded:
            self.load()
        return list(self._skills.values())

    def list_user_invocable(self) -> List[Skill]:
        """
        List skills that can be invoked by users via /skill-name.

        Returns:
            List of user-invocable skills
        """
        if not self._loaded:
            self.load()
        return [s for s in self._skills.values() if s.is_user_invocable]

    def list_model_invocable(self) -> List[Skill]:
        """
        List skills that can be auto-invoked by AI.

        Returns:
            List of model-invocable skills
        """
        if not self._loaded:
            self.load()
        return [s for s in self._skills.values() if s.is_model_invocable]

    def get_skill_tools(self) -> List[Dict]:
        """
        Convert model-invocable skills to tool definitions.

        Returns:
            List of tool definitions in OpenAI function format
        """
        return [skill.to_tool_definition() for skill in self.list_model_invocable()]

    def get_skill_names(self) -> List[str]:
        """
        Get list of all skill names.

        Returns:
            List of skill names
        """
        if not self._loaded:
            self.load()
        return list(self._skills.keys())

    def get_user_invocable_names(self) -> List[str]:
        """
        Get list of user-invocable skill names (for command completion).

        Returns:
            List of skill names with / prefix
        """
        return [f"/{skill.name}" for skill in self.list_user_invocable()]

    def has_skill(self, name: str) -> bool:
        """
        Check if a skill exists.

        Args:
            name: Skill name

        Returns:
            True if skill exists
        """
        return self.get(name) is not None

    @property
    def count(self) -> int:
        """Get the number of loaded skills."""
        if not self._loaded:
            self.load()
        return len(self._skills)

    def get_skills_prompt(self) -> str:
        """
        Generate skills description text for system prompt.

        Returns:
            Formatted string describing available skills for AI to use
        """
        skills = self.list_model_invocable()
        if not skills:
            return ""

        lines = ["## Available Skills", ""]
        lines.append("The following skills are available. Use them when the user's request matches their purpose:")
        lines.append("")

        for skill in skills:
            lines.append(f"- **skill_{skill.name}**: {skill.description or f'Execute skill: {skill.name}'}")

        return "\n".join(lines)

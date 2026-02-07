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

    def get_skills_prompt(self, language: str = "en") -> str:
        """
        Generate skills description text for system prompt.

        Args:
            language: Language code ("en" or "zh")

        Returns:
            Formatted string describing available skills for AI to use
        """
        skills = self.list_model_invocable()
        if not skills:
            return ""

        if language == "zh":
            lines = [
                "## 可用技能 (Skills) — 重要",
                "",
                "⚠️ **当用户提到\u201cskills\u201d、\u201c技能\u201d或技能名称时，你必须先调用对应的技能工具，不要自行操作！**",
                "",
                "以下技能是专业领域知识模块。当用户的请求涉及某个技能的领域时，你**必须**先调用对应的技能工具（`skill_<名称>`）来获取详细操作指南，然后严格按照返回的指南完成任务。",
                "",
                "**技能使用规则：**",
                "1. 当用户提到某个技能名称，或请求明显属于某技能的领域时，立即调用该技能工具——不要先调用list_tables或其他数据库工具",
                "2. 调用技能工具后，你会收到详细的分步指南，严格按照指南执行",
                "3. 不要在未调用技能的情况下自行猜测操作步骤",
                "",
            ]
        else:
            lines = [
                "## Available Skills — IMPORTANT",
                "",
                "⚠️ **When the user mentions \"skills\", a skill name, or their request matches a skill's domain, you MUST call the skill tool FIRST — do NOT start working on your own!**",
                "",
                "The following skills are specialized domain knowledge modules. When the user's request relates to a skill's domain, you **MUST** call the corresponding skill tool (`skill_<name>`) FIRST to get detailed instructions, then follow those instructions to complete the task.",
                "",
                "**Skill usage rules:**",
                "1. When the user mentions a skill name, or their request clearly falls within a skill's domain, immediately call that skill tool — do NOT call list_tables or other database tools first",
                "2. After calling the skill tool, you will receive step-by-step instructions — follow them strictly",
                "3. Do NOT improvise or guess the steps without calling the skill first",
                "",
            ]

        for skill in skills:
            tool_name = f"skill_{skill.name}"
            desc = skill.description or f"Execute skill: {skill.name}"
            # Extract capability keywords from skill instructions to help
            # the model match user requests to the right skill.
            keywords = self._extract_capability_keywords(skill.instructions)
            if keywords:
                lines.append(f"- **{tool_name}**: {desc}")
                kw_label = "触发关键词" if language == "zh" else "Triggers"
                lines.append(f"  {kw_label}: {keywords}")
            else:
                lines.append(f"- **{tool_name}**: {desc}")

        return "\n".join(lines)

    @staticmethod
    def _extract_capability_keywords(instructions: str) -> str:
        """Extract h3 headings under Capabilities as trigger keywords."""
        import re
        keywords = []
        in_capabilities = False
        for line in instructions.splitlines():
            stripped = line.strip()
            if re.match(r"^##\s+Capabilities", stripped, re.IGNORECASE):
                in_capabilities = True
                continue
            if in_capabilities:
                if re.match(r"^##\s+", stripped) and not re.match(r"^###", stripped):
                    break  # next h2 section
                m = re.match(r"^###\s+\d+\.\s+(.*)", stripped)
                if m:
                    keywords.append(m.group(1).strip())
        return ", ".join(keywords) if keywords else ""

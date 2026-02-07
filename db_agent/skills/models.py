"""
Skills data models - Data structures for skill configuration and skill instances.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SkillConfig:
    """Skill configuration parsed from YAML frontmatter."""

    name: str
    description: str = ""
    disable_model_invocation: bool = False  # Whether to disable AI auto-invocation
    user_invocable: bool = True  # Whether user can invoke via /skill-name
    allowed_tools: List[str] = field(default_factory=list)  # Tools the skill can use
    context: str = "main"  # Context type: main or fork

    @classmethod
    def from_dict(cls, data: dict) -> "SkillConfig":
        """Create SkillConfig from a dictionary (parsed YAML)."""
        # Handle allowed_tools which might be a comma-separated string or list
        allowed_tools = data.get("allowed-tools", data.get("allowed_tools", []))
        if isinstance(allowed_tools, str):
            allowed_tools = [t.strip() for t in allowed_tools.split(",") if t.strip()]

        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            disable_model_invocation=data.get(
                "disable-model-invocation",
                data.get("disable_model_invocation", False)
            ),
            user_invocable=data.get(
                "user-invocable",
                data.get("user_invocable", True)
            ),
            allowed_tools=allowed_tools,
            context=data.get("context", "main"),
        )


@dataclass
class Skill:
    """A loaded skill with its configuration and instructions."""

    config: SkillConfig
    instructions: str  # The markdown content after frontmatter
    source: str  # "personal" or "project"
    path: str  # Full path to SKILL.md file

    @property
    def name(self) -> str:
        """Get the skill name."""
        return self.config.name

    @property
    def description(self) -> str:
        """Get the skill description."""
        return self.config.description

    @property
    def is_user_invocable(self) -> bool:
        """Check if skill can be invoked by user via /skill-name."""
        return self.config.user_invocable

    @property
    def is_model_invocable(self) -> bool:
        """Check if skill can be auto-invoked by AI."""
        return not self.config.disable_model_invocation

    def to_tool_definition(self) -> dict:
        """Convert skill to OpenAI function tool definition format."""
        desc = self.description or f"Execute skill: {self.name}"
        # Enrich description with capability keywords from instructions
        keywords = self._extract_capability_keywords()
        if keywords:
            desc = f"{desc}. Covers: {keywords}"
        return {
            "type": "function",
            "function": {
                "name": f"skill_{self.name}",
                "description": desc,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arguments": {
                            "type": "string",
                            "description": "Arguments to pass to the skill"
                        }
                    }
                }
            }
        }

    def _extract_capability_keywords(self) -> str:
        """Extract h3 headings under Capabilities as trigger keywords."""
        import re
        keywords = []
        in_capabilities = False
        for line in self.instructions.splitlines():
            stripped = line.strip()
            if re.match(r"^##\s+Capabilities", stripped, re.IGNORECASE):
                in_capabilities = True
                continue
            if in_capabilities:
                if re.match(r"^##\s+", stripped) and not re.match(r"^###", stripped):
                    break
                m = re.match(r"^###\s+\d+\.\s+(.*)", stripped)
                if m:
                    keywords.append(m.group(1).strip())
        return ", ".join(keywords) if keywords else ""

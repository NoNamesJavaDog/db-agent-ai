"""
DB-Agent Skills Module

Provides Claude Code compatible skills support:
- Load external skills from ~/.claude/skills/ and .claude/skills/
- Parse SKILL.md files with YAML frontmatter
- Execute skills with variable substitution
"""

from .models import Skill, SkillConfig
from .parser import parse_frontmatter, parse_skill_file
from .loader import load_all_skills, load_skill_by_name, get_skill_paths
from .registry import SkillRegistry
from .executor import SkillExecutor, create_executor

__all__ = [
    # Models
    "Skill",
    "SkillConfig",
    # Parser
    "parse_frontmatter",
    "parse_skill_file",
    # Loader
    "load_all_skills",
    "load_skill_by_name",
    "get_skill_paths",
    # Registry
    "SkillRegistry",
    # Executor
    "SkillExecutor",
    "create_executor",
]

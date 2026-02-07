"""
Skill loader - Load skills from filesystem.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional

from .models import Skill, SkillConfig
from .parser import parse_skill_file

logger = logging.getLogger(__name__)


# Skill search paths in priority order (higher priority first)
SKILL_SEARCH_PATHS = [
    ("personal", os.path.expanduser("~/.claude/skills")),
    ("project", ".claude/skills"),
]


def get_skill_paths() -> List[tuple]:
    """
    Get all skill search paths.

    Returns:
        List of (source, path) tuples
    """
    return SKILL_SEARCH_PATHS.copy()


def find_skill_directories(base_path: str) -> List[str]:
    """
    Find all skill directories under a base path.

    Each skill directory should contain a SKILL.md file.

    Args:
        base_path: Base directory to search

    Returns:
        List of skill directory paths
    """
    if not os.path.exists(base_path):
        return []

    directories = []
    try:
        for entry in os.listdir(base_path):
            skill_dir = os.path.join(base_path, entry)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            if os.path.isdir(skill_dir) and os.path.isfile(skill_file):
                directories.append(skill_dir)
    except (PermissionError, OSError) as e:
        logger.warning(f"Cannot access skill directory {base_path}: {e}")

    return directories


def load_skill_from_directory(skill_dir: str, source: str) -> Optional[Skill]:
    """
    Load a skill from a directory.

    Args:
        skill_dir: Path to skill directory
        source: Source type ("personal" or "project")

    Returns:
        Loaded Skill or None if loading fails
    """
    skill_file = os.path.join(skill_dir, "SKILL.md")

    if not os.path.isfile(skill_file):
        logger.warning(f"SKILL.md not found in {skill_dir}")
        return None

    # Use directory name as default skill name
    default_name = os.path.basename(skill_dir)

    try:
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"Cannot read skill file {skill_file}: {e}")
        return None

    try:
        config_dict, instructions = parse_skill_file(content, default_name)
        config = SkillConfig.from_dict(config_dict)

        # Ensure name is set
        if not config.name:
            config.name = default_name

        return Skill(
            config=config,
            instructions=instructions,
            source=source,
            path=skill_file
        )
    except Exception as e:
        logger.warning(f"Failed to parse skill from {skill_file}: {e}")
        return None


def load_all_skills() -> Dict[str, Skill]:
    """
    Load all skills from all search paths.

    Skills from higher priority paths (personal) override those from
    lower priority paths (project) with the same name.

    Returns:
        Dictionary of skill_name -> Skill
    """
    skills = {}

    # Load in reverse priority order so higher priority overwrites
    for source, base_path in reversed(SKILL_SEARCH_PATHS):
        # Handle relative paths (for project skills)
        if not os.path.isabs(base_path):
            base_path = os.path.abspath(base_path)

        skill_dirs = find_skill_directories(base_path)

        for skill_dir in skill_dirs:
            skill = load_skill_from_directory(skill_dir, source)
            if skill:
                # Higher priority (loaded later) overwrites lower priority
                skills[skill.name] = skill
                logger.debug(f"Loaded skill '{skill.name}' from {skill.path} ({source})")

    return skills


def load_skill_by_name(name: str) -> Optional[Skill]:
    """
    Load a specific skill by name.

    Searches in priority order and returns the first match.

    Args:
        name: Skill name

    Returns:
        Loaded Skill or None if not found
    """
    for source, base_path in SKILL_SEARCH_PATHS:
        if not os.path.isabs(base_path):
            base_path = os.path.abspath(base_path)

        skill_dir = os.path.join(base_path, name)
        if os.path.isdir(skill_dir):
            skill = load_skill_from_directory(skill_dir, source)
            if skill:
                return skill

    return None

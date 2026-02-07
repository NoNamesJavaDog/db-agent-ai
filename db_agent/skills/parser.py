"""
SKILL.md parser - Parse YAML frontmatter and markdown content from SKILL.md files.
"""
import re
from typing import Tuple, Optional, Dict, Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# Regex to match YAML frontmatter
FRONTMATTER_PATTERN = re.compile(
    r'^---\s*\n(.*?)\n---\s*\n',
    re.DOTALL
)


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: The full content of a SKILL.md file

    Returns:
        Tuple of (frontmatter_dict, remaining_content)
    """
    if not YAML_AVAILABLE:
        # Fallback: simple key-value parsing
        return _parse_frontmatter_simple(content)

    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        # No frontmatter found
        return {}, content.strip()

    frontmatter_str = match.group(1)
    remaining = content[match.end():].strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_str)
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError:
        # If YAML parsing fails, try simple parsing
        frontmatter = _parse_simple_yaml(frontmatter_str)

    return frontmatter, remaining


def _parse_frontmatter_simple(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Simple frontmatter parser fallback when PyYAML is not available.

    Args:
        content: The full content of a SKILL.md file

    Returns:
        Tuple of (frontmatter_dict, remaining_content)
    """
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content.strip()

    frontmatter_str = match.group(1)
    remaining = content[match.end():].strip()

    return _parse_simple_yaml(frontmatter_str), remaining


def _parse_simple_yaml(yaml_str: str) -> Dict[str, Any]:
    """
    Simple YAML-like parser for key: value pairs.

    Args:
        yaml_str: YAML-like string content

    Returns:
        Dictionary of parsed values
    """
    result = {}
    for line in yaml_str.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Parse boolean values
            if value.lower() in ('true', 'yes'):
                value = True
            elif value.lower() in ('false', 'no'):
                value = False
            # Remove quotes if present
            elif (value.startswith('"') and value.endswith('"')) or \
                 (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            result[key] = value

    return result


def parse_skill_file(content: str, default_name: str = "") -> Tuple[Dict[str, Any], str]:
    """
    Parse a SKILL.md file and extract configuration and instructions.

    Args:
        content: The full content of the SKILL.md file
        default_name: Default name to use if not specified in frontmatter

    Returns:
        Tuple of (config_dict, instructions)
    """
    config, instructions = parse_frontmatter(content)

    # Set default name if not provided
    if not config.get("name") and default_name:
        config["name"] = default_name

    return config, instructions

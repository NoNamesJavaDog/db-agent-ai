"""
Skill Executor - Execute skills with variable substitution and dynamic commands.
"""
import os
import re
import subprocess
import logging
from typing import Dict, Any, Optional, List

from .models import Skill
from .registry import SkillRegistry

logger = logging.getLogger(__name__)


# Pattern for $ARGUMENTS, $N, $ARGUMENTS[N]
ARGUMENTS_PATTERN = re.compile(r'\$ARGUMENTS(?:\[(\d+)\])?')
NUMBERED_ARG_PATTERN = re.compile(r'\$(\d+)')

# Pattern for ${VAR_NAME} variables
ENV_VAR_PATTERN = re.compile(r'\$\{([A-Z_][A-Z0-9_]*)\}')

# Pattern for dynamic commands !`cmd`
DYNAMIC_CMD_PATTERN = re.compile(r'!`([^`]+)`')


class SkillExecutor:
    """
    Execute skills with variable substitution and optional dynamic commands.
    """

    def __init__(self, registry: SkillRegistry, session_id: Optional[str] = None):
        """
        Initialize the executor.

        Args:
            registry: SkillRegistry instance
            session_id: Current session ID for variable substitution
        """
        self.registry = registry
        self.session_id = session_id

    def execute(
        self,
        skill_name: str,
        arguments: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a skill by name.

        Args:
            skill_name: Name of the skill to execute
            arguments: Arguments passed to the skill
            context: Additional context variables

        Returns:
            Dictionary with status and result/instructions
        """
        skill = self.registry.get(skill_name)
        if not skill:
            return {
                "status": "error",
                "error": f"Skill not found: {skill_name}"
            }

        return self.execute_skill(skill, arguments, context)

    def execute_skill(
        self,
        skill: Skill,
        arguments: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a skill instance.

        Args:
            skill: Skill instance to execute
            arguments: Arguments passed to the skill
            context: Additional context variables

        Returns:
            Dictionary with status and processed instructions
        """
        if context is None:
            context = {}

        try:
            # Process the skill instructions
            instructions = skill.instructions

            # 1. Replace argument variables
            instructions = self._replace_arguments(instructions, arguments)

            # 2. Replace environment-like variables (${VAR})
            instructions = self._replace_env_vars(instructions, context)

            # 3. Execute dynamic commands (!`cmd`)
            instructions = self._execute_dynamic_commands(instructions)

            return {
                "status": "success",
                "skill_name": skill.name,
                "instructions": instructions,
                "source": skill.source,
                "allowed_tools": skill.config.allowed_tools,
            }

        except Exception as e:
            logger.error(f"Error executing skill {skill.name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill_name": skill.name
            }

    def _replace_arguments(self, content: str, arguments: str) -> str:
        """
        Replace argument placeholders in content.

        Supports:
        - $ARGUMENTS - all arguments
        - $ARGUMENTS[N] - Nth argument (0-indexed)
        - $N - Nth argument (1-indexed, Claude Code style)

        Args:
            content: Content with placeholders
            arguments: Arguments string

        Returns:
            Content with placeholders replaced
        """
        # Parse arguments into list
        arg_list = self._parse_arguments(arguments)

        # Replace $ARGUMENTS[N]
        def replace_indexed(match):
            index = match.group(1)
            if index is not None:
                idx = int(index)
                if 0 <= idx < len(arg_list):
                    return arg_list[idx]
                return ""
            return arguments

        content = ARGUMENTS_PATTERN.sub(replace_indexed, content)

        # Replace $N (1-indexed)
        def replace_numbered(match):
            idx = int(match.group(1)) - 1  # Convert to 0-indexed
            if 0 <= idx < len(arg_list):
                return arg_list[idx]
            return ""

        content = NUMBERED_ARG_PATTERN.sub(replace_numbered, content)

        return content

    def _parse_arguments(self, arguments: str) -> List[str]:
        """
        Parse arguments string into list.

        Handles quoted strings and whitespace.

        Args:
            arguments: Arguments string

        Returns:
            List of arguments
        """
        if not arguments:
            return []

        # Simple split by whitespace, respecting quotes
        result = []
        current = []
        in_quote = None

        for char in arguments:
            if in_quote:
                if char == in_quote:
                    in_quote = None
                else:
                    current.append(char)
            elif char in '"\'':
                in_quote = char
            elif char.isspace():
                if current:
                    result.append(''.join(current))
                    current = []
            else:
                current.append(char)

        if current:
            result.append(''.join(current))

        return result

    def _replace_env_vars(self, content: str, context: Dict[str, Any]) -> str:
        """
        Replace ${VAR_NAME} style variables.

        Args:
            content: Content with variables
            context: Context dictionary with variable values

        Returns:
            Content with variables replaced
        """
        # Build environment with session info
        env = {
            "CLAUDE_SESSION_ID": self.session_id or "",
        }
        env.update({k.upper(): str(v) for k, v in context.items()})

        def replace_var(match):
            var_name = match.group(1)
            # First check context, then environment
            if var_name in env:
                return env[var_name]
            return os.environ.get(var_name, "")

        return ENV_VAR_PATTERN.sub(replace_var, content)

    def _execute_dynamic_commands(self, content: str) -> str:
        """
        Execute dynamic commands (!`cmd`) and replace with output.

        Args:
            content: Content with dynamic commands

        Returns:
            Content with commands replaced by output
        """
        def execute_cmd(match):
            cmd = match.group(1)
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
                return result.stdout.strip() if result.returncode == 0 else ""
            except subprocess.TimeoutExpired:
                logger.warning(f"Dynamic command timed out: {cmd}")
                return ""
            except Exception as e:
                logger.warning(f"Dynamic command failed: {cmd} - {e}")
                return ""

        return DYNAMIC_CMD_PATTERN.sub(execute_cmd, content)


def create_executor(registry: SkillRegistry, session_id: Optional[str] = None) -> SkillExecutor:
    """
    Create a SkillExecutor instance.

    Args:
        registry: SkillRegistry instance
        session_id: Optional session ID

    Returns:
        SkillExecutor instance
    """
    return SkillExecutor(registry, session_id)

"""
CLI Shared UI Utilities

Provides console instance and Unicode symbol helpers
shared across CLI command modules.
"""
import sys
from rich.console import Console

# Check if console supports Unicode
def _supports_unicode():
    """Check if the console supports Unicode output"""
    if sys.platform != 'win32':
        return True
    try:
        '✓'.encode(sys.stdout.encoding or 'utf-8')
        return True
    except (UnicodeEncodeError, LookupError):
        return False

_UNICODE_SUPPORT = _supports_unicode()

def sym(unicode_char: str, ascii_fallback: str = '') -> str:
    """Return Unicode symbol or ASCII fallback based on console support"""
    if _UNICODE_SUPPORT:
        return unicode_char
    return ascii_fallback

# Common symbols
SYM_CHECK = lambda: sym('✓', '+')
SYM_CROSS = lambda: sym('✗', 'x')
SYM_BULLET = lambda: sym('●', '*')

# Shared console instance
console = Console()

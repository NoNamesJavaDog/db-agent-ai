"""
Simple encryption utilities for storing sensitive data
Uses base64 encoding with a local machine key for basic obfuscation
Note: This is NOT cryptographically secure, just prevents plain-text storage
"""
import base64
import hashlib
import os
import platform


def _get_machine_key() -> bytes:
    """
    Generate a machine-specific key based on system information.
    This provides basic protection against copying the database to another machine.
    """
    # Combine various system identifiers
    identifiers = [
        platform.node(),           # hostname
        platform.machine(),        # machine type
        os.getenv('USER', os.getenv('USERNAME', 'default'))  # username
    ]

    # Create a consistent hash from identifiers
    combined = '|'.join(identifiers).encode('utf-8')
    return hashlib.sha256(combined).digest()


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR data with key (key is repeated as needed)"""
    key_len = len(key)
    return bytes(data[i] ^ key[i % key_len] for i in range(len(data)))


def encrypt(plain_text: str) -> str:
    """
    Encrypt a string using simple obfuscation.

    Args:
        plain_text: The text to encrypt

    Returns:
        Base64 encoded encrypted string
    """
    if not plain_text:
        return ""

    key = _get_machine_key()
    data = plain_text.encode('utf-8')
    encrypted = _xor_bytes(data, key)
    return base64.b64encode(encrypted).decode('ascii')


def decrypt(encrypted_text: str) -> str:
    """
    Decrypt a string that was encrypted with encrypt().

    Args:
        encrypted_text: Base64 encoded encrypted string

    Returns:
        Original plain text
    """
    if not encrypted_text:
        return ""

    try:
        key = _get_machine_key()
        encrypted = base64.b64decode(encrypted_text.encode('ascii'))
        decrypted = _xor_bytes(encrypted, key)
        return decrypted.decode('utf-8')
    except Exception:
        # If decryption fails, return empty string
        return ""

# app/utils/tokens.py
"""
Token generation utilities for secure, non-guessable URLs.

Used for:
- Anonymous RSVP links for off-platform guests
- Shareable event links
"""

import secrets
import string


def generate_rsvp_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token for RSVP links.
    
    Args:
        length: Token length (default 32 chars = 192 bits entropy)
        
    Returns:
        URL-safe random string
        
    Example:
        >>> generate_rsvp_token()
        'K7mX9pQwR2vN8jL3hF6tY4zA1sD5gH0'
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_short_code(length: int = 8) -> str:
    """
    Generate a shorter code for user-friendly URLs.
    
    Args:
        length: Code length (default 8 chars = 48 bits entropy)
        
    Returns:
        URL-safe random string (lowercase + digits only)
        
    Example:
        >>> generate_short_code()
        'a7k3m9p2'
    """
    # Use only lowercase + digits for readability
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

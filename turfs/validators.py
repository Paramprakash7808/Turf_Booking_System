"""
Validation helpers for TurfBook:
- Email: Must contain '@' and '.' with valid domain syntax.
- Mobile: Must be exactly 10 digits (normalized from +91 / leading zeros).
- Password: Must be at least 8 characters.
- Names & text fields: Sensible lengths and valid characters.
"""
import re
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$'
)

def validate_email_format(email):
    """
    Validates that an email contains '@' and '.', with valid structure.
    Returns: (is_valid: bool, error_message: str | None, cleaned_email: str)
    """
    if not email:
        return False, "Email address is required.", ""
    
    email = email.strip()
    
    if '@' not in email and '.' not in email:
        return False, "Email must contain both '@' and a domain dot '.' (e.g. name@example.com).", email
    elif '@' not in email:
        return False, "Email must contain '@' (e.g. name@example.com).", email
    elif '.' not in email:
        return False, "Email must contain a domain dot '.' (e.g. name@example.com).", email

    parts = email.split('@')
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return False, "Invalid email address format.", email

    domain_part = parts[1]
    if '.' not in domain_part or domain_part.startswith('.') or domain_part.endswith('.'):
        return False, "Email domain must contain a valid dot '.' (e.g. example.com).", email

    if not EMAIL_REGEX.match(email):
        return False, "Please enter a valid email address (e.g. name@example.com).", email

    return True, None, email.lower()


def clean_and_validate_mobile(phone, required=True):
    """
    Validates that a mobile number contains exactly 10 digits.
    Handles optional formatting like '+91', leading '0', spaces, and hyphens.
    Returns: (is_valid: bool, error_message: str | None, cleaned_10_digits: str)
    """
    if not phone or not str(phone).strip():
        if required:
            return False, "Mobile number is required.", ""
        return True, None, ""

    raw = str(phone).strip()
    # Strip spaces, hyphens, parentheses, plus
    digits = re.sub(r'[\s\-\(\)\.]', '', raw)

    if digits.startswith('+91'):
        digits = digits[3:]
    elif digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]

    # Remove any remaining '+' if present
    digits = digits.replace('+', '')

    if not digits.isdigit():
        return False, "Mobile number must contain digits only.", raw

    if len(digits) != 10:
        return False, f"Mobile number must be exactly 10 digits (currently {len(digits)} digits).", raw

    return True, None, digits


def validate_password_rules(password, min_length=8):
    """
    Validates password length (at least 8 characters) and presence.
    Returns: (is_valid: bool, error_message: str | None)
    """
    if not password:
        return False, "Password is required."
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long."

    return True, None


def validate_name(name, field_name="Name", min_length=2, max_length=50, required=True):
    """
    Validates names (letters, spaces, hyphens, apostrophes).
    Returns: (is_valid: bool, error_message: str | None, cleaned_name: str)
    """
    if not name or not str(name).strip():
        if required:
            return False, f"{field_name} is required.", ""
        return True, None, ""

    cleaned = str(name).strip()
    if len(cleaned) < min_length:
        return False, f"{field_name} must be at least {min_length} characters.", cleaned
    if len(cleaned) > max_length:
        return False, f"{field_name} cannot exceed {max_length} characters.", cleaned

    return True, None, cleaned

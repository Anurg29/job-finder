import re
from datetime import datetime
import bcrypt


def hash_password(password: str) -> str:
    """Securely hash a raw password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def validate_registration_input(
    full_name: str,
    mobile_no: str,
    dob: str,
    password: str
) -> tuple[bool, str | None]:
    """
    Validate registration input parameters.
    Returns (is_valid, error_message).
    """
    if not full_name or len(full_name.strip()) < 2:
        return False, "Full name must be at least 2 characters long."

    clean_mobile = re.sub(r"[\s\-\+]", "", mobile_no)
    if not clean_mobile.isdigit() or len(clean_mobile) < 10 or len(clean_mobile) > 15:
        return False, "Mobile number must be between 10 and 15 digits."

    try:
        parsed_dob = datetime.strptime(dob.strip(), "%Y-%m-%d")
        if parsed_dob > datetime.now():
            return False, "Date of birth cannot be in the future."
    except ValueError:
        return False, "Date of birth must follow YYYY-MM-DD format (e.g., 2001-05-15)."

    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."

    return True, None

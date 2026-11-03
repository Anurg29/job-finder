from job_search.auth import hash_password, verify_password, validate_registration_input


def test_password_hashing():
    pw = "SuperSecure@2026"
    hashed = hash_password(pw)
    assert hashed.startswith("$2b$")
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_input_validation():
    ok, err = validate_registration_input("John Doe", "9876543210", "2000-01-01", "validPass123")
    assert ok is True
    assert err is None

    # Invalid mobile
    ok, err = validate_registration_input("John Doe", "123", "2000-01-01", "validPass123")
    assert ok is False
    assert "Mobile number" in (err or "")

    # Invalid DOB
    ok, err = validate_registration_input("John Doe", "9876543210", "invalid-date", "validPass123")
    assert ok is False

    # Short password
    ok, err = validate_registration_input("John Doe", "9876543210", "2000-01-01", "123")
    assert ok is False

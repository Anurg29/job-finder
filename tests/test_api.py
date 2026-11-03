from fastapi.testclient import TestClient
from job_search.api import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Job Search Studio" in response.text


def test_auth_registration_and_login_flow():
    import uuid
    unique_mobile = f"9{uuid.uuid4().int % 1000000000:09d}"
    reg_payload = {
        "full_name": "API Test User",
        "mobile_no": unique_mobile,
        "dob": "1999-12-31",
        "password": "Password#999"
    }

    # Register
    res_reg = client.post("/api/auth/register", json=reg_payload)
    assert res_reg.status_code == 200
    reg_data = res_reg.json()
    assert reg_data["status"] == "success"
    assert reg_data["user"]["mobile_no"] == unique_mobile
    assert "password" not in reg_data["user"]
    assert "password_hash" not in reg_data["user"]

    # Duplicate registration blocked
    res_dup = client.post("/api/auth/register", json=reg_payload)
    assert res_dup.status_code == 400

    # Successful login
    login_payload = {
        "mobile_no": unique_mobile,
        "password": "Password#999"
    }
    res_login = client.post("/api/auth/login", json=login_payload)
    assert res_login.status_code == 200
    assert res_login.json()["status"] == "success"

    # Failed login with wrong password
    bad_login = {
        "mobile_no": unique_mobile,
        "password": "WrongPassword"
    }
    res_bad = client.post("/api/auth/login", json=bad_login)
    assert res_bad.status_code == 401

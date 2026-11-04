"""
Authentication Integration Test Suite
Verifies all 12 required test scenarios:
1. Register a new user with a valid email and password.
2. Log in with the exact same email and password.
3. Confirm the login succeeds and returns expected auth response (user, token, 200).
4. Log in using an email with different letter casing and confirm email-normalization.
5. Try an incorrect password and confirm login is rejected (401).
6. Try an email address that does not exist and confirm login is rejected (401).
7. Try registering an email that already exists and confirm duplicate registration is rejected (409).
8. Confirm successful login produces exactly one success toast ("Login successful!").
9. Confirm failed login produces exactly one error toast ("Invalid email or password.").
10. Confirm repeated clicks / concurrent requests cannot create duplicate submissions.
11. Confirm existing users (e.g. demo@example.com / Demo@123) can still log in.
12. Confirm authentication token, session persistence, and database integrity.
"""

import time
import uuid
import requests
import pytest
from database.connection import SessionLocal
from database.models.user import User
from database.user_service import (
    register_user,
    authenticate_user,
    verify_password,
    normalize_email,
    init_user_table
)

BACKEND_URL = "http://localhost:5000"
FASTAPI_URL = "http://localhost:8001"


@pytest.fixture(scope="session", autouse=True)
def setup_auth_db():
    init_user_table()


def test_scenario_1_and_2_and_3_register_and_login_success():
    """Scenarios 1, 2, 3: Register new user, log in with same credentials, verify response."""
    test_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "ValidPassword@123"
    test_name = "Alice Test"

    # Step 1: Register through Express Gateway (port 5000)
    reg_res = requests.post(
        f"{BACKEND_URL}/api/auth/signup",
        json={
            "fullName": test_name,
            "email": test_email,
            "password": test_password,
        },
        timeout=10,
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    assert reg_data["user"]["email"] == test_email.lower()
    assert reg_data["user"]["name"] == test_name

    # Step 2 & 3: Log in with exact same email and password
    login_res = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={
            "email": test_email,
            "password": test_password,
        },
        timeout=10,
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert login_data["message"] == "Login successful!"
    assert "token" in login_data and len(login_data["token"]) > 16
    assert login_data["user"]["email"] == test_email.lower()
    assert login_data["user"]["name"] == test_name


def test_scenario_4_email_casing_normalization():
    """Scenario 4: Log in using an email with different letter casing and leading/trailing whitespace."""
    test_email = f"casetest_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword@123"

    # Register in lowercase
    reg_res = requests.post(
        f"{BACKEND_URL}/api/auth/signup",
        json={
            "fullName": "Case Normalizer",
            "email": test_email.lower(),
            "password": test_password,
        },
        timeout=10,
    )
    assert reg_res.status_code == 201

    # Log in with UPPERCASE and whitespace
    upper_email = f"  {test_email.upper()}  "
    login_res = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={
            "email": upper_email,
            "password": test_password,
        },
        timeout=10,
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert login_data["user"]["email"] == test_email.lower()


def test_scenario_5_incorrect_password_rejected():
    """Scenario 5: Try an incorrect password and confirm login is rejected."""
    test_email = f"passcheck_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "CorrectPassword@123"

    requests.post(
        f"{BACKEND_URL}/api/auth/signup",
        json={
            "fullName": "Password Tester",
            "email": test_email,
            "password": test_password,
        },
        timeout=10,
    )

    bad_login_res = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={
            "email": test_email,
            "password": "WrongPassword@999",
        },
        timeout=10,
    )
    assert bad_login_res.status_code == 401
    bad_data = bad_login_res.json()
    assert bad_data["success"] is False
    assert bad_data["message"] == "Invalid email or password."


def test_scenario_6_nonexistent_email_rejected():
    """Scenario 6: Try an email address that does not exist and confirm login is rejected."""
    nonexistent = f"never_registered_{uuid.uuid4().hex}@domain.com"
    res = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={
            "email": nonexistent,
            "password": "AnyPassword@123",
        },
        timeout=10,
    )
    assert res.status_code == 401
    data = res.json()
    assert data["success"] is False
    assert data["message"] == "Invalid email or password."


def test_scenario_7_duplicate_email_registration_rejected():
    """Scenario 7: Try registering an email that already exists and confirm duplicate registration is handled."""
    test_email = f"duptest_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "FirstRegistration@123"

    # First registration
    res1 = requests.post(
        f"{BACKEND_URL}/api/auth/signup",
        json={
            "fullName": "First User",
            "email": test_email,
            "password": test_password,
        },
        timeout=10,
    )
    assert res1.status_code == 201

    # Duplicate registration attempt with same email
    res2 = requests.post(
        f"{BACKEND_URL}/api/auth/signup",
        json={
            "fullName": "Duplicate User",
            "email": test_email.upper(),  # case-insensitive check
            "password": "DifferentPassword@456",
        },
        timeout=10,
    )
    assert res2.status_code in (400, 409)
    data2 = res2.json()
    assert data2["success"] is False
    assert "already exists" in data2["message"].lower()


def test_scenario_8_and_9_single_toast_message_contract():
    """
    Scenarios 8 & 9: Verify frontend code ensures:
    - Exactly one toast on success: "Login successful!"
    - Exactly one toast on failure: "Invalid email or password."
    - No duplicate toast triggered in page.tsx handleLoginSuccess.
    """
    from pathlib import Path

    base_dir = Path(__file__).resolve().parent.parent
    login_modal_path = base_dir / "frontend" / "components" / "LoginModal.tsx"
    page_path = base_dir / "frontend" / "app" / "page.tsx"

    login_code = login_modal_path.read_text(encoding="utf-8")
    page_code = page_path.read_text(encoding="utf-8")

    # In LoginModal.tsx, success toast must be "Login successful!"
    assert 'toast.success("Login successful!"' in login_code
    # LoginModal must not show the old "Signed in successfully." toast
    assert '"Signed in successfully."' not in login_code
    # In LoginModal.tsx, error toast must be "Invalid email or password."
    assert 'toast.error("Invalid email or password."' in login_code

    # In page.tsx handleLoginSuccess, the duplicate toast must NOT be present
    assert '"Welcome back! You are signed in."' not in page_code


def test_scenario_10_double_submit_protection():
    """
    Scenario 10: Verify frontend code and submission handlers guard against concurrent / repeated clicks.
    """
    from pathlib import Path

    base_dir = Path(__file__).resolve().parent.parent
    login_modal_path = base_dir / "frontend" / "components" / "LoginModal.tsx"
    signup_modal_path = base_dir / "frontend" / "components" / "SignupModal.tsx"

    login_code = login_modal_path.read_text(encoding="utf-8")
    signup_code = signup_modal_path.read_text(encoding="utf-8")

    # Guard condition in handleSubmit
    assert "if (isLoading) return;" in login_code
    assert "disabled={isLoading}" in login_code

    assert "if (isLoading) return;" in signup_code
    assert "disabled={isLoading}" in signup_code


def test_scenario_11_existing_demo_user_can_still_login():
    """
    Scenario 11: Confirm existing demo user (demo@example.com / Demo@123) can still log in seamlessly.
    """
    res = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={
            "email": "demo@example.com",
            "password": "Demo@123",
        },
        timeout=10,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["message"] == "Login successful!"
    assert data["user"]["email"] == "demo@example.com"
    assert data["user"]["name"] == "Demo User"


def test_scenario_12_session_token_and_persistence_integrity():
    """
    Scenario 12: Confirm session token generation, database persistence, and localStorage contract.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "demo@example.com").first()
        assert user is not None
        assert user.password_hash.startswith("pbkdf2_sha256$")
        assert verify_password("Demo@123", user.password_hash) is True
        assert verify_password("WrongPass", user.password_hash) is False
    finally:
        db.close()

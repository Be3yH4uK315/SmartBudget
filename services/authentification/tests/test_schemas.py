import pytest
from pydantic import ValidationError
from app.schemas import VerifyEmailRequest, CompleteRegistrationRequest
def test_verify_email_request_valid():
    data = {"email": "valid@example.com"}
    model = VerifyEmailRequest(**data)
    assert model.email == "valid@example.com", "Должен принимать valid email"

def test_verify_email_request_invalid_email():
    with pytest.raises(ValidationError) as exc:
        VerifyEmailRequest(email="invalid_email")
    assert "validation error" in str(exc.value), "Должен выбрасывать ошибку для invalid email"

def test_verify_email_request_missing_field():
    with pytest.raises(ValidationError) as exc:
        VerifyEmailRequest()
    assert "required" in str(exc.value), "Должен требовать email"

def test_complete_registration_request_valid():
    data = {
        "email": "test@example.com",
        "name": "Test User",
        "country": "US",
        "token": "valid_token",
        "password": "secure12345",
        "user_agent": "Mozilla/5.0"
    }
    model = CompleteRegistrationRequest(**data)
    assert model.password == "secure12345"
    assert len(model.password) >= 8, "Пароль должен быть min 8"

def test_complete_registration_request_password_too_short():
    data = {"email": "test@example.com", "name": "User", "country": "US", "token": "token", "password": "short", "user_agent": "UA"}
    with pytest.raises(ValidationError):
        CompleteRegistrationRequest(**data)

def test_complete_registration_request_name_too_long():
    data = {"email": "test@example.com", "name": "a" * 256, "country": "US", "token": "token", "password": "secure123", "user_agent": "UA"}
    with pytest.raises(ValidationError):
        CompleteRegistrationRequest(**data)
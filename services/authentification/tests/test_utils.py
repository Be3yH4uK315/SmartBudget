import pytest
from app.utils import parse_device, get_location, hash_token, hash_password, check_password
from unittest.mock import patch

def test_parse_device_valid_desktop():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    result = parse_device(ua)
    assert result == "Other, Windows 10", "Должен правильно парсить десктопный UA"

def test_parse_device_valid_mobile():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    result = parse_device(ua)
    assert result == "iPhone, iOS 14.0", "Должен правильно парсить мобильный UA"

def test_parse_device_empty():
    ua = ""
    result = parse_device(ua)
    assert result == "Other, Other ", "Должен обрабатывать пустой UA как Other"

def test_parse_device_unknown():
    ua = "SomeUnknownAgent/1.0"
    result = parse_device(ua)
    assert result.startswith("Other, Other"), "Должен обрабатывать неизвестный UA"

@patch("os.path.exists", return_value=True)
@patch("app.utils.geoip2.database.Reader")
async def test_get_location_valid_public_ip(mock_reader, mock_exists):
    mock_instance = mock_reader.return_value
    mock_instance.city.return_value.country.name = "United States"
    mock_instance.city.return_value.city.name = "New York"
    result = get_location("8.8.8.8")
    assert result == "United States, New York"

@pytest.mark.asyncio
@patch("app.utils.geoip2.database.Reader")
async def test_get_location_private_ip(mock_reader):
    result = get_location("192.168.1.1")
    assert result == "Local Network", "Должен возвращать 'Local Network' для private IP"
    mock_reader.assert_not_called()

@pytest.mark.asyncio
@patch("app.utils.geoip2.database.Reader")
async def test_get_location_invalid_ip(mock_reader):
    mock_instance = mock_reader.return_value
    mock_instance.city.side_effect = Exception("Invalid IP")
    result = get_location("invalid_ip")
    assert result == "Unknown", "Должен возвращать 'Unknown' для invalid IP"

@pytest.mark.asyncio
@patch("app.utils.geoip2.database.Reader")
async def test_get_location_missing_db(mock_reader):
    with patch("os.path.exists", return_value=False):
        result = get_location("8.8.8.8")
        assert result == "Unknown", "Должен возвращать 'Unknown' если DB не найдена"

def test_hash_token_consistent():
    token = "test_token"
    hash1 = hash_token(token)
    hash2 = hash_token(token)
    expected_hash = hash1
    assert hash1 == hash2 == expected_hash

def test_hash_token_different():
    assert hash_token("token1") != hash_token("token2"), "Разные токены - разные хэши"

def test_hash_token_empty():
    assert hash_token("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "Хэш для пустой строки"

def test_hash_password_and_check_valid():
    pw = "securepassword123"
    hashed = hash_password(pw)
    assert len(hashed) > 0, "Хэш должен быть не пустым"
    assert check_password(pw, hashed) is True, "Должен совпадать с оригинальным паролем"

def test_hash_password_unique_salts():
    pw = "samepassword"
    hash1 = hash_password(pw)
    hash2 = hash_password(pw)
    assert hash1 != hash2, "Хэши должны отличаться из-за разных солей"

def test_check_password_invalid():
    hashed = hash_password("correct")
    assert check_password("wrong", hashed) is False, "Не должен совпадать с неправильным паролем"

def test_check_password_empty():
    hashed = hash_password("")
    assert check_password("", hashed) is True, "Должен работать с пустым паролем (хотя не рекомендуется)"
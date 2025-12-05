import pytest
from app.settings import settings, Settings
from unittest.mock import patch
from pydantic import ValidationError
import os
from functools import lru_cache

@patch("app.settings.Path.read_text")
def test_jwt_keys_cached(mock_read):
    mock_read.side_effect = ["private_key_content", "public_key_content"]
    
    if 'jwt_private_key' in settings.__dict__:
        del settings.__dict__['jwt_private_key']
    if 'jwt_public_key' in settings.__dict__:
        del settings.__dict__['jwt_public_key']

    with patch.dict(os.environ, {
        "DB_URL": "...", 
        "KAFKA_BOOTSTRAP_SERVERS": "...", 
        "REDIS_URL": "...", 
        "SMTP_HOST": "...", 
        "GEOIP_DB_PATH": "..."
    }):
        test_settings = Settings()

        assert test_settings.jwt_private_key == "private_key_content", "Private key loaded"
        assert test_settings.jwt_public_key == "public_key_content", "Public key loaded"
        assert mock_read.call_count == 2, "Loaded once"
        
        _ = test_settings.jwt_private_key
        _ = test_settings.jwt_public_key
        assert mock_read.call_count == 2, "Cached, no reload"

@patch.dict(os.environ, clear=True)
@patch("app.settings.env_file_path", "/nonexistent.env")
def test_settings_missing_env():
    with pytest.raises(ValidationError):
        Settings()

def test_settings_defaults():
    assert settings.env == 'test', "Default env test"
    assert settings.log_level == "INFO", "Default log level INFO"
    assert settings.jwt_algorithm == "RS256", "Default algorithm"


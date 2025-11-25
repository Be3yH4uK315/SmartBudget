from app.redis_keys import get_verify_email_key, get_reset_password_key, get_login_fail_key

def test_get_verify_email_key_standard():
    assert get_verify_email_key("test@example.com") == "verify:test@example.com", "Стандартный email"

def test_get_verify_email_key_special_chars():
    assert get_verify_email_key("user+tag@example.com") == "verify:user+tag@example.com", "С special chars"

def test_get_verify_email_key_empty():
    assert get_verify_email_key("") == "verify:", "Пустой email"

def test_get_reset_password_key_standard():
    assert get_reset_password_key("reset@example.com") == "reset:reset@example.com"

def test_get_login_fail_key_ipv4():
    assert get_login_fail_key("192.168.1.1") == "fail:192.168.1.1"

def test_get_login_fail_key_ipv6():
    assert get_login_fail_key("2001:db8::1") == "fail:2001:db8::1"

def test_get_login_fail_key_invalid():
    assert get_login_fail_key("invalid_ip") == "fail:invalid_ip", "Любой string принимается"
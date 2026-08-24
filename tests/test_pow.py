import hashlib

from speedtest.pow import _find_nonce


def test_find_nonce_basic():
    challenge = "0009c63f35a24cd402be9f27d6da2769"
    target_hex_chars = 5
    target_zero_str = "00000"

    nonce = _find_nonce(challenge, target_hex_chars, target_zero_str)

    h = hashlib.sha256(f"{challenge}{nonce}".encode()).hexdigest()
    assert h[:target_hex_chars] == target_zero_str


def test_find_nonce_low_difficulty():
    challenge = "abc123"
    target_hex_chars = 1
    target_zero_str = "0"

    nonce = _find_nonce(challenge, target_hex_chars, target_zero_str)

    h = hashlib.sha256(f"{challenge}{nonce}".encode()).hexdigest()
    assert h[0] == "0"


def test_find_nonce_returns_string_compatible():
    challenge = "test_challenge"
    target_hex_chars = 2
    target_zero_str = "00"

    nonce = _find_nonce(challenge, target_hex_chars, target_zero_str)

    h = hashlib.sha256(f"{challenge}{nonce}".encode()).hexdigest()
    assert h[:2] == "00"
    assert isinstance(nonce, int)


def test_pow_difficulty_conversion():
    """difficulty (bits) -> target_hex_chars = ceil(difficulty / 4)"""
    import math

    assert math.ceil(20 / 4) == 5
    assert math.ceil(16 / 4) == 4
    assert math.ceil(1 / 4) == 1
    assert math.ceil(8 / 4) == 2

import hashlib
import json
import math

import httpx

from speedtest import config
from speedtest.client import anti_cache_url


async def solve_pow(client: httpx.AsyncClient) -> bool:
    try:
        resp = await client.get(anti_cache_url(config.POW_PATH))
        resp.raise_for_status()
        data = resp.json()

        challenge = data["challenge"]
        difficulty = int(data["difficulty"])
        token = data["token"]

        target_hex_chars = math.ceil(difficulty / 4)
        target_zero_str = "0" * target_hex_chars

        nonce = _find_nonce(challenge, target_hex_chars, target_zero_str)

        body = json.dumps({"token": token, "nonce": str(nonce)})
        verify_resp = await client.post(
            config.POW_VERIFY_PATH,
            content=body,
            headers={"Content-Type": "text/plain;charset=UTF-8"},
        )
        verify_resp.raise_for_status()
        return True
    except Exception:
        return False


def _find_nonce(challenge: str, target_hex_chars: int, target_zero_str: str) -> int:
    for nonce in range(100_000_000):
        h = hashlib.sha256(f"{challenge}{nonce}".encode()).hexdigest()
        if h[:target_hex_chars] == target_zero_str:
            return nonce
    raise RuntimeError("PoW failed: no valid nonce found")

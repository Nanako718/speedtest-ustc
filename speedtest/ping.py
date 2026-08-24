import time

import httpx

from speedtest import config
from speedtest.client import anti_cache_url
from speedtest.models import SpeedTestState


async def measure_ping(
    client: httpx.AsyncClient,
    state: SpeedTestState,
    count: int = config.PING_COUNT,
) -> tuple[float, float]:
    state.phase = "ping"

    rtts: list[float] = []
    jitter = 0.0
    prev_rtt = 0.0

    consecutive_errors = 0
    for i in range(count):
        try:
            t0 = time.monotonic()
            resp = await client.get(anti_cache_url(config.PING_PATH))
            rtt = (time.monotonic() - t0) * 1000  # ms
            if resp.status_code != 200:
                error_text = resp.text.strip()
                if "not ustc" in error_text.lower():
                    raise ConnectionError("测速服务器拒绝访问：仅限中科大网络使用")
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    raise ConnectionError(f"测速服务器返回错误 (HTTP {resp.status_code})")
                rtt = 9999.0
            else:
                consecutive_errors = 0
        except ConnectionError:
            raise
        except Exception:
            rtt = 9999.0

        rtt = max(rtt, 0.01)
        rtts.append(rtt)

        if i == 0:
            prev_rtt = rtt
            continue

        inst_jitter = abs(rtt - prev_rtt)
        if i == 1:
            jitter = inst_jitter
        else:
            if inst_jitter > jitter:
                jitter = jitter * 0.3 + inst_jitter * 0.7
            else:
                jitter = jitter * 0.8 + inst_jitter * 0.2

        prev_rtt = rtt

        state.ping_ms = round(min(rtts), 2)
        state.jitter_ms = round(jitter, 2)
        state.ping_progress = (i + 1) / count

    ping = round(min(rtts), 2) if rtts else 0.0
    return ping, round(jitter, 2)

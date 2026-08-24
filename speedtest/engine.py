import asyncio
import time

import httpx

from speedtest import config
from speedtest.client import anti_cache_url, init_session, make_client
from speedtest.download import run_download
from speedtest.models import SpeedTestState, TestResult
from speedtest.ping import measure_ping
from speedtest.pow import solve_pow
from speedtest.upload import run_upload


async def get_ip(client: httpx.AsyncClient) -> str:
    resp = await client.get(anti_cache_url(config.GET_IP_PATH + "?cors=true&isp=true"))
    resp.raise_for_status()
    data = resp.json()
    raw = data.get("processedString", "")
    return raw.split(" - ")[0].strip() if " - " in raw else raw


async def run_test(
    ipv6: bool = False,
    duration: float | None = None,
    ping_count: int = config.PING_COUNT,
    state: SpeedTestState | None = None,
) -> TestResult:
    if state is None:
        state = SpeedTestState()

    dl_duration = duration if duration is not None else config.DOWNLOAD_DURATION
    ul_duration = duration if duration is not None else config.UPLOAD_DURATION

    result = TestResult()
    total_start = time.monotonic()

    client = make_client(ipv6=ipv6)
    try:
        # 0. Init session (get ustc=1 cookie)
        state.phase = "ip"
        await init_session(client, ipv6=ipv6)

        # 1. Get IP
        state.phase = "ip"
        try:
            result.ip = await get_ip(client)
            state.client_ip = result.ip
        except Exception:
            result.ip = "未知"

        # 2. PoW
        state.phase = "pow"
        await solve_pow(client)

        # 3. Ping
        result.ping, result.jitter = await measure_ping(client, state, ping_count)

        # 4. Download
        result.download = await run_download(client, state, dl_duration)

        # 5. Upload
        result.upload = await run_upload(client, state, ul_duration)

    finally:
        await client.aclose()

    result.duration = round(time.monotonic() - total_start, 2)
    state.total_duration = result.duration
    state.phase = "done"
    return result

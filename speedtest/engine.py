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


async def query_server_location(server_ip: str) -> tuple[str, str]:
    """Query server IP location via external API. Returns (location, isp)."""
    try:
        url = config.IP_QUERY_URL.format(ip=server_ip)
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                url,
                params={"fields": config.IP_QUERY_FIELDS, "lang": "zh-CN"},
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "success":
                return "", ""

            parts = []
            country = data.get("country", "")
            region = data.get("regionName", "")
            city = data.get("city", "")
            if country:
                parts.append(country)
            if region and region != country:
                parts.append(region)
            if city and city != region:
                parts.append(city)

            location = " · ".join(parts)
            isp = data.get("isp", "")
            return location, isp
    except Exception:
        return "", ""


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
    result.server_ip = config.SERVER_IP
    total_start = time.monotonic()

    client = make_client(ipv6=ipv6)
    try:
        # 0. Init session (get ustc=1 cookie)
        state.phase = "ip"
        await init_session(client, ipv6=ipv6)

        # 1. Get IP + Server location (parallel)
        state.phase = "ip"
        ip_task = asyncio.create_task(get_ip(client))
        loc_task = asyncio.create_task(query_server_location(config.SERVER_IP))

        try:
            result.ip = await ip_task
            state.client_ip = result.ip
        except Exception:
            result.ip = "未知"

        try:
            result.server_location, result.server_isp = await loc_task
        except Exception:
            pass

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

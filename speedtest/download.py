import asyncio
import time

import httpx

from speedtest import config
from speedtest.client import anti_cache_url
from speedtest.models import SpeedTestState


async def run_download(
    client: httpx.AsyncClient,
    state: SpeedTestState,
    duration: float = config.DOWNLOAD_DURATION,
    streams: int = config.DOWNLOAD_STREAMS,
) -> float:
    state.phase = "download"
    state.dl_bytes = 0
    state.dl_speed_mbps = 0.0
    state.dl_progress = 0.0

    tot_loaded = 0
    lock = asyncio.Lock()
    stop_event = asyncio.Event()
    error_count = 0
    MAX_CONSECUTIVE_ERRORS = 10

    async def stream_worker(stream_id: int):
        nonlocal tot_loaded, error_count
        await asyncio.sleep(stream_id * config.STREAM_STAGGER_MS / 1000.0)

        while not stop_event.is_set():
            try:
                url = anti_cache_url(
                    f"{config.DOWNLOAD_PATH}?ckSize={config.CHUNK_SIZE}&cors=true"
                )
                async with client.stream("GET", url) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        error_text = body.decode(errors="ignore").strip()
                        if "not ustc" in error_text.lower():
                            raise ConnectionError(
                                "测速服务器拒绝访问：仅限中科大网络使用"
                            )
                        raise ConnectionError(
                            f"测速服务器返回错误 (HTTP {resp.status_code})"
                        )
                    async for chunk in resp.aiter_bytes(65536):
                        if stop_event.is_set():
                            break
                        async with lock:
                            tot_loaded += len(chunk)
                            error_count = 0
            except ConnectionError:
                raise
            except Exception:
                if stop_event.is_set():
                    break
                error_count += 1
                if error_count >= MAX_CONSECUTIVE_ERRORS:
                    raise ConnectionError("下载测速连续失败，请检查网络连接")
                await asyncio.sleep(0.1)

    tasks = [asyncio.create_task(stream_worker(i)) for i in range(streams)]

    start_time = time.monotonic()
    grace_done = False
    measure_start = 0.0
    bonus_t = 0.0

    try:
        while True:
            await asyncio.sleep(0.1)

            for t in tasks:
                if t.done() and t.exception():
                    exc = t.exception()
                    stop_event.set()
                    raise exc

            now = time.monotonic()
            elapsed = now - start_time

            if not grace_done and elapsed >= config.DOWNLOAD_GRACE_TIME:
                grace_done = True
                measure_start = now
                tot_loaded = 0
                bonus_t = 0.0

            if grace_done:
                m_elapsed = now - measure_start
                if m_elapsed > 0.1:
                    speed_bps = tot_loaded / m_elapsed
                    speed_mbps = (
                        speed_bps * 8 * config.OVERHEAD_COMPENSATION / 1_000_000
                    )
                    state.dl_speed_mbps = round(speed_mbps, 2)
                    state.dl_bytes = tot_loaded
                    state.elapsed_seconds = m_elapsed

                    if config.AUTO_MODE_ENABLED:
                        bonus = min(
                            config.AUTO_BONUS_CAP_MS,
                            5.0 * speed_bps / 100_000,
                        )
                        bonus_t += bonus

                    state.dl_progress = min(1.0, m_elapsed / duration)

                    if (m_elapsed * 1000 + bonus_t) / 1000.0 >= duration:
                        break
            else:
                state.dl_progress = 0.0
    finally:
        stop_event.set()
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    m_elapsed = time.monotonic() - measure_start if grace_done else 0.001
    final_speed = (
        tot_loaded / m_elapsed * 8 * config.OVERHEAD_COMPENSATION / 1_000_000
    )
    state.dl_speed_mbps = round(final_speed, 2)
    state.dl_bytes = tot_loaded
    state.dl_progress = 1.0
    return state.dl_speed_mbps

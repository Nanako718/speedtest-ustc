import asyncio
import os
import time

import httpx

from speedtest import config
from speedtest.client import anti_cache_url
from speedtest.models import SpeedTestState


async def run_upload(
    client: httpx.AsyncClient,
    state: SpeedTestState,
    duration: float = config.UPLOAD_DURATION,
    streams: int = config.UPLOAD_STREAMS,
) -> float:
    state.phase = "upload"
    state.ul_bytes = 0
    state.ul_speed_mbps = 0.0
    state.ul_progress = 0.0

    blob = os.urandom(config.UPLOAD_BLOB_SIZE_MB * 1024 * 1024)

    tot_uploaded = 0
    lock = asyncio.Lock()
    stop_event = asyncio.Event()
    error_count = 0
    MAX_CONSECUTIVE_ERRORS = 10

    async def stream_worker(stream_id: int):
        nonlocal tot_uploaded, error_count
        await asyncio.sleep(stream_id * config.STREAM_STAGGER_MS / 1000.0)

        while not stop_event.is_set():
            try:
                url = anti_cache_url(f"{config.UPLOAD_PATH}?cors=true")
                resp = await client.post(
                    url,
                    content=blob,
                    headers={"Content-Encoding": "identity"},
                )
                if resp.status_code != 200:
                    error_text = resp.text.strip()
                    if "not ustc" in error_text.lower():
                        raise ConnectionError(
                            "请稍后重试"
                        )
                    raise ConnectionError(
                        f"测速服务器返回错误 (HTTP {resp.status_code})"
                    )
                if not stop_event.is_set():
                    async with lock:
                        tot_uploaded += len(blob)
                        error_count = 0
            except ConnectionError:
                raise
            except Exception:
                if stop_event.is_set():
                    break
                error_count += 1
                if error_count >= MAX_CONSECUTIVE_ERRORS:
                    raise ConnectionError("上传测速连续失败，请检查网络连接")
                await asyncio.sleep(0.1)

    tasks = [asyncio.create_task(stream_worker(i)) for i in range(streams)]

    start_time = time.monotonic()
    grace_done = False
    measure_start = 0.0
    grace_uploaded = 0
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

            if not grace_done and elapsed >= config.UPLOAD_GRACE_TIME:
                grace_done = True
                measure_start = now
                grace_uploaded = tot_uploaded
                bonus_t = 0.0

            # 始终更新显示速度（含 grace period）
            if elapsed > 0.1:
                speed_bps = tot_uploaded / elapsed
                speed_mbps = (
                    speed_bps * 8 * config.OVERHEAD_COMPENSATION / 1_000_000
                )
                state.ul_speed_mbps = round(speed_mbps, 2)
                state.ul_bytes = tot_uploaded
                state.elapsed_seconds = elapsed

            if grace_done:
                m_elapsed = now - measure_start
                if m_elapsed > 0.1:
                    if config.AUTO_MODE_ENABLED:
                        measured = tot_uploaded - grace_uploaded
                        speed_bps = measured / m_elapsed
                        bonus = min(
                            config.AUTO_BONUS_CAP_MS,
                            5.0 * speed_bps / 100_000,
                        )
                        bonus_t += bonus

                    state.ul_progress = min(1.0, m_elapsed / duration)

                    if (m_elapsed * 1000 + bonus_t) / 1000.0 >= duration:
                        break
            else:
                state.ul_progress = 0.0
    finally:
        stop_event.set()
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    m_elapsed = time.monotonic() - measure_start if grace_done else 0.001
    measured_uploaded = tot_uploaded - grace_uploaded
    final_speed = (
        measured_uploaded / m_elapsed * 8 * config.OVERHEAD_COMPENSATION / 1_000_000
    )
    state.ul_speed_mbps = round(final_speed, 2)
    state.ul_bytes = tot_uploaded
    state.ul_progress = 1.0
    return state.ul_speed_mbps

import random

import httpx

from speedtest import config


def make_client(ipv6: bool = False) -> httpx.AsyncClient:
    base = config.USTC_BASE_URL_IPV6 if ipv6 else config.USTC_BASE_URL
    return httpx.AsyncClient(
        base_url=base,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
            "Origin": config.USTC_ORIGIN,
            "Referer": f"{config.USTC_ORIGIN}/",
            "Accept": "*/*",
        },
        timeout=httpx.Timeout(config.REQUEST_TIMEOUT),
        limits=httpx.Limits(
            max_connections=config.DOWNLOAD_STREAMS + config.UPLOAD_STREAMS + 4,
            max_keepalive_connections=config.DOWNLOAD_STREAMS + config.UPLOAD_STREAMS + 2,
        ),
        follow_redirects=True,
    )


async def init_session(client: httpx.AsyncClient, ipv6: bool = False) -> None:
    origin = config.USTC_ORIGIN_IPV6 if ipv6 else config.USTC_ORIGIN
    resp = await client.get(f"{origin}/")
    resp.raise_for_status()


def anti_cache_url(path: str) -> str:
    sep = "&" if "?" in path else "?"
    return f"{path}{sep}r={random.random()}"

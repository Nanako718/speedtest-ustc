import argparse
import asyncio
import json
import sys

from rich.console import Console
from rich.live import Live

from speedtest import __version__, config
from speedtest.engine import run_test
from speedtest.models import SpeedTestState
from speedtest.ui import render_live, render_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="speedtest-ustc",
        description="USTC 网络测速工具",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("--time", type=float, default=None, help="测速时长（秒）")
    parser.add_argument("--ping-count", type=int, default=config.PING_COUNT, help="Ping 次数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--simple", action="store_true", help="简单输出")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--ipv4", action="store_true", default=True, help="使用 IPv4")
    parser.add_argument("--ipv6", action="store_true", help="使用 IPv6")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    console = Console()
    state = SpeedTestState()
    use_json = args.json
    use_simple = args.simple
    debug = args.debug
    ipv6 = args.ipv6

    async def run_with_live():
        if use_json or use_simple:
            return await run_test(
                ipv6=ipv6,
                duration=args.time,
                ping_count=args.ping_count,
                state=state,
            )

        with Live(
            render_live(state),
            console=console,
            refresh_per_second=config.UI_REFRESH_FPS,
            transient=True,
        ) as live:
            async def update_ui():
                while state.phase not in ("done", "error"):
                    live.update(render_live(state))
                    await asyncio.sleep(1.0 / config.UI_REFRESH_FPS)
                live.update(render_live(state))

            ui_task = asyncio.create_task(update_ui())

            try:
                result = await run_test(
                    ipv6=ipv6,
                    duration=args.time,
                    ping_count=args.ping_count,
                    state=state,
                )
            except Exception:
                state.phase = "error"
                ui_task.cancel()
                try:
                    await ui_task
                except asyncio.CancelledError:
                    pass
                raise
            else:
                await ui_task
                return result

    try:
        result = asyncio.run(run_with_live())
    except KeyboardInterrupt:
        console.print("\n  测速已取消", style="bold red")
        return 130
    except Exception as e:
        if debug:
            raise
        console.print(f"\n  ✗ 测速失败: {e}", style="bold red")
        console.print("  请检查网络连接后重试。", style="dim")
        return 1

    if use_json:
        output = {
            "server": result.server,
            "server_name": result.server_name,
            "ip": result.ip,
            "server_ip": result.server_ip,
            "server_location": result.server_location,
            "server_isp": result.server_isp,
            "download": result.download,
            "upload": result.upload,
            "ping": result.ping,
            "jitter": result.jitter,
            "duration": result.duration,
            "unit": result.unit,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif use_simple:
        print(f"Ping: {result.ping:.2f} ms")
        print(f"Jitter: {result.jitter:.2f} ms")
        print(f"Download: {result.download:.2f} Mbps")
        print(f"Upload: {result.upload:.2f} Mbps")
    else:
        console.print(render_result(result, state))

    return 0

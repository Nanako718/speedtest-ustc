import argparse
import asyncio
import json
import sys

from rich.console import Console
from rich.live import Live

from speedtest import config
from speedtest.engine import run_test
from speedtest.models import SpeedTestState
from speedtest.ui import render_live, render_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="speedtest",
        description="USTC 网络测速工具",
    )
    sub = parser.add_subparsers(dest="command")

    ustc = sub.add_parser("ustc", help="测速中国科学技术大学")
    ustc.add_argument("--time", type=float, default=None, help="测速时长（秒）")
    ustc.add_argument("--ping-count", type=int, default=config.PING_COUNT, help="Ping 次数")
    ustc.add_argument("--json", action="store_true", help="JSON 输出")
    ustc.add_argument("--simple", action="store_true", help="简单输出")
    ustc.add_argument("--debug", action="store_true", help="调试模式")
    ustc.add_argument("--ipv4", action="store_true", default=True, help="使用 IPv4")
    ustc.add_argument("--ipv6", action="store_true", help="使用 IPv6")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "ustc":
        return run_ustc(args)

    return 0


def run_ustc(args: argparse.Namespace) -> int:
    console = Console()
    state = SpeedTestState()
    use_json = args.json
    use_simple = args.simple
    debug = args.debug
    ipv6 = args.ipv6

    # header is printed as part of the result UI

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

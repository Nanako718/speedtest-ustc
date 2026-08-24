from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from speedtest import config
from speedtest.models import SpeedTestState, TestResult


def format_bytes(n: int) -> str:
    if n >= 1_073_741_824:
        return f"{n / 1_073_741_824:.2f} GB"
    if n >= 1_048_576:
        return f"{n / 1_048_576:.2f} MB"
    if n >= 1024:
        return f"{n / 1024:.2f} KB"
    return f"{n} B"


def mbps_to_mbs(mbps: float) -> float:
    return mbps / 8


def _make_dl_progress() -> Progress:
    return Progress(
        TextColumn("[bold cyan]{task.description:<4}"),
        BarColumn(bar_width=68, style="cyan", finished_style="cyan"),
        TextColumn("{task.fields[speed]:>10}"),
        console=Console(stderr=True),
        transient=True,
    )


def _make_ul_progress() -> Progress:
    return Progress(
        TextColumn("[bold red]{task.description:<4}"),
        BarColumn(bar_width=68, style="red", finished_style="red"),
        TextColumn("{task.fields[speed]:>10}"),
        console=Console(stderr=True),
        transient=True,
    )


def _build_live_table(
    state: SpeedTestState,
    dl_progress: Progress,
    ul_progress: Progress,
) -> Panel:
    dl_speed = state.dl_speed_mbps
    ul_speed = state.ul_speed_mbps
    dl_mbs = mbps_to_mbs(dl_speed)
    ul_mbs = mbps_to_mbs(ul_speed)
    ping = state.ping_ms
    jitter = state.jitter_ms
    dl_prog = state.dl_progress
    ul_prog = state.ul_progress
    phase = state.phase

    if phase in ("ping", "download", "upload", "done") and ping > 0:
        ping_str = f"{ping:.2f} ms"
        jitter_str = f"{jitter:.2f} ms"
    else:
        ping_str = "-- ms"
        jitter_str = "-- ms"

    if phase in ("download", "upload", "done"):
        dl_speed_str = f"{dl_speed:.2f} Mbps"
        dl_mbs_str = f"{dl_mbs:.2f} MB/s"
    else:
        dl_speed_str = "-- Mbps"
        dl_mbs_str = "-- MB/s"

    if phase in ("upload", "done"):
        ul_speed_str = f"{ul_speed:.2f} Mbps"
        ul_mbs_str = f"{ul_mbs:.2f} MB/s"
    else:
        ul_speed_str = "-- Mbps"
        ul_mbs_str = "-- MB/s"

    ping_speed_str = f"[green]{ping_str}[/]" if ping_str != "-- ms" else ping_str
    jitter_speed_str = f"[orange1]{jitter_str}[/]" if jitter_str != "-- ms" else jitter_str

    header = Table(show_header=True, box=None, padding=(0, 2), expand=True)
    header.add_column("下载速度", justify="center", style="bold cyan", ratio=1)
    header.add_column("上传速度", justify="center", style="bold red", ratio=1)
    header.add_column("网络延迟", justify="center", style="bold white", ratio=1)
    header.add_row(
        Text.from_markup(f"[cyan]{dl_speed_str}[/]"),
        Text.from_markup(f"[red]{ul_speed_str}[/]"),
        Text.from_markup(ping_speed_str),
    )
    header.add_row(
        Text.from_markup(f"[cyan]{dl_mbs_str}[/]"),
        Text.from_markup(f"[red]{ul_mbs_str}[/]"),
        Text.from_markup(jitter_speed_str),
    )

    if phase in ("download", "upload", "done"):
        dl_speed_display = f"{dl_speed:.0f} Mbps"
    else:
        dl_speed_display = "-- Mbps"

    if phase == "upload" or phase == "done":
        ul_speed_display = f"{ul_speed:.0f} Mbps"
    else:
        ul_speed_display = "-- Mbps"

    dl_progress.add_task(
        "下载",
        total=100,
        completed=dl_prog * 100,
        speed=dl_speed_display,
    )
    ul_progress.add_task(
        "上传",
        total=100,
        completed=ul_prog * 100,
        speed=ul_speed_display,
    )

    if phase == "download":
        status = f"[cyan]正在下载...[/] [dim]{int(dl_prog * 100)}%[/]"
    elif phase == "upload":
        status = f"[red]正在上传...[/] [dim]{int(ul_prog * 100)}%[/]"
    elif phase == "ping":
        status = "[dim]正在测延迟...[/]"
    elif phase in ("ip", "pow"):
        status = "[dim]正在连接测速服务器...[/]"
    else:
        status = ""

    info = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    info.add_column(ratio=1)
    info.add_column(ratio=1)
    info.add_row(
        f"[dim]测速时间[/] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"[dim]耗时[/]     {state.elapsed_seconds:.1f}s",
    )

    # Show server info as soon as data is available
    if state.client_ip or state.server_ip:
        info.add_row(
            f"[dim]本机IP[/]   {state.client_ip or '...'}",
            f"[dim]机房IP[/]   {state.server_ip or '...'}",
        )
    if state.server_location or state.server_isp:
        info.add_row(
            f"[dim]位置[/]     {state.server_location or '...'}",
            f"[dim]ISP[/]      {state.server_isp or '...'}",
        )

    body = Table(show_header=False, box=None, padding=0, expand=True)
    body.add_column(ratio=1)
    body.add_row(header)
    body.add_row(Text(""))
    body.add_row(dl_progress)
    body.add_row(Text(""))
    body.add_row(ul_progress)
    body.add_row(Text(""))
    body.add_row(info)

    if status:
        body.add_row(Text(""))
        body.add_row(Text.from_markup(status))

    return Panel(
        body,
        title="[bold]网络测速[/]",
        border_style="blue",
        width=90,
    )


def _build_result_panel(
    result: TestResult,
    dl_progress: Progress,
    ul_progress: Progress,
) -> Panel:
    dl_speed = result.download
    ul_speed = result.upload
    dl_mbs = mbps_to_mbs(dl_speed)
    ul_mbs = mbps_to_mbs(ul_speed)
    ping = result.ping
    jitter = result.jitter

    header = Table(show_header=True, box=None, padding=(0, 2), expand=True)
    header.add_column("下载速度", justify="center", style="bold cyan", ratio=1)
    header.add_column("上传速度", justify="center", style="bold red", ratio=1)
    header.add_column("网络延迟", justify="center", style="bold white", ratio=1)
    header.add_row(
        Text.from_markup(f"[cyan]{dl_speed:.2f} Mbps[/]"),
        Text.from_markup(f"[red]{ul_speed:.2f} Mbps[/]"),
        Text.from_markup(f"[green]{ping:.2f} ms[/]"),
    )
    header.add_row(
        Text.from_markup(f"[cyan]{dl_mbs:.2f} MB/s[/]"),
        Text.from_markup(f"[red]{ul_mbs:.2f} MB/s[/]"),
        Text.from_markup(f"[orange1]{jitter:.2f} ms[/]"),
    )

    dl_progress.add_task(
        "下载",
        total=100,
        completed=100,
        speed=f"{dl_speed:.0f} Mbps",
    )
    ul_progress.add_task(
        "上传",
        total=100,
        completed=100,
        speed=f"{ul_speed:.0f} Mbps",
    )

    location_str = result.server_location or "未知"
    isp_str = result.server_isp or ""
    ip_str = result.server_ip or ""

    info = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    info.add_column(ratio=1)
    info.add_column(ratio=1)
    info.add_row(
        f"[dim]测速时间[/] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"[dim]耗时[/]     {result.duration:.2f}s",
    )
    info.add_row(
        f"[dim]本机IP[/]   {result.ip or '未知'}",
        f"[dim]机房IP[/]   {ip_str}",
    )
    if location_str != "未知" or isp_str:
        info.add_row(
            f"[dim]位置[/]     {location_str}",
            f"[dim]ISP[/]      {isp_str}",
        )

    body = Table(show_header=False, box=None, padding=0, expand=True)
    body.add_column(ratio=1)
    body.add_row(header)
    body.add_row(Text(""))
    body.add_row(dl_progress)
    body.add_row(Text(""))
    body.add_row(ul_progress)
    body.add_row(Text(""))
    body.add_row(info)

    return Panel(
        body,
        title="[bold green]\u2713 TEST COMPLETE[/]",
        border_style="green",
        width=90,
    )


def render_live(state: SpeedTestState) -> Panel:
    dl_progress = _make_dl_progress()
    ul_progress = _make_ul_progress()
    return _build_live_table(state, dl_progress, ul_progress)


def render_result(result: TestResult, state: SpeedTestState) -> Panel:
    dl_progress = _make_dl_progress()
    ul_progress = _make_ul_progress()
    return _build_result_panel(result, dl_progress, ul_progress)

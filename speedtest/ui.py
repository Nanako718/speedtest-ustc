from __future__ import annotations

import time
from collections import deque

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from speedtest.models import SpeedTestState, TestResult


# ============================================================
# 基础配置
# ============================================================

console = Console()

MAX_POINTS = 60

DOWNLOAD_COLOR = "blue"
UPLOAD_COLOR = "green"

DOWNLOAD_HEX = "#2997FF"
UPLOAD_HEX = "#30D158"
TEXT_COLOR = "#E5E5EA"
SECONDARY_COLOR = "#8E8E93"


# ============================================================
# 数据模型
# ============================================================

class SpeedData:
    def __init__(self, max_points: int = MAX_POINTS):
        self.max_points = max_points
        self.timestamps: deque[float] = deque(maxlen=max_points)
        self.download: deque[float] = deque(maxlen=max_points)
        self.upload: deque[float] = deque(maxlen=max_points)

    def add(self, timestamp: float, download: float, upload: float):
        self.timestamps.append(timestamp)
        self.download.append(download)
        self.upload.append(upload)

    @property
    def latest_download(self) -> float:
        return self.download[-1] if self.download else 0.0

    @property
    def latest_upload(self) -> float:
        return self.upload[-1] if self.upload else 0.0

    @property
    def peak_download(self) -> float:
        return max(self.download) if self.download else 0.0

    @property
    def peak_upload(self) -> float:
        return max(self.upload) if self.upload else 0.0

    @property
    def elapsed(self) -> float:
        return self.timestamps[-1] if self.timestamps else 0.0

    def clear(self):
        self.timestamps.clear()
        self.download.clear()
        self.upload.clear()


# ============================================================
# 顶部标题
# ============================================================

def build_header(phase: str = "idle") -> Panel:
    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(justify="left", ratio=1)
    table.add_column(justify="right")

    title = Text()
    title.append("◉ ", style=f"bold {DOWNLOAD_HEX}")
    title.append("USTC SpeedTest", style="bold white")
    title.append("  网络测速", style=f"dim {TEXT_COLOR}")

    if phase in ("ip", "pow"):
        status = Text("正在连接测速服务器...", style="dim")
    elif phase == "ping":
        status = Text("正在测延迟...", style="bold #BF5AF2")
    elif phase == "download":
        status = Text("正在下载...", style="bold #2997FF")
    elif phase == "upload":
        status = Text("正在上传...", style="bold #30D158")
    elif phase == "done":
        status = Text("测速完成", style="bold #30D158")
    else:
        status = Text(time.strftime("%Y-%m-%d %H:%M:%S"), style=f"dim {TEXT_COLOR}")

    table.add_row(title, status)

    return Panel(table, border_style="grey30", box=box.ROUNDED, padding=(0, 1))


# ============================================================
# 速度卡片
# ============================================================

def build_speed_panel(
    title: str, value: float, peak: float, color: str, icon: str
) -> Panel:
    table = Table.grid(expand=True)
    table.add_column()

    title_text = Text()
    title_text.append(icon + " ", style=f"bold {color}")
    title_text.append(title, style="bold white")

    speed_text = Text()
    speed_text.append(f"{value:,.2f}", style=f"bold {color}")
    speed_text.append(" Mbps", style=f"{color}")

    peak_text = Text()
    peak_text.append("峰值  ", style="dim")
    peak_text.append(f"{peak:,.2f} Mbps", style=f"dim {color}")

    table.add_row(title_text)
    table.add_row("")
    table.add_row(Align(speed_text, align="left"))
    table.add_row("")
    table.add_row(peak_text)

    return Panel(table, border_style=color, box=box.ROUNDED, padding=(0, 2))


# ============================================================
# 网络指标
# ============================================================

def build_metrics(
    latency: float = 0.0,
    jitter: float = 0.0,
    packet_loss: float = 0.0,
    phase: str = "idle",
) -> Panel:
    table = Table.grid(expand=True, padding=(0, 2))
    table.add_column()

    if phase in ("ping", "download", "upload", "done") and latency > 0:
        latency_str = f"{latency:.2f} ms"
    else:
        latency_str = "-- ms"

    if phase in ("ping", "download", "upload", "done") and jitter > 0:
        jitter_str = f"{jitter:.2f} ms"
    else:
        jitter_str = "-- ms"

    latency_text = Text()
    latency_text.append("延迟  ", style="dim")
    latency_text.append(latency_str, style="bold #BF5AF2")

    jitter_text = Text()
    jitter_text.append("抖动  ", style="dim")
    jitter_text.append(jitter_str, style="bold #FFD60A")

    loss_text = Text()
    loss_text.append("丢包率  ", style="dim")
    loss_text.append(f"{packet_loss:.2f} %", style="bold #FF453A")

    table.add_row(latency_text)
    table.add_row("")
    table.add_row(jitter_text)
    table.add_row("")
    table.add_row(loss_text)

    return Panel(table, border_style="orange1", box=box.ROUNDED, padding=(0, 1))


# ============================================================
# 底部状态 + 网络信息（同一个面板）
# ============================================================

def build_footer(
    data: SpeedData,
    server_name: str = "中国科学技术大学",
    client_ip: str = "",
    server_ip: str = "",
    server_location: str = "",
    server_isp: str = "",
    ip_version: str = "IPv4",
    phase: str = "idle",
) -> Panel:
    table = Table.grid(expand=True, padding=(0, 2))
    table.add_column()
    table.add_column()
    table.add_column()
    table.add_column()

    duration = data.elapsed

    server = Text()
    server.append("测速服务器\n", style="dim")
    server.append(server_name, style="white")

    duration_text = Text()
    duration_text.append("测试时长\n", style="dim")
    duration_text.append(time.strftime("%H:%M:%S", time.gmtime(duration)), style="white")

    ver = Text()
    ver.append("测试类型\n", style="dim")
    ver.append(ip_version, style="white")

    isp = Text()
    isp.append("ISP\n", style="dim")
    isp.append(server_isp or "...", style="white")

    table.add_row(server, duration_text, ver, isp)

    ip = Text()
    ip.append("本机IP\n", style="dim")
    ip.append(client_ip or "...", style="white")

    srv_ip = Text()
    srv_ip.append("机房IP\n", style="dim")
    srv_ip.append(server_ip or "...", style="white")

    loc = Text()
    loc.append("位置\n", style="dim")
    loc.append(server_location or "...", style="white")

    table.add_row(ip, srv_ip, loc, Text(""))

    return Panel(table, border_style="grey30", box=box.ROUNDED, padding=(1, 1))


# ============================================================
# 进度条
# ============================================================

def build_progress(
    dl_progress: float = 0.0,
    ul_progress: float = 0.0,
    phase: str = "idle",
) -> Panel:
    bar_width = 72

    def _bar(progress: float, color: str, label: str) -> Text:
        filled = int(progress * bar_width)
        filled = min(filled, bar_width)

        text = Text()
        text.append(f"{label}  ", style="bold white")
        if filled > 0:
            text.append("━" * filled, style=f"bold {color}")
        if filled < bar_width:
            text.append("╸", style=f"bold {color}")
        if filled + 1 < bar_width:
            text.append("━" * (bar_width - filled - 1), style="dim")
        pct = int(progress * 100)
        text.append(f"  {pct:>3}%", style=f"bold {color}")
        return text

    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column()

    if phase in ("download", "upload", "done"):
        table.add_row(_bar(dl_progress, DOWNLOAD_HEX, "下载"))
        table.add_row("")
        table.add_row(_bar(ul_progress, UPLOAD_HEX, "上传"))
    else:
        table.add_row(_bar(0, DOWNLOAD_HEX, "下载"))
        table.add_row("")
        table.add_row(_bar(0, UPLOAD_HEX, "上传"))

    return Panel(table, border_style="grey30", box=box.ROUNDED, padding=(0, 1))


# ============================================================
# 完整 UI
# ============================================================

def build_ui(
    data: SpeedData,
    latency: float = 0.0,
    jitter: float = 0.0,
    packet_loss: float = 0.0,
    phase: str = "idle",
    server_name: str = "中国科学技术大学",
    client_ip: str = "",
    server_ip: str = "",
    server_location: str = "",
    server_isp: str = "",
    ip_version: str = "IPv4",
    dl_progress: float = 0.0,
    ul_progress: float = 0.0,
) -> Group:
    header = build_header(phase)

    download_panel = build_speed_panel(
        title="下载速度",
        value=data.latest_download,
        peak=data.peak_download,
        color=DOWNLOAD_HEX,
        icon="↓",
    )

    upload_panel = build_speed_panel(
        title="上传速度",
        value=data.latest_upload,
        peak=data.peak_upload,
        color=UPLOAD_HEX,
        icon="↑",
    )

    metrics = build_metrics(latency, jitter, packet_loss, phase)

    speed_table = Table.grid(expand=True)
    speed_table.add_column(ratio=1)
    speed_table.add_column(ratio=1)
    speed_table.add_column(ratio=1)
    speed_table.add_row(download_panel, upload_panel, metrics)

    footer = build_footer(
        data,
        server_name=server_name,
        client_ip=client_ip,
        server_ip=server_ip,
        server_location=server_location,
        server_isp=server_isp,
        ip_version=ip_version,
        phase=phase,
    )

    progress = build_progress(
        dl_progress=dl_progress,
        ul_progress=ul_progress,
        phase=phase,
    )

    parts = [header, speed_table, progress, footer]

    return Group(*parts)


# ============================================================
# CLI 桥接：render_live / render_result
# ============================================================

_live_data: SpeedData | None = None
_prev_elapsed: float = 0.0


def _get_live_data() -> SpeedData:
    global _live_data
    if _live_data is None:
        _live_data = SpeedData()
    return _live_data


def render_live(state: SpeedTestState) -> Panel:
    """cli.py 在 Live 循环中反复调用此函数。"""
    global _prev_elapsed

    data = _get_live_data()

    elapsed = state.elapsed_seconds
    if elapsed > _prev_elapsed and state.phase in ("download", "upload"):
        data.add(
            timestamp=elapsed,
            download=state.dl_speed_mbps,
            upload=state.ul_speed_mbps,
        )
        _prev_elapsed = elapsed

    return Panel(
        build_ui(
            data,
            latency=state.ping_ms,
            jitter=state.jitter_ms,
            phase=state.phase,
            server_name="中国科学技术大学",
            client_ip=state.client_ip,
            server_ip=state.server_ip,
            server_location=state.server_location,
            server_isp=state.server_isp,
            ip_version=state.ip_version,
            dl_progress=state.dl_progress,
            ul_progress=state.ul_progress,
        ),
        border_style="blue",
        width=96,
    )


def render_result(result: TestResult, state: SpeedTestState) -> Panel:
    """cli.py 测速完成后调用此函数显示最终结果。"""
    global _live_data, _prev_elapsed

    data = _get_live_data()

    data.add(
        timestamp=result.duration,
        download=result.download,
        upload=result.upload,
    )

    result_ui = build_ui(
        data,
        latency=result.ping,
        jitter=result.jitter,
        phase="done",
        server_name=result.server_name or "中国科学技术大学",
        client_ip=result.ip,
        server_ip=result.server_ip,
        server_location=result.server_location,
        server_isp=result.server_isp,
        ip_version=state.ip_version,
        dl_progress=1.0,
        ul_progress=1.0,
    )

    _live_data = None
    _prev_elapsed = 0.0

    return Panel(
        result_ui,
        title="[bold green]\u2713 TEST COMPLETE[/]",
        border_style="green",
        width=96,
    )

from dataclasses import dataclass, field


@dataclass
class SpeedTestState:
    phase: str = "idle"
    client_ip: str = ""
    server_ip: str = ""
    server_location: str = ""
    server_isp: str = ""
    ping_ms: float = 0.0
    jitter_ms: float = 0.0
    dl_speed_mbps: float = 0.0
    ul_speed_mbps: float = 0.0
    dl_bytes: int = 0
    ul_bytes: int = 0
    dl_progress: float = 0.0
    ul_progress: float = 0.0
    elapsed_seconds: float = 0.0
    error: str = ""
    total_duration: float = 0.0


@dataclass
class TestResult:
    server: str = "中科大"
    server_name: str = "中国科学技术大学"
    ip: str = ""
    server_ip: str = ""
    server_location: str = ""
    server_isp: str = ""
    download: float = 0.0
    upload: float = 0.0
    ping: float = 0.0
    jitter: float = 0.0
    duration: float = 0.0
    unit: str = "Mbps"

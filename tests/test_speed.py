from speedtest import config


def test_download_speed_calculation():
    total_bytes = 125_000_000  # 125 MB in 1 second = ~1000 Mbps
    elapsed = 1.0

    mbps = total_bytes * 8 / elapsed / 1_000_000 * config.OVERHEAD_COMPENSATION
    assert abs(mbps - 1060.0) < 0.01


def test_upload_speed_calculation():
    total_bytes = 50_000_000  # 50 MB in 1 second = ~400 Mbps
    elapsed = 1.0

    mbps = total_bytes * 8 / elapsed / 1_000_000 * config.OVERHEAD_COMPENSATION
    assert abs(mbps - 424.0) < 0.01


def test_overhead_compensation():
    base_mbps = 100.0
    compensated = base_mbps * config.OVERHEAD_COMPENSATION
    assert abs(compensated - 106.0) < 0.001


def test_speed_zero_bytes():
    total_bytes = 0
    elapsed = 1.0
    mbps = total_bytes * 8 / elapsed / 1_000_000 * config.OVERHEAD_COMPENSATION
    assert mbps == 0.0


def test_auto_mode_bonus():
    speed_bps = 125_000_000  # 1 Gbps in bytes/sec
    bonus = min(config.AUTO_BONUS_CAP_MS, 5.0 * speed_bps / 100_000)
    # 5 * 125000000 / 100000 = 6250, capped at 400
    assert bonus == config.AUTO_BONUS_CAP_MS

    speed_bps_slow = 1_000_000  # 8 Mbps
    bonus_slow = min(config.AUTO_BONUS_CAP_MS, 5.0 * speed_bps_slow / 100_000)
    # 5 * 1000000 / 100000 = 50, not capped
    assert bonus_slow == 50.0

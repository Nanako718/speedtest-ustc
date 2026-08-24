from speedtest.ui import format_bytes


def test_format_bytes_gb():
    assert format_bytes(1_073_741_824) == "1.00 GB"
    assert format_bytes(2_147_483_648) == "2.00 GB"


def test_format_bytes_mb():
    assert format_bytes(1_048_576) == "1.00 MB"
    assert format_bytes(104_857_600) == "100.00 MB"


def test_format_bytes_kb():
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(102_400) == "100.00 KB"


def test_format_bytes_b():
    assert format_bytes(100) == "100 B"
    assert format_bytes(0) == "0 B"


def test_mbps_to_mbs():
    from speedtest.ui import mbps_to_mbs
    assert mbps_to_mbs(100) == 12.5
    assert mbps_to_mbs(0) == 0.0

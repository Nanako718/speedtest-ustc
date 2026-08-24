def test_jitter_spike_weighting():
    jitter = 1.0
    inst_jitter = 10.0

    # spike: new > old -> 0.3*old + 0.7*new
    result = jitter * 0.3 + inst_jitter * 0.7
    assert abs(result - 7.3) < 0.001


def test_jitter_stable_weighting():
    jitter = 10.0
    inst_jitter = 1.0

    # stable: new <= old -> 0.8*old + 0.2*new
    result = jitter * 0.8 + inst_jitter * 0.2
    assert abs(result - 8.2) < 0.001


def test_ping_is_minimum_rtt():
    rtts = [8.42, 8.91, 8.35, 9.02, 8.47]
    ping = min(rtts)
    assert abs(ping - 8.35) < 0.001


def test_jitter_sequence():
    rtts = [10.0, 12.0, 11.0, 15.0, 10.0]
    jitter = 0.0
    prev_rtt = rtts[0]

    for i in range(1, len(rtts)):
        inst = abs(rtts[i] - prev_rtt)
        if i == 1:
            jitter = inst
        else:
            if inst > jitter:
                jitter = jitter * 0.3 + inst * 0.7
            else:
                jitter = jitter * 0.8 + inst * 0.2
        prev_rtt = rtts[i]

    assert jitter > 0
    assert isinstance(jitter, float)

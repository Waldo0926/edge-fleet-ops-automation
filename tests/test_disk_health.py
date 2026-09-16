from edge_fleet_ops.disk_health import parse_root_df, classify_disk_health


def test_parse_root_df():
    text = """__DF__\n/dev/root 10000M 8200M 1800M 82% /\n__SMART__\n"""
    assert parse_root_df(text) == (82, 1800)


def test_disk_usage_warning():
    text = """__DF__\n/dev/root 10000M 8200M 1800M 82% /\n__SMART__\n"""
    severity, warnings = classify_disk_health(text, warn_percent=80, critical_percent=90)
    assert severity == "warning"
    assert any("high" in w for w in warnings)


def test_smart_failure_is_critical():
    text = """__DF__\n/dev/root 10000M 2000M 8000M 20% /\n__SMART__\nSMART overall-health self-assessment test result: FAILED\n"""
    severity, warnings = classify_disk_health(text)
    assert severity == "critical"
    assert "SMART failure" in warnings

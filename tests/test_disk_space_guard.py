from edge_fleet_ops.disk_space_guard import CleanupPolicy, safe_cleanup_command


def test_cleanup_is_dry_run_by_default():
    cmd = safe_cleanup_command(CleanupPolicy())
    assert "-print" in cmd
    assert "-delete" not in cmd


def test_cleanup_apply_is_explicit():
    cmd = safe_cleanup_command(CleanupPolicy(), apply=True)
    assert "-delete" in cmd

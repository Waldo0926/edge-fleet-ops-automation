from edge_fleet_ops.workload_health import parse_containers, classify_workloads


def test_parse_container_line():
    text = "CT\tworker-a\tregistry/example:1\trunning\tPID=123\tESTAB=4\tSOCK=8\n"
    items = parse_containers(text)
    assert items[0].name == "worker-a"
    assert items[0].established == 4


def test_zero_socket_running_container_warns():
    text = "CT\tworker-a\tregistry/example:1\trunning\tPID=123\tESTAB=0\tSOCK=0\n"
    severity, reasons = classify_workloads(parse_containers(text))
    assert severity == "warning"
    assert reasons


def test_stopped_container_critical():
    text = "CT\tworker-a\tregistry/example:1\texited\tPID=0\tESTAB=0\tSOCK=0\n"
    severity, _ = classify_workloads(parse_containers(text))
    assert severity == "critical"

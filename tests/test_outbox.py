from edge_fleet_ops.outbox import AlertOutbox


def test_atomic_bounded_drain(tmp_path):
    outbox = AlertOutbox(tmp_path / "alerts.jsonl")
    for i in range(3):
        outbox.enqueue(f"message-{i}", node=f"n{i}")
    assert outbox.drain(limit=2) == ["message-0", "message-1"]
    assert outbox.drain(limit=2) == ["message-2"]
    assert outbox.drain(limit=2) == []

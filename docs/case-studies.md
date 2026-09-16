# Operational case studies

These are sanitized summaries of problems the original private automation addressed.

## Fleet disk-health audit

A heterogeneous edge fleet used a mix of SATA/USB, NVMe and eMMC storage. A single audit needed to collect filesystem capacity, device inventory and whichever health telemetry each device class exposed. The tooling normalized those signals into `ok`, `warning` and `critical` states instead of assuming one storage technology.

## Stateful workload health

A process being `running` was not sufficient evidence that a workload was healthy. The checks combined container state with PID, established TCP connections and open socket counts. Persistent state made it possible to alert on transitions rather than emitting the same warning every polling interval.

## Disk-pressure guard

Some nodes accumulated logs quickly enough to affect workload stability. The legacy scripts included targeted cleanup and post-clean verification. The portfolio version keeps only a constrained, dry-run-first cleanup primitive: it operates on explicitly configured log roots and requires an explicit apply mode to delete files.

## Alert delivery without duplicate sends

Health-check jobs wrote compact messages to a JSONL outbox. A separate delivery job atomically renamed and drained that queue in bounded batches. This decoupled long-running fleet checks from notification delivery and reduced duplicate alerts when jobs overlapped or were restarted.

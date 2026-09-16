# Architecture

The original private tooling grew from operational scripts used to observe and recover a small fleet of Linux edge nodes. This public version keeps the engineering patterns while removing private infrastructure details, credentials, device identifiers and vendor-specific assumptions.

```text
              +-----------------------+
              |   Fleet control API   |
              | node -> IPv6 metadata |
              +-----------+-----------+
                          |
                          v
+----------------+  +-----+-------------------+
| nodes config   +->+ edge-fleet-ops          |
| labels/fallback|  | coordinator             |
+----------------+  +-----+-------------------+
                          |
                 IPv6 / OpenSSH
             +------------+-------------+
             |            |             |
             v            v             v
        +---------+   +---------+   +---------+
        | node A  |   | node B  |   | node N  |
        | Linux   |   | Linux   |   | Linux   |
        +----+----+   +----+----+   +----+----+
             |             |             |
             +------+------+-------------+
                    |
        +-----------+------------+
        | disk / workload checks |
        | state + JSONL alerts   |
        +------------------------+
```

## Core patterns preserved from the production scripts

- control-plane discovery with cached/fallback host candidates;
- IPv6 SSH across a multi-node fleet;
- bounded concurrent/periodic health checks;
- SMART/NVMe/eMMC and filesystem-capacity inspection;
- Docker process/socket health classification;
- persistent state and JSONL logs for change detection;
- an atomic alert outbox that avoids duplicate delivery;
- lock-based cron launchers to prevent overlapping jobs;
- conservative self-healing: destructive actions are excluded or require an explicit apply flag.

## Sanitization decisions

The public repository intentionally omits production node IDs, location labels, internal API domains, shared credentials, live host addresses, and workload-provider identifiers. Password-based SSH from the legacy scripts was replaced by key-based OpenSSH.

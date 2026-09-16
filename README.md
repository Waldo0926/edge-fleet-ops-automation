# Edge Fleet Ops Automation

> Stateful Linux edge-fleet monitoring, disk-health auditing and safe operations automation.  
> Linux 边缘节点集群的状态化监控、磁盘健康巡检与安全运维自动化工具。

[![tests](https://github.com/Waldo0926/edge-fleet-ops-automation/actions/workflows/tests.yml/badge.svg)](https://github.com/Waldo0926/edge-fleet-ops-automation/actions/workflows/tests.yml)

## Why this project exists

This repository is a sanitized portfolio reconstruction of automation originally built to operate a small fleet of Linux edge nodes. The private scripts evolved around real operational problems: nodes moving between IPv6 addresses, heterogeneous storage, disk pressure, container health, long-running cron jobs, and noisy/duplicated alerts.

The public version keeps those engineering patterns while removing production credentials, device IDs, internal endpoints, site labels and workload-provider details.

这个仓库来自一套真实使用过的 Linux 边缘节点运维脚本。公开版本保留核心工程思路，同时移除了生产环境凭据、设备 ID、内部 API、地点标签与业务方专有信息。

## What it demonstrates

- **Fleet discovery:** resolve node IDs to live IPv6 candidates through a control-plane API, with configured fallbacks.
- **Remote operations:** key-based IPv6 OpenSSH across multiple Linux nodes.
- **Disk-health auditing:** filesystem pressure plus SMART / NVMe / eMMC signals.
- **Workload health:** Docker state combined with PID, established TCP connections and socket counts.
- **Stateful alerts:** persistent JSONL state/outbox patterns for transition-based notifications.
- **Cron safety:** bounded jobs and lock-friendly deployment examples.
- **Conservative self-healing:** public cleanup logic is dry-run first and intentionally excludes formatting or broad destructive repair.

## Architecture

```text
Control API + node config
          |
          v
  edge-fleet-ops coordinator
          |
      IPv6 SSH
   +------+------+------+
   |      |      |      |
 node A node B node C ... node N
   |      |      |      |
   +------+------+- ----+
          |
  +-------+--------------------+
  | disk health / workloads    |
  | persistent state / alerts  |
  +----------------------------+
```

See [`docs/architecture.md`](docs/architecture.md) for the detailed design.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Set your own control-plane endpoint and SSH key in the environment. Do **not** commit `.env`.

Run tests:

```bash
pytest -q
```

Example read-only fleet checks:

```bash
export EDGE_CONTROL_API=https://control.example.invalid/api/nodes
edge-fleet-ops audit-disk --nodes config/nodes.example.json
edge-fleet-ops check-workloads --nodes config/nodes.example.json
```

## Public vs. private version

The original private toolkit contained several highly environment-specific scripts, including disk auto-repair, one-off migrations and bandwidth/result reconciliation. Those files are deliberately excluded from the public repository. The showcase focuses on reusable SRE/DevOps patterns rather than publishing production-specific behavior.

A security review of the legacy scripts also found a shared plaintext SSH credential pattern. The public implementation removes password-based SSH entirely and uses standard key-based OpenSSH. If adapting old private scripts, rotate any credential that may still be valid.

## Repository layout

```text
src/edge_fleet_ops/
  control_plane.py      # node discovery / IPv6 candidates
  ssh.py                # key-based remote execution
  disk_health.py        # disk + filesystem health classification
  workload_health.py    # Docker/socket health classification
  disk_space_guard.py   # constrained dry-run-first cleanup primitive
  outbox.py             # persistent atomic alert queue
  cli.py                # command-line entry point
config/
  nodes.example.json
docs/
  architecture.md
  case-studies.md
  security.md
deployment/cron/
tests/
```

## Safety boundary

This is a portfolio/reference project, not a drop-in production daemon. Review remote commands, permissions, thresholds, paths, and alert routing before using it on real systems. See [`docs/security.md`](docs/security.md).

## Status

**Archived / Portfolio Project.** The original deployment has been retired or changed; this repository preserves the engineering work in a sanitized, reviewable form.

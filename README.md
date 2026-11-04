# Zabbix Chrony NTP Monitoring Template (`zabbix-template-chrony`)

[🇬🇧 Read in English](README.md) | [🇷🇺 Читать на русском](README_RU.md)

[![Zabbix](https://img.shields.io/badge/Zabbix-7.0%20LTS%20%7C%207.4%2B-red?logo=zabbix)](https://www.zabbix.com/)
[![Chrony](https://img.shields.io/badge/NTP-Chrony-blue)](https://chrony-project.org/)
[![Agent](https://img.shields.io/badge/Agent-Zabbix%20Agent%202-green)](https://www.zabbix.com/documentation/current/en/manual/concepts/agent2)
[![GitHub Repository](https://img.shields.io/badge/GitHub-qwertykolea%2Fzabbix--template--chrony-181717?logo=github)](https://github.com/qwertykolea/zabbix-template-chrony)

A production-grade, highly efficient Chrony NTP client monitoring suite designed for **Zabbix Agent 2** and compliant with official Zabbix 7.4 standards.

Features the **Master + Dependent Items** pattern, raw CSV output parsing via native Zabbix Preprocessing, automated Low-Level Discovery (LLD) of all upstream NTP sources, native Zabbix 7.0+ template dashboard, Grafana dashboard integration, zero external bash scripts, and minimal system overhead.

---

## 🚀 Key Advantages

| Feature | This Suite | Typical Internet Templates |
| :--- | :--- | :--- |
| **`chronyc` Execution Frequency** | **Only 2 calls per minute** (`tracking` & `sources`) | 10–15 separate subshell forks every minute |
| **External Shell Scripts** | **0 (Zero-script)**. Single `.conf` file in agent | 2–3 bash/awk/sed scripts in `/usr/local/bin` |
| **OS Locale / Language Dependency**| **None**. Uses `-c` flag for pure CSV output | **High** (fragile English text parsing with `awk`) |
| **Pure NTP Client Support** | **100%**. No server sockets or clients required | Fails on clients by expecting UDP 323 & connected clients |
| **Agent Modes Supported** | **Dual Templates**: Passive and Active included | Only a single hard-coded mode |
| **Upstream Sources Discovery (LLD)**| **Automated (LLD)** for every configured peer | Static metrics or not implemented |
| **Built-in Template Dashboard** | **Native Zabbix 7.0/7.4 Dashboard** with KPI cards & graphs | Absent |
| **Grafana Integration** | **Ready-to-use JSON** for Zabbix plugin | Absent |
| **Triggers & Anti-flapping** | Multi-level thresholds with restart dependencies | Absent or basic without dependencies |

---

## 📁 Repository Structure

```text
zabbix-template-chrony/
├── README.md                                 # English Documentation
├── README_RU.md                              # Russian Documentation
├── agent2_conf/
│   └── chrony.conf                           # Lightweight UserParameter config for Agent 2
├── templates/
│   ├── template_chrony_agent2_passive.yaml   # Template for Passive Agent (Zabbix Server pulls metrics)
│   ├── template_chrony_agent2_active.yaml    # Template for Active Agent (Agent pushes metrics)
│   └── generate.py                           # Deterministic template & UUID generator
├── dashboards/
│   └── grafana/
│       ├── chrony-overview.json              # Production Grafana Dashboard for Zabbix plugin
│       ├── README.md                         # Grafana setup guide (EN)
│       └── README_RU.md                      # Grafana setup guide (RU)
└── deploy/
    ├── install.sh                            # Automated 1-click Linux host installer
    ├── uninstall.sh                          # Clean uninstaller
    └── ansible/                              # Fleet automation via Ansible
        ├── playbook.yml                      # Ansible playbook
        ├── inventory.ini.example             # Example inventory
        ├── README.md                         # Ansible guide (EN)
        └── README_RU.md                      # Ansible guide (RU)
```

---

## ⚡ Quick Start (Linux Host Setup)

### Option 1: One-Line Online Installation from GitHub (Recommended)

Run directly on your target Linux host:

```bash
curl -fsSL https://raw.githubusercontent.com/qwertykolea/zabbix-template-chrony/main/deploy/install.sh | sudo bash
```

### Option 2: Run Locally from Cloned Repository

```bash
git clone https://github.com/qwertykolea/zabbix-template-chrony.git
cd zabbix-template-chrony/deploy
sudo chmod +x install.sh
sudo ./install.sh
```

### Option 3: Manual Installation (1 minute)

1. Copy the configuration file:
   ```bash
   sudo cp agent2_conf/chrony.conf /etc/zabbix/zabbix_agent2.d/chrony.conf
   sudo chmod 644 /etc/zabbix/zabbix_agent2.d/chrony.conf
   ```

2. Restart Zabbix Agent 2:
   ```bash
   sudo systemctl restart zabbix-agent2
   ```

3. Verify metric collection:
   ```bash
   zabbix_agent2 -t chrony.tracking
   zabbix_agent2 -t chrony.sources
   ```

---

## 🖥️ Zabbix Web UI Configuration

1. Navigate to **Data collection** -> **Templates** -> click **Import**.
2. Select the template file from the `templates/` folder:
   * `template_chrony_agent2_passive.yaml` — for hosts reachable directly by Zabbix Server/Proxy on port 10050.
   * `template_chrony_agent2_active.yaml` — for hosts behind NAT / firewalls where the agent initiates outbound connections to port 10051.
3. Link the imported template to your target hosts under **Data collection** -> **Hosts**.
4. View incoming metrics in **Monitoring** -> **Latest data** (filter by application `Chrony`).

---

## 📊 Monitored Metrics

### 1. System Synchronization Metrics (Tracking)
* `Chrony: Service process state` — daemon process status (`proc.num[chronyd]`).
* `Chrony: System time offset` — local system clock offset from the reference source in seconds (`s`).
* `Chrony: RMS offset` — long-term root mean square average of the offset (`s`).
* `Chrony: Last offset` — estimated local clock offset during the latest measurement (`s`).
* `Chrony: Stratum` — current NTP stratum level of the synchronized upstream source.
* `Chrony: Leap status` — leap second and synchronization status with Value Map:
  * `0` — Normal (clock is synchronized properly);
  * `1` — Insert second;
  * `2` — Delete second;
  * `3` — Not synchronised (loss of time sync).
* `Chrony: Root delay` — network round-trip delay to the stratum-1 reference clock (`s`).
* `Chrony: Root dispersion` — maximum estimated error accumulation (`s`).
* `Chrony: Frequency` — local oscillator frequency drift rate in parts per million (`ppm`).
* `Chrony: Residual frequency` — residual frequency offset (`ppm`).
* `Chrony: Skew` — estimated error bound on frequency in `ppm`.
* `Chrony: Update interval` — interval between the last two clock updates in seconds (`s`).
* `Chrony: Reference source IP` — IP address or identifier of the active upstream reference server.

### 2. Sources Summary Metrics
* `Chrony: Configured sources count` — total count of NTP sources discovered in Chrony.
* `Chrony: Synchronized sources count` — count of sources in active synchronization (`*` or `+`).

### 3. Low-Level Discovery (LLD) of Upstream Sources
Zabbix automatically discovers each configured upstream NTP source and tracks:
* `Chrony: Source [{#SOURCE_NAME}]: State` — sync state (`*` = peered/synced, `+` = combined candidate, `-` = excluded/outlier, `?` = unreachable, `x` = false ticker, `~` = jittery).
* `Chrony: Source [{#SOURCE_NAME}]: Stratum` — stratum level of the upstream source.
* `Chrony: Source [{#SOURCE_NAME}]: Reachability register` — 8-bit reachability register converted from octal to decimal (`255` = 100% reachability across last 8 queries, `0` = completely unreachable).
* `Chrony: Source [{#SOURCE_NAME}]: Last sample offset` — estimated offset relative to this source (`s`).
* `Chrony: Source [{#SOURCE_NAME}]: Root distance / delay` — network round-trip distance to this source (`s`).
* `Chrony: Source [{#SOURCE_NAME}]: Poll interval` — polling interval expressed as log2 seconds.

---

## 🔔 Triggers and Alert Thresholds

| Severity | Trigger Name | Expression | Description & Dependencies |
| :--- | :--- | :--- | :--- |
| **High** | `Chrony: Service process is not running` | `last(proc.num[chronyd])=0` | The `chronyd` background service is stopped or crashed. |
| **High** | `Chrony: Host is not synchronised with NTP` | `last(chrony.tracking.leap_status)=3` | Leap status is unsynchronized (depends on service running). |
| **High** | `Chrony: Stratum is invalid (0 or >= 16)` | `stratum=0 or stratum>=16` | Upstream stratum indicates unsynchronized state (depends on service running). |
| **Warning** | `Chrony: Clock offset is excessive (> 100ms)` | `min(offset, 3m) > 0.1s or max(offset, 3m) < -0.1s` | Clock offset exceeds 100ms for over 3 minutes (filters network spikes). |
| **High** | `Chrony: Clock offset is critical (> 500ms)` | `last(offset) > 0.5s or last(offset) < -0.5s` | Critical clock drift beyond 500ms (depends on warning trigger). |
| **Warning** | `Chrony: Root dispersion is excessive (> 100ms)` | `min(root_dispersion, 5m) > 0.1s` | Root dispersion exceeds `{$CHRONY.DISPERSION.WARN}` for 5 minutes. Early warning of degraded network path quality to NTP servers. |
| **Info** | `Chrony: Active reference source is flapping` | `changecount(ref_ip, 1h) > 5` | Active upstream reference peer switched more than 5 times in 1 hour. Indicates routing instability or network jitter. |
| **Warning (Disabled by default)** | `Chrony: Low number of synchronized NTP sources (< 2)` | `last(synced_count) < 2` | Active synchronized sources count dropped below threshold. Can be enabled in Zabbix UI. |
| **Warning (Prototype)** | `Chrony: NTP source [{#SOURCE_NAME}] is flagged as false ticker` | `last(state)="x"` | Chrony identified this source as providing invalid or contradictory time. |
| **Info (Prototype)** | `Chrony: NTP source [{#SOURCE_NAME}] is unreachable` | `last(reach)=0` | Last 8 consecutive polling attempts to this source failed. |

### User Macros (Customizable Thresholds):
You can override thresholds at the template level or per-host level:
* `{$CHRONY.OFFSET.WARN}`: `0.1` (Warning threshold in seconds, default 100ms);
* `{$CHRONY.OFFSET.CRIT}`: `0.5` (Critical threshold in seconds, default 500ms);
* `{$CHRONY.DISPERSION.WARN}`: `0.1` (Warning threshold for root dispersion in seconds, default 100ms);
* `{$CHRONY.SOURCES.MIN.WARN}`: `2` (Minimum synchronized sources for the optional trigger).

---

## 📈 Visualizations & Dashboards

### 1. Built-in Multi-Page Template Dashboard (Zabbix 7.0 LTS / 7.4+)
The template features a native, modernized multi-page dashboard **Chrony NTP overview**, accessible directly in Zabbix host dashboards:

* **Page 1: Overview**
  * **Modern KPI Value Cards**: Clean, uncluttered value indicators with custom typography and real-time threshold coloring:
    * `System time offset`: Color-coded thresholds (`green` < 50ms, `yellow` >= 50ms, `red` >= 100ms) with 4-decimal precision;
    * `Reference source IP`: Full non-truncated IPv4 address display with generous horizontal margin;
    * `Stratum`: Integer formatting (`3` instead of `3.00`) with color-coded health thresholds (`green` 1–3, `yellow` 4–9, `red` 16);
    * `Leap status`: Clean status label (`Normal`, `Insert second`, `Not synchronised`) without clipping or truncated text.
  * **System Clock Offsets Graph**: Time-series comparing System time offset, RMS offset, and Last sample offset.
  * **Root Delay & Dispersion Graph**: Network latency and accumulated error bounds to upstream reference clocks.
  * **Frequency & Skew Graph**: Local crystal oscillator frequency drift (ppm) and stability bounds.
  * **NTP Sources Count Graph**: Configured vs. active synchronized sources count over time.
  * **Discovered NTP Sources Grid**: Full-width 2-column prototype graphs displaying offset and delay for each discovered peer.

* **Page 2: NTP Sources (Peers)**
  * Dedicated multi-peer analysis tab with wide, high-resolution graph prototypes for all discovered upstream servers, fully synchronized with the global dashboard time selector (`DASHBOARD._timeperiod`).

### 2. Standalone Grafana Dashboard
For teams utilizing Grafana with the official **Zabbix plugin** (`alexanderzobnin-zabbix-datasource`), a ready-to-import JSON dashboard is provided in [`dashboards/grafana/`](dashboards/grafana/):
* Dynamic dropdown selectors for Host Group and Host.
* Polished stat cards and multi-series timeseries graphs.
* See the [Grafana Setup Guide](dashboards/grafana/README.md) for quick import instructions.

---

## 🛠️ Diagnostics & Troubleshooting

If `zabbix_agent2 -t chrony.tracking` returns an error or empty string:

1. **Verify user permissions**:
   ```bash
   sudo -u zabbix chronyc -c tracking
   ```
2. **If UNIX domain socket access is restricted**:
   Ensure `/run/chrony` permissions allow local read operations:
   ```bash
   chmod o+rx /run/chrony
   chmod 666 /run/chrony/chronyd.sock
   ```
3. **Test sources item syntax**:
   ```bash
   zabbix_agent2 -t chrony.sources
   ```

---

## 🗑️ Uninstallation

To cleanly remove the configuration from a host:

```bash
curl -fsSL https://raw.githubusercontent.com/qwertykolea/zabbix-template-chrony/main/deploy/uninstall.sh | sudo bash
```

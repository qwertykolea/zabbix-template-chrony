# Chrony NTP Grafana Dashboard

This directory contains a pre-built Grafana dashboard designed for the **Zabbix Chrony Monitoring Template**. It leverages the official [Zabbix plugin for Grafana](https://grafana.com/grafana/plugins/alexanderzobnin-zabbix-datasource/) (`alexanderzobnin-zabbix-datasource`).

## Features

- **System Clock Status KPIs**: Real-time stat cards for System Time Offset, NTP Stratum, Leap Indicator status, Active Reference Peer IP, Synchronized Sources count, and Root Dispersion.
- **Clock Offsets & Stability**: High-resolution time-series comparing System time offset, RMS offset, and Last sample offset.
- **Root Metrics**: Track Root Delay and Root Dispersion to gauge network distance and upstream clock jitter.
- **Frequency & Skew**: Real-time monitoring of local clock frequency adjustments (ppm) and estimated error bounds (skew).
- **Multi-Source Discovery Panels**: Dynamic regular-expression panels that automatically display all discovered upstream NTP sources (`chrony.source.offset[*]`, `chrony.source.delay[*]`).
- **Dynamic Templating**: Host Group and Host dropdown selectors automatically populated from your Zabbix inventory.

## Prerequisites

1. **Grafana** (v9.0+, v10.x, or v11.x).
2. **Zabbix Plugin for Grafana** (`alexanderzobnin-zabbix-datasource` installed and configured with your Zabbix API endpoint).
3. The host must be monitored using **Chrony by Zabbix agent 2** (or Active variant).

## Installation

1. In the Grafana Web UI, navigate to **Dashboards** -> **New** -> **Import**.
2. Click **Upload dashboard JSON file** and select `chrony-overview.json` (or paste its raw JSON content).
3. Under **Data Source**, select your configured Zabbix data source.
4. Click **Import**.
5. Select your target **Host Group** and **Host** in the dashboard top navigation bar.

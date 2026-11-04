# Automated Deployment via Ansible

[🇬🇧 Read in English](README.md) | [🇷🇺 Читать на русском](README_RU.md)

This playbook automates the deployment of the Chrony monitoring configuration (`chrony.conf`) across any number of Linux servers running Zabbix Agent 2.

## Quick Start Guide:

1. Copy and edit the example inventory file with your target server hostnames or IP addresses:
   ```bash
   cp inventory.ini.example inventory.ini
   nano inventory.ini
   ```

2. Execute the playbook:
   ```bash
   ansible-playbook -i inventory.ini playbook.yml
   ```

3. What the playbook performs automatically:
   - Verifies the `chrony` package is installed and the service is enabled/active.
   - Ensures the `/etc/zabbix/zabbix_agent2.d/` directory exists.
   - Deploys the `chrony.conf` UserParameter configuration file.
   - Restarts `zabbix-agent2` if the configuration changed.
   - Validates live metric collection via `zabbix_agent2 -t chrony.tracking` and prints the output to your terminal.

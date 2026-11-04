#!/usr/bin/env bash
# ==============================================================================
# Uninstaller for Chrony NTP Monitoring (Zabbix Agent 2)
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

if [[ "${EUID}" -ne 0 ]]; then
    echo -e "${RED}[ERROR] This uninstaller must be run as root (or with sudo).${NC}" >&2
    exit 1
fi

CONF_DEST="/etc/zabbix/zabbix_agent2.d/chrony.conf"

if [[ -f "${CONF_DEST}" ]]; then
    echo -e "${BLUE}[INFO] Removing ${CONF_DEST}...${NC}"
    rm -f "${CONF_DEST}"
else
    echo -e "${BLUE}[INFO] ${CONF_DEST} does not exist.${NC}"
fi

if systemctl list-unit-files | grep -q "^zabbix-agent2.service"; then
    echo -e "${BLUE}[INFO] Restarting zabbix-agent2 service...${NC}"
    systemctl restart zabbix-agent2
    echo -e "${GREEN}[OK] zabbix-agent2 restarted.${NC}"
fi

echo -e "${GREEN}[OK] Chrony monitoring configuration removed successfully.${NC}"

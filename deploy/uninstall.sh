#!/usr/bin/env bash
# ==============================================================================
# Uninstaller for Chrony NTP Monitoring (Zabbix Agent 2)
# Repository: https://github.com/qwertykolea/zabbix-template-chrony
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

if systemctl is-active --quiet zabbix-agent2 || systemctl list-unit-files 2>/dev/null | grep -Eq "^zabbix[-_]agent2"; then
    echo -e "${BLUE}[INFO] Restarting zabbix-agent2 service...${NC}"
    systemctl restart zabbix-agent2 || true
    echo -e "${GREEN}[OK] zabbix-agent2 restarted.${NC}"
fi

echo -e "${GREEN}[OK] Chrony monitoring configuration removed successfully.${NC}"

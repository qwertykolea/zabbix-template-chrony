#!/usr/bin/env bash
# ==============================================================================
# Installer for Chrony NTP Monitoring (Zabbix Agent 2)
# Repository: https://github.com/qwertykolea/zabbix-template-chrony
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}   Chrony NTP Monitoring Setup for Zabbix Agent 2               ${NC}"
echo -e "${BLUE}==================================================================${NC}"

# 1. Root check
if [[ "${EUID}" -ne 0 ]]; then
    echo -e "${RED}[ERROR] This installer must be run as root (or with sudo).${NC}" >&2
    exit 1
fi

# 2. Check chronyc presence
if ! command -v chronyc &>/dev/null; then
    echo -e "${RED}[ERROR] 'chronyc' command not found. Please install chrony first.${NC}" >&2
    echo -e "       Debian/Ubuntu: apt-get install chrony"
    echo -e "       RHEL/CentOS/Rocky/Alma: dnf install chrony"
    exit 1
fi

# 3. Check chronyd service status
CHRONY_SVC="chronyd"
if ! systemctl list-unit-files 2>/dev/null | grep -q "^chronyd.service"; then
    if systemctl list-unit-files 2>/dev/null | grep -q "^chrony.service"; then
        CHRONY_SVC="chrony"
    fi
fi

if ! systemctl is-active --quiet "${CHRONY_SVC}"; then
    echo -e "${YELLOW}[WARN] Chrony daemon (${CHRONY_SVC}) is not active! Attempting to start...${NC}"
    systemctl enable --now "${CHRONY_SVC}" || true
fi

# 4. Check zabbix-agent2 presence
if ! command -v zabbix_agent2 &>/dev/null; then
    echo -e "${YELLOW}[WARN] 'zabbix_agent2' binary not found in PATH.${NC}"
    echo -e "       Continuing with config deployment, but agent restart/testing might fail."
fi

# 5. Locate configuration file (safe when run via piped curl ... | bash)
CONF_SRC=""
if [[ -n "${BASH_SOURCE[0]:-}" ]] && [[ -f "${BASH_SOURCE[0]:-}" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    CONF_SRC="${SCRIPT_DIR}/../agent2_conf/chrony.conf"
fi

CONF_DEST_DIR="/etc/zabbix/zabbix_agent2.d"
CONF_DEST="${CONF_DEST_DIR}/chrony.conf"

if [[ -z "${CONF_SRC}" ]] || [[ ! -f "${CONF_SRC}" ]]; then
    # In case script is piped directly from curl (e.g. curl ... | sudo bash)
    echo -e "${BLUE}[INFO] Creating chrony.conf directly...${NC}"
    mkdir -p "${CONF_DEST_DIR}"
    cat <<'EOF' > "${CONF_DEST}"
# Chrony NTP monitoring configuration for Zabbix Agent 2
UserParameter=chrony.tracking,chronyc -c tracking
UserParameter=chrony.sources,chronyc -c sources
EOF
else
    echo -e "${BLUE}[INFO] Copying configuration to ${CONF_DEST}...${NC}"
    mkdir -p "${CONF_DEST_DIR}"
    cp -f "${CONF_SRC}" "${CONF_DEST}"
fi

chmod 644 "${CONF_DEST}"
chown -R root:root "${CONF_DEST_DIR}" || true

# 6. Test chronyc execution permissions as zabbix user
if id -u zabbix &>/dev/null; then
    echo -e "${BLUE}[INFO] Verifying chronyc access for user 'zabbix'...${NC}"
    if ! su -s /bin/bash zabbix -c "chronyc -c tracking" &>/dev/null; then
        echo -e "${YELLOW}[WARN] User 'zabbix' cannot execute 'chronyc tracking' directly.${NC}"
        echo -e "${YELLOW}       Adding read permissions or checking chrony unix socket...${NC}"
        if [[ -d /run/chrony ]]; then
            chmod o+rx /run/chrony || true
        fi
        if [[ -S /run/chrony/chronyd.sock ]]; then
            chmod 666 /run/chrony/chronyd.sock || true
        fi
    fi
fi

# 7. Restart Zabbix Agent 2
if systemctl is-active --quiet zabbix-agent2 || systemctl list-unit-files 2>/dev/null | grep -Eq "^zabbix[-_]agent2"; then
    echo -e "${BLUE}[INFO] Restarting zabbix-agent2 service...${NC}"
    systemctl restart zabbix-agent2 || true
    if systemctl is-active --quiet zabbix-agent2; then
        echo -e "${GREEN}[OK] zabbix-agent2 is active and running.${NC}"
    fi
else
    echo -e "${YELLOW}[WARN] zabbix-agent2 service not found or not active. If running in a container, please reload the agent manually.${NC}"
fi

# 8. Test metrics
echo -e "\n${BLUE}==================================================================${NC}"
echo -e "${BLUE}   Testing Zabbix Agent 2 Metric Collection                     ${NC}"
echo -e "${BLUE}==================================================================${NC}"

if command -v zabbix_agent2 &>/dev/null; then
    echo -e "\n${BLUE}[TEST] chrony.tracking:${NC}"
    zabbix_agent2 -t chrony.tracking || true

    echo -e "\n${BLUE}[TEST] chrony.sources:${NC}"
    zabbix_agent2 -t chrony.sources || true
else
    echo -e "Testing directly via chronyc:"
    chronyc -c tracking
fi

echo -e "\n${GREEN}==================================================================${NC}"
echo -e "${GREEN}   Installation completed successfully!                         ${NC}"
echo -e "${GREEN}==================================================================${NC}"
echo -e "Next steps in Zabbix Web UI (v7.0+ / 7.4):"
echo -e "  1. Import template: 'Chrony by Zabbix agent 2' (or Active variant)"
echo -e "  2. Link the template to this host"
echo -e "  3. Check 'Latest Data' -> Application: Chrony"

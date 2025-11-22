#!/bin/bash

# Automated SSH Hardening Deployment Script
# Deploys SSH hardening across all servers in the network

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Server list
SERVERS=(
    "popos-laptop"
    "mesh01"
    "mesh02"
    "mesh03"
    "mesh04"
    "mesh05"
    "mesh06"
    "mesh07"
    "mesh08"
    "mesh09"
    "mesh10"
    "mesh11"
    "mesh12"
    "mesh13"
    "mesh14"
    "mesh15"
    "mesh16"
    "agenticoverlord"
    "digitalocean"
)

# SSH connection details
SSH_USER="andre"
SSH_KEY="$HOME/.ssh/id_rsa"
HARDENING_SCRIPT_DIR="/home/andre/batcave/mao/security_hardening"
LOG_FILE="/home/andre/batcave/mao/security_hardening/hardening_deploy_$(date +%Y%m%d_%H%M%S).log"

# Progress tracking
TOTAL_SERVERS=${#SERVERS[@]}
COMPLETED_SERVERS=0
FAILED_SERVERS=()
SUCCESS_SERVERS=()

# Logging
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo -e "${BLUE}=== Automated SSH Hardening Deployment ===${NC}"
echo -e "${BLUE}Started at: $(date)${NC}"
echo -e "${BLUE}Total servers to harden: $TOTAL_SERVERS${NC}"
echo -e "${BLUE}Log file: $LOG_FILE${NC}"

# Function to check SSH connectivity
check_ssh_connectivity() {
    local server=$1
    echo -e "${YELLOW}Checking SSH connectivity to $server...${NC}"

    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SSH_USER@$server" "echo 'Connection successful'" 2>/dev/null; then
        echo -e "${GREEN}✓ SSH connectivity to $server confirmed${NC}"
        return 0
    else
        echo -e "${RED}✗ SSH connectivity to $server failed${NC}"
        return 1
    fi
}

# Function to harden single server
harden_server() {
    local server=$1
    echo -e "\n${CYAN}=== Hardening Server: $server ===${NC}"
    echo -e "${BLUE}Time: $(date)${NC}"

    # Check connectivity first
    if ! check_ssh_connectivity "$server"; then
        FAILED_SERVERS+=("$server")
        return 1
    fi

    # Create temporary directory on server
    echo -e "${YELLOW}Creating temporary directory on $server...${NC}"
    ssh "$SSH_USER@$server" "mkdir -p /tmp/ssh_hardening_$(date +%s)" || {
        echo -e "${RED}Failed to create temporary directory on $server${NC}"
        FAILED_SERVERS+=("$server")
        return 1
    }

    # Copy hardening script to server
    echo -e "${YELLOW}Copying hardening script to $server...${NC}"
    scp "$HARDENING_SCRIPT_DIR/ssh_hardening.sh" "$SSH_USER@$server:/tmp/ssh_hardening.sh" || {
        echo -e "${RED}Failed to copy hardening script to $server${NC}"
        FAILED_SERVERS+=("$server")
        return 1
    }

    # Execute hardening script with sudo
    echo -e "${YELLOW}Executing SSH hardening on $server...${NC}"
    if ssh "$SSH_USER@$server" "sudo bash /tmp/ssh_hardening.sh"; then
        echo -e "${GREEN}✓ SSH hardening completed successfully on $server${NC}"
        SUCCESS_SERVERS+=("$server")

        # Retrieve audit report
        echo -e "${YELLOW}Retrieving audit report from $server...${NC}"
        ssh "$SSH_USER@$server" "sudo find /var/log -name '*ssh_security_audit_*' -type f -exec cp {} /tmp/ \;" || true

        # Copy audit reports back
        ssh "$SSH_USER@$server" "mkdir -p /tmp/audit_reports" || true
        scp "$SSH_USER@$server:/tmp/ssh_security_audit_*.txt" "$HARDENING_SCRIPT_DIR/reports/" 2>/dev/null || true

    else
        echo -e "${RED}✗ SSH hardening failed on $server${NC}"
        FAILED_SERVERS+=("$server")
        return 1
    fi

    # Clean up temporary files
    echo -e "${YELLOW}Cleaning up temporary files on $server...${NC}"
    ssh "$SSH_USER@$server" "sudo rm -f /tmp/ssh_hardening.sh" || true

    return 0
}

# Function to show progress
show_progress() {
    local completed=$1
    local total=$2
    local percentage=$((completed * 100 / total))

    echo -e "\n${BLUE}=== Progress Update ===${NC}"
    echo -e "Completed: $completed/$total servers (${percentage}%)"
    echo -e "Successful: ${#SUCCESS_SERVERS[@]}"
    echo -e "Failed: ${#FAILED_SERVERS[@]}"

    if [ ${#FAILED_SERVERS[@]} -gt 0 ]; then
        echo -e "${RED}Failed servers: ${FAILED_SERVERS[*]}${NC}"
    fi
}

# Function to test connectivity to all servers first
test_all_connectivity() {
    echo -e "\n${BLUE}=== Testing Connectivity to All Servers ===${NC}"

    local reachable_servers=()
    local unreachable_servers=()

    for server in "${SERVERS[@]}"; do
        if check_ssh_connectivity "$server"; then
            reachable_servers+=("$server")
        else
            unreachable_servers+=("$server")
        fi
    done

    echo -e "\n${GREEN}=== Connectivity Test Results ===${NC}"
    echo -e "Reachable servers: ${#reachable_servers[@]}/${TOTAL_SERVERS}"
    if [ ${#unreachable_servers[@]} -gt 0 ]; then
        echo -e "${RED}Unreachable servers: ${unreachable_servers[*]}${NC}"
    fi

    # Update server list to only include reachable servers
    SERVERS=("${reachable_servers[@]}")
    TOTAL_SERVERS=${#SERVERS[@]}
}

# Function to create summary report
create_summary_report() {
    echo -e "\n${BLUE}=== Creating Summary Report ===${NC}"

    SUMMARY_FILE="/home/andre/batcave/mao/security_hardening/hardening_summary_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$SUMMARY_FILE" << EOF
=== SSH Hardening Deployment Summary ===
Deployment Date: $(date)
Total Servers Targeted: ${#SERVERS[@]}
Successfully Hardened: ${#SUCCESS_SERVERS[@]}
Failed: ${#FAILED_SERVERS[@]}

=== Successfully Hardened Servers ===
${SUCCESS_SERVERS[*]}

=== Failed Servers ===
${FAILED_SERVERS[*]}

=== Audit Reports Location ===
$HARDENING_SCRIPT_DIR/reports/

=== Next Steps ===
1. Review audit reports for each server
2. Verify SSH connectivity to all hardened servers
3. Ensure SSH keys are properly set up for passwordless authentication
4. Schedule regular security audits and updates

=== End of Summary ===
EOF

    echo -e "${GREEN}Summary report created: $SUMMARY_FILE${NC}"
}

# Function to cleanup and prepare
cleanup_and_prepare() {
    echo -e "\n${BLUE}=== Cleaning up and Preparing ===${NC}"

    # Create reports directory
    mkdir -p "$HARDENING_SCRIPT_DIR/reports"

    # Make scripts executable
    chmod +x "$HARDENING_SCRIPT_DIR/ssh_hardening.sh"
    chmod +x "$0"

    echo -e "${GREEN}Preparation completed${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}Starting automated SSH hardening deployment...${NC}"

    cleanup_and_prepare

    # Test connectivity to all servers first
    test_all_connectivity

    if [ $TOTAL_SERVERS -eq 0 ]; then
        echo -e "${RED}No servers are reachable. Aborting deployment.${NC}"
        exit 1
    fi

    echo -e "\n${BLUE}=== Starting Hardening Process ===${NC}"

    # Harden each server
    for server in "${SERVERS[@]}"; do
        echo -e "\n${CYAN}Processing server $((COMPLETED_SERVERS + 1))/$TOTAL_SERVERS: $server${NC}"

        if harden_server "$server"; then
            ((COMPLETED_SERVERS++))
        fi

        # Show progress every 3 servers
        if [ $((COMPLETED_SERVERS % 3)) -eq 0 ] || [ $COMPLETED_SERVERS -eq $TOTAL_SERVERS ]; then
            show_progress $COMPLETED_SERVERS $TOTAL_SERVERS
        fi

        # Brief pause between servers
        sleep 2
    done

    # Create final summary
    create_summary_report

    echo -e "\n${GREEN}=== Hardening Deployment Complete ===${NC}"
    echo -e "${GREEN}Successfully hardened: ${#SUCCESS_SERVERS[@]} servers${NC}"
    echo -e "${RED}Failed: ${#FAILED_SERVERS[@]} servers${NC}"
    echo -e "${BLUE}Check summary report for details${NC}"

    if [ ${#FAILED_SERVERS[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}=== Failed Servers - Manual Review Required ===${NC}"
        for server in "${FAILED_SERVERS[@]}"; do
            echo -e "${RED}• $server - requires manual investigation${NC}"
        done
        exit 1
    else
        echo -e "\n${GREEN}🎉 All servers successfully hardened!${NC}"
        exit 0
    fi
}

# Handle script interruption
trap 'echo -e "\n${RED}Script interrupted. Cleaning up...${NC}"; exit 1' INT TERM

# Run main function
main "$@"
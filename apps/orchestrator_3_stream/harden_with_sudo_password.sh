#!/bin/bash

# Cloud Server SSH Hardening with Sudo Password
# For servers that require password authentication for sudo

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

harden_server_with_sudo() {
    local server=$1
    local host_name=$(echo "$server" | cut -d':' -f1)
    local host_ip=$(echo "$server" | cut -d':' -f2)

    echo
    echo "================================================================================"
    log "Hardening server with sudo password: $host_name ($host_ip)"
    echo "================================================================================"

    # Step 1: Create SSH config backup
    log "Creating SSH configuration backup..."
    if ssh andre@$host_ip 'sudo -S cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)' <<< "$sudo_password"; then
        success "✓ Backup created on $host_name"
    else
        error "✗ Failed to create backup on $host_name"
        return 1
    fi

    # Step 2: Check current configuration
    log "Checking current SSH configuration..."
    local current_config=$(ssh andre@$host_ip 'grep -E "^#?PasswordAuthentication|^#?PubkeyAuthentication" /etc/ssh/sshd_config')
    log "Current config: $current_config"

    # Step 3: Apply hardening changes
    log "Applying SSH hardening configuration..."

    # Disable password authentication
    ssh andre@$host_ip 'sudo -S sed -i "s/^#PasswordAuthentication yes/PasswordAuthentication no/" /etc/ssh/sshd_config' <<< "$sudo_password"
    ssh andre@$host_ip 'sudo -S sed -i "s/^PasswordAuthentication yes/PasswordAuthentication no/" /etc/ssh/sshd_config' <<< "$sudo_password"

    # Enable public key authentication
    ssh andre@$host_ip 'sudo -S sed -i "s/^#PubkeyAuthentication yes/PubkeyAuthentication yes/" /etc/ssh/sshd_config' <<< "$sudo_password"
    ssh andre@$host_ip 'sudo -S sed -i "s/^PubkeyAuthentication no/PubkeyAuthentication yes/" /etc/ssh/sshd_config' <<< "$sudo_password"

    # Disable root login
    ssh andre@$host_ip 'sudo -S sed -i "s/^#PermitRootLogin yes/PermitRootLogin no/" /etc/ssh/sshd_config' <<< "$sudo_password"
    ssh andre@$host_ip 'sudo -S sed -i "s/^PermitRootLogin yes/PermitRootLogin no/" /etc/ssh/sshd_config' <<< "$sudo_password"

    success "✓ SSH configuration updated on $host_name"

    # Step 4: Restart SSH service
    log "Restarting SSH service on $host_name..."
    if ssh andre@$host_ip 'sudo -S systemctl restart sshd' <<< "$sudo_password"; then
        success "✓ SSH service restarted on $host_name"
    else
        error "✗ Failed to restart SSH service on $host_name"
        return 1
    fi

    # Step 5: Wait for service to stabilize
    log "Waiting for SSH service to stabilize..."
    sleep 5

    # Step 6: Verify hardening
    log "Verifying hardening on $host_name..."
    if ssh -o BatchMode=yes andre@$host_ip 'echo "Hardening verification successful"'; then
        # Check configuration using non-privileged method
        local config_check=$(ssh andre@$host_ip 'grep -E "^PasswordAuthentication|^PubkeyAuthentication" /etc/ssh/sshd_config' | tr " " ":")

        local password_auth=$(echo "$config_check" | grep "PasswordAuthentication" | cut -d':' -f2)
        local pubkey_auth=$(echo "$config_check" | grep "PubkeyAuthentication" | cut -d':' -f2)

        if [[ "$password_auth" == "no" ]] && [[ "$pubkey_auth" == "yes" ]]; then
            success "✓ SSH hardening verified on $host_name"
            success "  - Password Authentication: DISABLED"
            success "  - Public Key Authentication: ENABLED"
            return 0
        else
            error "✗ SSH hardening verification failed on $host_name"
            error "  - Password Authentication: $password_auth (should be no)"
            error "  - Public Key Authentication: $pubkey_auth (should be yes)"
            return 1
        fi
    else
        error "✗ Cannot access $host_name after SSH hardening!"
        warning "⚠ Attempting rollback..."
        ssh andre@$host_ip 'sudo -S systemctl restart sshd' <<< "$sudo_password" || true
        error "❌ Manual intervention required for $host_name"
        return 1
    fi
}

# Main execution
main() {
    if [[ -z "${sudo_password:-}" ]]; then
        error "Sudo password not provided. Usage: sudo_password='your_password' ./harden_with_sudo_password.sh"
        exit 1
    fi

    # Cloud servers that need hardening
    declare -a CLOUD_SERVERS=(
        "do-small:138.197.22.224"
        "do-medium:159.203.149.190"
    )

    log "Starting SSH hardening for cloud servers with sudo password"
    log "Servers to process: ${#CLOUD_SERVERS[@]}"

    local success_count=0
    local failed_count=0

    for server in "${CLOUD_SERVERS[@]}"; do
        if harden_server_with_sudo "$server"; then
            ((success_count++))
        else
            ((failed_count++))
        fi
    done

    echo
    echo "================================================================================"
    log "Cloud Server Hardening Summary"
    echo "================================================================================"
    success "✓ Successfully hardened: $success_count servers"

    if [[ $failed_count -gt 0 ]]; then
        error "✗ Failed to harden: $failed_count servers"
    fi

    echo
    log "Cloud server hardening completed."
}

main "$@"
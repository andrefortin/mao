#!/bin/bash

# Cloud Server SSH Hardening Script
# Target: do-small and do-medium servers

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Cloud servers that need hardening
declare -a CLOUD_SERVERS=(
    "do-small:138.197.22.224"
    "do-medium:159.203.149.190"
)

harden_server() {
    local server=$1
    local host_name=$(echo "$server" | cut -d':' -f1)
    local host_ip=$(echo "$server" | cut -d':' -f2)

    echo
    echo "================================================================================"
    log "Hardening cloud server: $host_name ($host_ip)"
    echo "================================================================================"

    # Step 1: Verify current access
    log "Verifying current SSH access..."
    if ! ssh -o BatchMode=yes -o ConnectTimeout=10 andre@$host_ip 'echo "Connection verified"'; then
        error "Cannot establish key-based SSH connection to $host_name"
        return 1
    fi
    success "✓ Key-based access verified for $host_name"

    # Step 2: Check current configuration
    log "Checking current SSH configuration..."
    local current_config=$(ssh andre@$host_ip 'grep -E "^#?PasswordAuthentication|^#?PubkeyAuthentication" /etc/ssh/sshd_config')
    log "Current config: $current_config"

    # Step 3: Create backup
    log "Creating SSH configuration backup..."
    ssh andre@$host_ip "sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)"
    success "✓ Backup created on $host_name"

    # Step 4: Hardening with explicit confirmation
    warning "About to modify SSH configuration on $host_name"
    warning "This will disable password authentication!"
    read -p "Continue with hardening $host_name? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Applying SSH hardening to $host_name..."

        # Update SSH configuration
        ssh andre@$host_ip "sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"
        ssh andre@$host_ip "sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"
        ssh andre@$host_ip "sudo sed -i 's/^#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config"
        ssh andre@$host_ip "sudo sed -i 's/^PubkeyAuthentication no/PubkeyAuthentication yes/' /etc/ssh/sshd_config"

        # Ensure root login is disabled
        ssh andre@$host_ip "sudo sed -i 's/^#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config"
        ssh andre@$host_ip "sudo sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config"

        # Restart SSH service
        log "Restarting SSH service on $host_name..."
        ssh andre@$host_ip "sudo systemctl restart sshd"
        success "✓ SSH service restarted on $host_name"

        # Step 5: Wait for service to stabilize
        log "Waiting for SSH service to stabilize..."
        sleep 5

        # Step 6: Verify hardening
        log "Verifying hardening on $host_name..."
        if ssh -o BatchMode=yes andre@$host_ip 'echo "Hardening verification successful"'; then
            # Check configuration
            local new_config=$(ssh andre@$host_ip 'sudo sshd -T | grep -E "(passwordauthentication|pubkeyauthentication)" | tr " " ":"')
            local password_auth=$(echo "$new_config" | grep "passwordauthentication" | cut -d':' -f2)
            local pubkey_auth=$(echo "$new_config" | grep "pubkeyauthentication" | cut -d':' -f2)

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
            ssh andre@$host_ip "sudo systemctl restart sshd" || true
            error "❌ Manual intervention required for $host_name"
            return 1
        fi
    else
        warning "⚠ Skipping SSH hardening for $host_name by user choice"
        return 1
    fi
}

main() {
    log "Starting SSH hardening for cloud servers"
    log "Servers to process: ${#CLOUD_SERVERS[@]}"

    local success_count=0
    local failed_count=0

    for server in "${CLOUD_SERVERS[@]}"; do
        if harden_server "$server"; then
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
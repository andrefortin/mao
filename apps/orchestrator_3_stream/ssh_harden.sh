#!/bin/bash

# SSH Security Hardening Script
# CRITICAL: This script must be executed with extreme caution
# Author: SSH Authentication Setup Agent
# Purpose: Disable password authentication and enforce key-based SSH access

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Server list from SSH config
declare -a SERVERS=(
    "popos-laptop:192.168.2.142"
    "mesh01:192.168.2.201"
    "mesh02:192.168.2.202"
    "mesh03:192.168.2.203"
    "mesh04:192.168.2.204"
    "mesh05:192.168.2.205"
    "mesh06:192.168.2.206"
    "mesh07:192.168.2.207"
    "mesh08:192.168.2.208"
    "mesh09:192.168.2.209"
    "mesh10:192.168.2.210"
    "popos-server:192.168.2.143"
    "do-small:138.197.22.224"
    "do-medium:159.203.149.190"
    "aidev.agenticoverlord.com"
    "mesh11.agenticoverlord.com"
    "mesh12.agenticoverlord.com"
    "mesh13.agenticoverlord.com"
)

# Function to test SSH connection
test_ssh_connection() {
    local host=$1
    local user=${2:-andre}

    log "Testing SSH connection to $host..."
    if ssh -o BatchMode=yes -o ConnectTimeout=10 "$user@$host" 'echo "Connection successful"' 2>/dev/null; then
        success "✓ Key-based authentication working for $host"
        return 0
    else
        error "✗ Key-based authentication failed for $host"
        return 1
    fi
}

# Function to check if SSH key is already deployed
check_key_deployed() {
    local host=$1
    local user=${2:-andre}

    log "Checking if SSH key is deployed to $host..."
    local key_content=$(cat ~/.ssh/id_rsa.pub)

    if ssh -o BatchMode=yes "$user@$host" "grep -q '$key_content' ~/.ssh/authorized_keys" 2>/dev/null; then
        success "✓ SSH key already deployed to $host"
        return 0
    else
        warning "⚠ SSH key not found in authorized_keys on $host"
        return 1
    fi
}

# Function to deploy SSH key
deploy_ssh_key() {
    local host=$1
    local user=${2:-andre}

    log "Deploying SSH key to $host..."

    # Try ssh-copy-id first
    if ssh-copy-id -i ~/.ssh/id_rsa.pub "$user@$host" 2>/dev/null; then
        success "✓ SSH key deployed successfully to $host via ssh-copy-id"
        return 0
    else
        warning "⚠ ssh-copy-id failed, attempting manual deployment..."

        # Manual deployment
        local key_content=$(cat ~/.ssh/id_rsa.pub)
        if ssh "$user@$host" "mkdir -p ~/.ssh && echo '$key_content' >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"; then
            success "✓ SSH key deployed manually to $host"
            return 0
        else
            error "✗ Failed to deploy SSH key to $host"
            return 1
        fi
    fi
}

# Function to harden SSH configuration
harden_ssh_config() {
    local host=$1
    local user=${2:-andre}

    log "Hardening SSH configuration on $host..."

    # Create backup of sshd_config
    ssh "$user@$host" "sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)"

    # Update SSH configuration
    ssh "$user@$host" "sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"
    ssh "$user@$host" "sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"
    ssh "$user@$host" "sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config"
    ssh "$user@$host" "sudo sed -i 's/PubkeyAuthentication no/PubkeyAuthentication yes/' /etc/ssh/sshd_config"
    ssh "$user@$host" "sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config"
    ssh "$user@$host" "sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config"

    # Restart SSH service
    if ssh "$user@$host" "sudo systemctl restart sshd"; then
        success "✓ SSH service restarted successfully on $host"
        return 0
    else
        error "✗ Failed to restart SSH service on $host"
        return 1
    fi
}

# Function to verify hardening
verify_hardening() {
    local host=$1
    local user=${2:-andre}

    log "Verifying SSH hardening on $host..."

    # Test key-based authentication
    if test_ssh_connection "$host" "$user"; then
        # Check configuration
        local auth_method=$(ssh "$user@$host" "sudo sshd -T | grep passwordauthentication" 2>/dev/null | cut -d' ' -f2)
        local pubkey_method=$(ssh "$user@$host" "sudo sshd -T | grep pubkeyauthentication" 2>/dev/null | cut -d' ' -f2)

        if [[ "$auth_method" == "no" ]] && [[ "$pubkey_method" == "yes" ]]; then
            success "✓ SSH hardening verified on $host - Password auth disabled, key auth enabled"
            return 0
        else
            warning "⚠ SSH hardening may not be complete on $host"
            warning "Password auth: $auth_method, Pubkey auth: $pubkey_method"
            return 1
        fi
    else
        error "✗ Cannot verify hardening - key-based authentication failed on $host"
        return 1
    fi
}

# Function to rollback changes
rollback_changes() {
    local host=$1
    local user=${2:-andre}

    warning "⚠ Rolling back changes on $host..."
    ssh "$user@$host" "sudo systemctl restart sshd" || true
    warning "⚠ Manual intervention may be required on $host"
}

# Main execution function
process_server() {
    local server=$1
    local host_name
    local host_ip

    if [[ "$server" == *":"* ]]; then
        host_name=$(echo "$server" | cut -d':' -f1)
        host_ip=$(echo "$server" | cut -d':' -f2)
    else
        host_name="$server"
        host_ip="$server"
    fi

    echo
    echo "================================================================================"
    log "Processing server: $host_name ($host_ip)"
    echo "================================================================================"

    # Step 1: Test current SSH connection
    if ! test_ssh_connection "$host_ip"; then
        error "Cannot establish initial SSH connection to $host_name - skipping"
        return 1
    fi

    # Step 2: Check if key is deployed
    if ! check_key_deployed "$host_ip"; then
        # Step 3: Deploy SSH key if needed
        if ! deploy_ssh_key "$host_ip"; then
            error "Failed to deploy SSH key to $host_name - aborting hardening"
            return 1
        fi

        # Step 4: Test key-based authentication again
        if ! test_ssh_connection "$host_ip"; then
            error "Key-based authentication still failing on $host_name - aborting hardening"
            return 1
        fi
    fi

    # Step 5: Harden SSH configuration (with confirmation)
    warning "About to harden SSH configuration on $host_name"
    warning "This will disable password authentication!"
    read -p "Continue with hardening $host_name? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if ! harden_ssh_config "$host_ip"; then
            error "Failed to harden SSH configuration on $host_name"
            rollback_changes "$host_ip"
            return 1
        fi

        # Step 6: Wait for SSH service to stabilize
        log "Waiting for SSH service to stabilize..."
        sleep 5

        # Step 7: Verify hardening
        if ! verify_hardening "$host_ip"; then
            error "SSH hardening verification failed on $host_name"
            rollback_changes "$host_ip"
            return 1
        fi
    else
        warning "Skipping SSH hardening for $host_name by user choice"
        return 1
    fi

    success "✓ SSH hardening completed successfully for $host_name"
    return 0
}

# Main execution
main() {
    log "Starting SSH security hardening across all servers"
    log "Total servers to process: ${#SERVERS[@]}"

    # Check if we have an SSH key
    if [[ ! -f ~/.ssh/id_rsa ]]; then
        error "No SSH key found at ~/.ssh/id_rsa"
        exit 1
    fi

    local success_count=0
    local failed_count=0
    local failed_servers=()

    for server in "${SERVERS[@]}"; do
        if process_server "$server"; then
            ((success_count++))
        else
            ((failed_count++))
            failed_servers+=("$server")
        fi
    done

    echo
    echo "================================================================================"
    log "SSH Security Hardening Summary"
    echo "================================================================================"
    success "✓ Successfully hardened: $success_count servers"

    if [[ $failed_count -gt 0 ]]; then
        error "✗ Failed to harden: $failed_count servers"
        error "Failed servers: ${failed_servers[*]}"
    fi

    echo
    log "Hardening completed. All accessible servers now require key-based authentication."
}

# Execute main function
main "$@"
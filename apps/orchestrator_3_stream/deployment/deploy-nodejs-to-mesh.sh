#!/bin/bash

# Deploy Node.js to All Mesh Servers
# This script copies and executes the Node.js installation on all mesh servers
# Usage: ./deploy-nodejs-to-mesh.sh [server_list]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Mesh server list
MESH_SERVERS=(
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
)

# Override with command line arguments if provided
if [ $# -gt 0 ]; then
    MESH_SERVERS=("$@")
fi

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/install-nodejs.sh"

# Check if install script exists
if [ ! -f "$INSTALL_SCRIPT" ]; then
    log_error "Installation script not found: $INSTALL_SCRIPT"
    exit 1
fi

# Results array
declare -a RESULTS

# Function to install on a single server
install_on_server() {
    local server=$1
    log "Installing Node.js on $server..."

    # Test SSH connectivity
    if ! ssh -o ConnectTimeout=5 "$server" "echo 'Connection test successful'" >/dev/null 2>&1; then
        log_error "Cannot connect to $server"
        RESULTS+=("$server: FAILED - Connection error")
        return 1
    fi

    # Check if Node.js is already installed
    local node_check=$(ssh "$server" "bash -l -c 'node --version'" 2>/dev/null || echo "NOT_FOUND")
    if [ "$node_check" != "NOT_FOUND" ]; then
        log_warning "$server already has Node.js $node_check installed"
        RESULTS+=("$server: SKIPPED - Node.js $node_check already installed")
        return 0
    fi

    # Copy installation script
    if ! scp "$INSTALL_SCRIPT" "$server:/tmp/install-nodejs.sh" >/dev/null 2>&1; then
        log_error "Failed to copy installation script to $server"
        RESULTS+=("$server: FAILED - Script copy error")
        return 1
    fi

    # Execute installation
    if ssh "$server" "chmod +x /tmp/install-nodejs.sh && /tmp/install-nodejs.sh" >/dev/null 2>&1; then
        # Verify installation
        local node_version=$(ssh "$server" "bash -l -c 'node --version'" 2>/dev/null || echo "unknown")
        local npm_version=$(ssh "$server" "bash -l -c 'npm --version'" 2>/dev/null || echo "unknown")
        log_success "$server: Node.js $node_version, NPM $npm_version installed successfully"
        RESULTS+=("$server: SUCCESS - Node.js $node_version, NPM $npm_version")

        # Cleanup
        ssh "$server" "rm -f /tmp/install-nodejs.sh" >/dev/null 2>&1
    else
        log_error "Installation failed on $server"
        RESULTS+=("$server: FAILED - Installation error")
        return 1
    fi

    return 0
}

# Main execution
main() {
    log "Starting Node.js deployment to mesh servers..."
    log "Target servers: ${MESH_SERVERS[*]}"
    echo

    # Install on each server
    for server in "${MESH_SERVERS[@]}"; do
        install_on_server "$server"
        echo
    done

    # Summary
    log "Deployment Summary:"
    echo "=================="

    local success_count=0
    local skip_count=0
    local fail_count=0

    for result in "${RESULTS[@]}"; do
        if [[ "$result" == *"SUCCESS"* ]]; then
            log_success "$result"
            ((success_count++))
        elif [[ "$result" == *"SKIPPED"* ]]; then
            log_warning "$result"
            ((skip_count++))
        else
            log_error "$result"
            ((fail_count++))
        fi
    done

    echo
    log "Summary: $success_count successful, $skip_count skipped, $fail_count failed"

    if [ $fail_count -gt 0 ]; then
        log_error "Some installations failed. Check the logs above."
        exit 1
    else
        log_success "Deployment completed successfully!"
    fi
}

# Run main function
main "$@"
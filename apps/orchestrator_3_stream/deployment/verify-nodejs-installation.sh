#!/bin/bash

# Verify Node.js Installation on Mesh Servers
# This script verifies that Node.js is properly installed on mesh servers
# Usage: ./verify-nodejs-installation.sh [server_list]

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

# Function to verify installation on a single server
verify_server() {
    local server=$1

    log "Verifying Node.js installation on $server..."

    # Test SSH connectivity
    if ! ssh -o ConnectTimeout=5 "$server" "echo 'Connection test successful'" >/dev/null 2>&1; then
        log_error "$server: Connection failed"
        return 1
    fi

    # Check Node.js version
    local node_version=$(ssh "$server" "bash -l -c 'node --version'" 2>/dev/null || echo "NOT_FOUND")

    if [ "$node_version" = "NOT_FOUND" ]; then
        log_error "$server: Node.js not found or not in PATH"
        return 1
    fi

    # Check NPM version
    local npm_version=$(ssh "$server" "bash -l -c 'npm --version'" 2>/dev/null || echo "NOT_FOUND")

    if [ "$npm_version" = "NOT_FOUND" ]; then
        log_error "$server: NPM not found or not in PATH"
        return 1
    fi

    # Check NVM version
    local nvm_version=$(ssh "$server" "bash -l -c 'nvm --version'" 2>/dev/null || echo "NOT_FOUND")

    # Check if Node.js is available in login shell (persistence test)
    local login_node_version=$(ssh "$server" "bash -l -c 'source ~/.profile && node --version'" 2>/dev/null || echo "NOT_FOUND")

    # Test npm functionality
    local npm_help_test=$(ssh "$server" "bash -l -c 'npm --help | head -1'" 2>/dev/null || echo "FAILED")

    # Get installation paths
    local node_path=$(ssh "$server" "bash -l -c 'which node'" 2>/dev/null || echo "NOT_FOUND")
    local npm_path=$(ssh "$server" "bash -l -c 'which npm'" 2>/dev/null || echo "NOT_FOUND")

    # Results
    echo "  Node.js Version: $node_version"
    echo "  NPM Version: $npm_version"
    echo "  NVM Version: $nvm_version"
    echo "  Login Shell Node.js: $login_node_version"
    echo "  Node.js Path: $node_path"
    echo "  NPM Path: $npm_path"
    if [[ "$npm_help_test" == *"FAILED"* ]]; then
        npm_test_result="FAIL"
    else
        npm_test_result="PASS"
    fi
    echo "  NPM Help Test: $npm_test_result"

    # Determine overall status
    if [ "$login_node_version" = "NOT_FOUND" ]; then
        log_warning "$server: Node.js installed but not available in login shells"
        return 1
    elif [ "$npm_help_test" = "FAILED" ]; then
        log_warning "$server: Node.js installed but npm has issues"
        return 1
    else
        log_success "$server: All checks passed - Node.js $node_version fully functional"
        return 0
    fi
}

# Main execution
main() {
    log "Verifying Node.js installation on mesh servers..."
    log "Target servers: ${MESH_SERVERS[*]}"
    echo

    local success_count=0
    local total_count=${#MESH_SERVERS[@]}
    local failed_servers=()

    # Verify each server
    for server in "${MESH_SERVERS[@]}"; do
        if verify_server "$server"; then
            ((success_count++))
        else
            failed_servers+=("$server")
        fi
        echo
    done

    # Summary
    log "Verification Summary:"
    echo "==================="
    echo "Total servers checked: $total_count"
    echo "Successful verifications: $success_count"
    echo "Failed verifications: $((total_count - success_count))"
    echo

    if [ ${#failed_servers[@]} -gt 0 ]; then
        log_warning "Servers that need attention:"
        for server in "${failed_servers[@]}"; do
            echo "  - $server"
        done
        echo
        log "To fix these servers, run the installation script manually:"
        for server in "${failed_servers[@]}"; do
            echo "  scp install-nodejs.sh $server:/tmp/ && ssh $server '/tmp/install-nodejs.sh'"
        done
        return 1
    else
        log_success "All servers passed verification!"
        return 0
    fi
}

# Run main function
main "$@"
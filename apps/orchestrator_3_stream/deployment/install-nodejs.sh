#!/bin/bash

# Node.js and NVM Installation Script for Mesh Servers
# This script installs NVM and Node.js LTS on Ubuntu/Debian systems
# Usage: ./install-nodejs.sh

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    log_error "This script should not be run as root. Run as regular user."
    exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    log "Installing curl..."
    sudo apt-get update && sudo apt-get install -y curl
fi

# Install NVM if not already installed
if [ ! -d "$HOME/.nvm" ]; then
    log "Installing NVM (Node Version Manager)..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash

    # Source NVM in current session
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    log_success "NVM installed successfully"
else
    log "NVM already installed at $HOME/.nvm"

    # Source NVM in current session
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

# Add NVM configuration to .profile if not present
if ! grep -q "NVM_DIR" "$HOME/.profile"; then
    log "Adding NVM configuration to ~/.profile..."
    cat >> "$HOME/.profile" << 'EOF'

# NVM configuration
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
EOF
    log_success "NVM configuration added to ~/.profile"
fi

# Install Node.js LTS
log "Installing Node.js LTS..."
nvm install --lts
nvm use --lts
nvm alias default lts/*

# Verify installation
NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
NVM_VERSION=$(nvm --version)

log_success "Installation completed successfully!"
echo
echo "Installed versions:"
echo "  - Node.js: $NODE_VERSION"
echo "  - NPM: $NPM_VERSION"
echo "  - NVM: $NVM_VERSION"
echo
echo "Installation paths:"
echo "  - Node.js: $(which node)"
echo "  - NPM: $(which npm)"
echo "  - NVM: $HOME/.nvm"
echo
log "To use Node.js in your current session, run: source ~/.profile"
log "Or start a new shell session."
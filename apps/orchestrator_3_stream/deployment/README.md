# Node.js Deployment for Mesh Servers

This directory contains scripts and documentation for deploying NVM and Node.js LTS across the mesh server network for Claude Code deployment.

## Files Overview

- **`install-nodejs.sh`** - Standalone script to install NVM and Node.js LTS on a single server
- **`deploy-nodejs-to-mesh.sh`** - Automated deployment script that installs Node.js on all mesh servers
- **`verify-nodejs-installation.sh`** - Verification script to check installations across the network
- **`README.md`** - This documentation file

## Quick Start

### Install on a Single Server

```bash
# Copy the installation script to the target server
scp install-nodejs.sh user@server:/tmp/

# Execute the installation
ssh user@server "/tmp/install-nodejs.sh"
```

### Deploy to All Mesh Servers

```bash
# Deploy to all configured mesh servers (mesh01-mesh13)
./deploy-nodejs-to-mesh.sh

# Deploy to specific servers only
./deploy-nodejs-to-mesh.sh mesh01 mesh02 mesh03
```

### Verify Installations

```bash
# Verify all mesh servers
./verify-nodejs-installation.sh

# Verify specific servers
./verify-nodejs-installation.sh mesh01 mesh02 mesh03
```

## Installation Details

### What Gets Installed

- **NVM (Node Version Manager) v0.40.0** - Latest stable version
- **Node.js v24.11.1 LTS** - Current Long Term Support version
- **NPM v11.6.2** - Comes bundled with Node.js

### Configuration Changes

1. **NVM Configuration** - Added to `~/.profile` for persistence across login shells
2. **Default Node.js Version** - Set to LTS version (`nvm alias default lts/*`)
3. **Environment Variables** - `NVM_DIR` set to `$HOME/.nvm`

### Installation Paths

- **NVM**: `~/.nvm/`
- **Node.js**: `~/.nvm/versions/node/v24.11.1/bin/node`
- **NPM**: `~/.nvm/versions/node/v24.11.1/bin/npm`

## Prerequisites

### System Requirements

- Ubuntu/Debian-based Linux distribution
- SSH access with key-based authentication
- User account with sudo privileges (for installing curl)
- Internet connection for downloading packages

### SSH Configuration

The deployment scripts use SSH aliases configured in `~/.ssh/config`. Ensure your mesh servers are configured:

```bash
# Example SSH config entries
Host mesh01
  HostName 192.168.2.201
  User andre

Host mesh02
  HostName 192.168.2.202
  User andre
```

## Usage Examples

### Manual Installation Steps

If you prefer to install manually:

```bash
# 1. Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash

# 2. Source NVM in current session
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 3. Install Node.js LTS
nvm install --lts
nvm use --lts
nvm alias default lts/*

# 4. Add to ~/.profile for persistence
echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.profile
echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.profile
echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' >> ~/.profile
```

### Testing Installation

```bash
# Test Node.js installation
node --version
npm --version

# Create a test project
mkdir test-project && cd test-project
npm init -y
npm install lodash
node -e "console.log('Node.js works!')"
```

## Troubleshooting

### Common Issues

1. **"nvm: command not found"**
   - Solution: Source the profile with `source ~/.profile` or start a new session
   - Check if NVM is installed: `ls -la ~/.nvm`

2. **"Connection failed" errors**
   - Check SSH connectivity: `ssh mesh01 "echo test"`
   - Verify SSH config entries in `~/.ssh/config`

3. **"Node.js not found in login shells"**
   - Verify `~/.profile` contains NVM configuration
   - Test with: `bash -l -c 'node --version'`

### Verification Commands

```bash
# Check SSH connectivity
for i in {01..13}; do echo -n "mesh$i: "; ssh -o ConnectTimeout=3 mesh$i "echo OK" 2>/dev/null || echo "FAILED"; done

# Check Node.js versions across servers
for i in {01..13}; do echo -n "mesh$i: "; ssh mesh$i "bash -l -c 'node --version'" 2>/dev/null || echo "NOT_INSTALLED"; done

# Verify NVM is sourced properly
ssh mesh01 "bash -l -c 'echo \$NVM_DIR'"
```

## Maintenance

### Updating Node.js

```bash
# Update to latest LTS on a single server
ssh mesh01 "bash -l -c 'nvm install --lts && nvm alias default lts/*'"

# Update all servers (for loop)
for i in {01..13}; do echo "Updating mesh$i..."; ssh mesh$i "bash -l -c 'nvm install --lts && nvm alias default lts/*'"; done
```

### Cleaning Up

```bash
# Remove old Node.js versions
ssh mesh01 "bash -l -c 'nvm ls-remote | grep -v lts | tail -n +2 | awk \"{print \\$1}\" | xargs -I {} nvm uninstall {} 2>/dev/null || true'"

# Clean npm cache
ssh mesh01 "bash -l -c 'npm cache clean --force'"
```

## Security Considerations

- Node.js is installed in user home directory, no system-wide changes
- NVM manages permissions appropriately
- Consider using `.npmrc` for security configurations
- Regularly update Node.js to latest LTS for security patches

## Integration with Claude Code

Once Node.js is installed, your mesh servers will be ready for:

1. **Claude Code Node.js applications** - Deploy and run Node.js-based tools
2. **Package management** - Use npm for installing dependencies
3. **Development environments** - Set up Node.js development workflows
4. **CI/CD pipelines** - Build and deploy Node.js applications
5. **API servers** - Run Node.js microservices and APIs

The installation provides a consistent Node.js environment across all mesh servers, making it easy to deploy Claude Code tools and applications uniformly.
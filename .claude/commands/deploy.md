---
description: Deploy applications to local server network with SSH, Docker, and Git integration
argument-hint: [app-name] [target-servers] [branch]
model: claude-sonnet-4-5-20250929
---

# Deploy to Local Server Network

## Purpose

Deploy applications from andrefortin GitHub repository to your local server network including mesh servers, agenticoverlord.com servers, and DigitalOcean servers with automatic Docker setup and service management.

## Variables

APP_NAME: $1 (required, application name from andrefortin GitHub account)
TARGET_SERVERS: $2 (optional, server list or category)
BRANCH: $3 (optional, git branch to deploy)
GITHUB_USERNAME: andrefortin
SSH_PASSWORD: jkl;jkl;

## Instructions

- All servers have SSH access configured with user andre
- Git is pre-configured for andrefortin GitHub account
- Docker is available on all servers
- Default deployment directory is /opt on target servers
- Always validate deployment success on all target servers

## Server Categories

### **Available Server Categories:**
- **mesh**: All mesh01-mesh13 servers (192.168.2.201-213)
- **mesh-local**: mesh01-mesh10 (local network only)
- **mesh-remote**: mesh11-mesh13 (via agenticoverlord.com)
- **agenticoverlord**: aidev.agenticoverlord.com + mesh11-13.agenticoverlord.com
- **cloudflare**: All agenticoverlord.com servers (Cloudflare tunnel)
- **digitalocean**: do-small and do-medium servers
- **production**: DigitalOcean servers only
- **all**: Deploy to all available servers
- **test**: Deploy to aidev.agenticoverlord.com only

### **Individual Servers:**
- **mesh01** through **mesh13**: Individual mesh servers
- **aidev**: aidev.agenticoverlord.com
- **mesh11-13**: mesh11.agenticoverlord.com through mesh13.agenticoverlord.com
- **do-small**: DigitalOcean small instance
- **do-medium**: DigitalOcean medium instance

## Workflow

### Step 1: Validate Input and Resolve Target Servers
```bash
# Set default values
if [ -z "$TARGET_SERVERS" ]; then
    TARGET_SERVERS="aidev"  # Default to development server
fi

if [ -z "$BRANCH" ]; then
    BRANCH="main"
fi

echo "Deployment Configuration:"
echo "  App: $APP_NAME"
echo "  Branch: $BRANCH"
echo "  Target: $TARGET_SERVERS"

# Resolve server list based on category
declare -a SERVERS=()

case $TARGET_SERVERS in
    "mesh")
        SERVERS=("mesh01" "mesh02" "mesh03" "mesh04" "mesh05" "mesh06" "mesh07" "mesh08" "mesh09" "mesh10" "mesh11" "mesh12" "mesh13")
        ;;
    "mesh-local")
        SERVERS=("mesh01" "mesh02" "mesh03" "mesh04" "mesh05" "mesh06" "mesh07" "mesh08" "mesh09" "mesh10")
        ;;
    "mesh-remote")
        SERVERS=("mesh11" "mesh12" "mesh13")
        ;;
    "agenticoverlord")
        SERVERS=("aidev" "mesh11" "mesh12" "mesh13")
        ;;
    "cloudflare")
        SERVERS=("aidev" "mesh11" "mesh12" "mesh13")
        ;;
    "digitalocean")
        SERVERS=("do-small" "do-medium")
        ;;
    "production")
        SERVERS=("do-medium" "do-small")
        ;;
    "test")
        SERVERS=("aidev")
        ;;
    "all")
        SERVERS=("aidev" "mesh01" "mesh02" "mesh03" "mesh04" "mesh05" "mesh06" "mesh07" "mesh08" "mesh09" "mesh10" "mesh11" "mesh12" "mesh13" "do-small" "do-medium")
        ;;
    *)
        # Assume individual server names provided
        SERVERS=($TARGET_SERVERS)
        ;;
esac

echo "Target servers: ${SERVERS[@]}"
```

### Step 2: Validate GitHub Repository
```bash
# Check if repository exists on GitHub
REPO_URL="https://github.com/$GITHUB_USERNAME/$APP_NAME.git"

if ! curl -s -o /dev/null -w "%{http_code}" "https://github.com/$GITHUB_USERNAME/$APP_NAME" | grep -q "200"; then
    echo "❌ Error: Repository $GITHUB_USERNAME/$APP_NAME not found on GitHub"
    echo "Available repositories:"
    curl -s "https://api.github.com/users/$GITHUB_USERNAME/repos" | jq -r '.[].name' | head -10
    exit 1
fi

echo "✅ Repository validated: $REPO_URL"
```

### Step 3: Pre-Deployment Checks
```bash
# Check SSH connectivity to all servers
FAILED_SERVERS=()
for server in "${SERVERS[@]}"; do
    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $server "echo 'SSH OK'" 2>/dev/null; then
        FAILED_SERVERS+=($server)
        echo "⚠️  Warning: Cannot connect to $server"
    else
        echo "✅ SSH connection OK: $server"
    fi
done

if [ ${#FAILED_SERVERS[@]} -gt 0 ]; then
    echo "❌ Cannot connect to servers: ${FAILED_SERVERS[@]}"
    echo "Continuing with available servers..."
    # Remove failed servers from deployment list
    SERVERS=($(printf "%s\n" "${SERVERS[@]}" | grep -vxF "$(printf "%s\n" "${FAILED_SERVERS[@]}")"))
fi

if [ ${#SERVERS[@]} -eq 0 ]; then
    echo "❌ No servers available for deployment"
    exit 1
fi
```

### Step 4: Deploy to Each Server
```bash
DEPLOYMENT_RESULTS=()

for server in "${SERVERS[@]}"; do
    echo ""
    echo "🚀 Deploying to $server..."
    
    # Execute deployment on target server
    DEPLOY_RESULT=$(ssh $server "
        set -e
        
        echo '📦 Preparing deployment environment...'
        
        # Create deployment directory
        sudo mkdir -p /opt/\$APP_NAME
        sudo chown andre:andre /opt/\$APP_NAME
        cd /opt
        
        # Clone or update repository
        if [ -d \"\$APP_NAME\" ]; then
            echo '📥 Updating existing repository...'
            cd \$APP_NAME
            git fetch origin
            git checkout $BRANCH
            git pull origin $BRANCH
        else
            echo '📥 Cloning repository...'
            git clone https://github.com/$GITHUB_USERNAME/\$APP_NAME.git
            cd \$APP_NAME
            git checkout $BRANCH
        fi
        
        echo '📋 Repository information:'
        echo \"  Branch: \$(git branch --show-current)\"
        echo \"  Commit: \$(git rev-parse --short HEAD)\"
        echo \"  Directory: \$(pwd)\"
        
        # Check for Docker configuration
        if [ -f 'docker-compose.yml' ] || [ -f 'docker-compose.yaml' ]; then
            echo '🐳 Docker deployment detected...'
            
            # Stop existing containers
            docker compose down 2>/dev/null || true
            
            # Build and start services
            docker compose up -d --build
            
            echo '📊 Container status:'
            docker compose ps
            
            # Wait for services to be healthy
            echo '⏳ Waiting for services to start...'
            sleep 10
            
            # Check service health
            if docker compose ps | grep -q 'Up (healthy)'; then
                echo '✅ Services are healthy'
                DEPLOYMENT_STATUS='SUCCESS'
                ERROR_MESSAGE=''
            else
                echo '⚠️  Services may not be fully healthy yet'
                DEPLOYMENT_STATUS='WARNING'
                ERROR_MESSAGE='Services not fully healthy'
            fi
            
        elif [ -f 'package.json' ]; then
            echo '📦 Node.js application detected...'
            
            # Install dependencies
            npm ci --production
            
            # Start application (customize as needed)
            if [ -f 'ecosystem.config.js' ] || [ -f 'ecosystem.config.json' ]; then
                # PM2 deployment
                npm install -g pm2 2>/dev/null || true
                pm2 restart \$APP_NAME 2>/dev/null || pm2 start ecosystem.config.js
                DEPLOYMENT_STATUS='SUCCESS'
                ERROR_MESSAGE=''
            else
                # Simple Node.js start
                nohup npm start > app.log 2>&1 &
                echo \$! > app.pid
                DEPLOYMENT_STATUS='SUCCESS'
                ERROR_MESSAGE=''
            fi
            
        elif [ -f 'requirements.txt' ] || [ -f 'pyproject.toml' ]; then
            echo '🐍 Python application detected...'
            
            # Setup virtual environment
            python3 -m venv venv
            source venv/bin/activate
            
            # Install dependencies
            if [ -f 'requirements.txt' ]; then
                pip install -r requirements.txt
            else
                pip install -e .
            fi
            
            # Start application (customize as needed)
            nohup python main.py > app.log 2>&1 &
            echo \$! > app.pid
            DEPLOYMENT_STATUS='SUCCESS'
            ERROR_MESSAGE=''
            
        else
            echo '⚠️  No recognized deployment configuration found'
            echo 'Available files:'
            ls -la
            DEPLOYMENT_STATUS='ERROR'
            ERROR_MESSAGE='No deployment configuration found'
        fi
        
        echo '📍 Deployment completed'
        echo \"STATUS:\$DEPLOYMENT_STATUS\"
        echo \"ERROR:\$ERROR_MESSAGE\"
        
        # Return deployment result
        echo \"SERVER:$server\"
        echo \"STATUS:\$DEPLOYMENT_STATUS\"
        echo \"ERROR:\$ERROR_MESSAGE\"
        echo \"DIRECTORY:/opt/\$APP_NAME\"
        echo \"TIMESTAMP:\$(date -Iseconds)\"
    " 2>&1)
    
    # Parse deployment result
    SERVER_RESULT=$(echo "$DEPLOY_RESULT" | grep -E "(SERVER|STATUS|ERROR|DIRECTORY|TIMESTAMP)" | paste -sd " " -)
    DEPLOYMENT_RESULTS+=("$SERVER_RESULT")
    
    # Show deployment summary for this server
    echo "📋 Deployment summary for $server:"
    echo "$DEPLOY_RESULT" | grep -E "(STATUS|ERROR|DIRECTORY)" | sed 's/STATUS:/📊 Status:/' | sed 's/ERROR:/❌ Error:/' | sed 's/DIRECTORY:/📁 Directory:/'
    echo ""
done
```

### Step 5: Generate Deployment Report
```bash
echo "🎯 DEPLOYMENT SUMMARY"
echo "===================="
echo ""
echo "Application: $APP_NAME"
echo "Branch: $BRANCH"
echo "Repository: https://github.com/$GITHUB_USERNAME/$APP_NAME.git"
echo "Deployed to: ${#SERVERS[@]} servers"
echo ""

echo "SERVER RESULTS:"
echo "---------------"

SUCCESS_COUNT=0
WARNING_COUNT=0
ERROR_COUNT=0

for result in "${DEPLOYMENT_RESULTS[@]}"; do
    if [[ $result == *"STATUS:SUCCESS"* ]]; then
        echo "✅ $result"
        ((SUCCESS_COUNT++))
    elif [[ $result == *"STATUS:WARNING"* ]]; then
        echo "⚠️  $result"
        ((WARNING_COUNT++))
    elif [[ $result == *"STATUS:ERROR"* ]]; then
        echo "❌ $result"
        ((ERROR_COUNT++))
    fi
done

echo ""
echo "STATISTICS:"
echo "-----------"
echo "Successful: $SUCCESS_COUNT"
echo "Warnings: $WARNING_COUNT"
echo "Errors: $ERROR_COUNT"
echo ""

if [ $ERROR_COUNT -gt 0 ]; then
    echo "❌ Deployment completed with errors"
    exit 1
elif [ $WARNING_COUNT -gt 0 ]; then
    echo "⚠️  Deployment completed with warnings"
else
    echo "✅ Deployment completed successfully"
fi

echo ""
echo "📊 NEXT STEPS:"
echo "1. Test application endpoints on deployed servers"
echo "2. Monitor application logs and performance"
echo "3. Update load balancer if using multiple servers"
echo "4. Configure monitoring and alerting as needed"
```

## Report

### Deployment Completed
- **Application**: $APP_NAME from andrefortin GitHub repository
- **Branch**: $BRANCH
- **Target Servers**: ${#SERVERS[@]} servers deployed
- **Success Rate**: [Calculated from results]

### Server Deployment Details

#### Successful Deployments
[List of servers with successful deployments and access information]

#### Warnings/Issues
[List of any warnings or issues encountered during deployment]

#### Access Information
```markdown
## Application Access
- **aidev.agenticoverlord.com**: http://aidev.agenticoverlord.com:[port]
- **mesh01**: http://192.168.2.201:[port]
- **mesh02**: http://192.168.2.202:[port]
[... and so on for each deployed server]

## SSH Access
```bash
# Access deployed application
ssh mesh01 "cd /opt/$APP_NAME && docker compose logs"

# Check service status
ssh mesh01 "docker ps | grep $APP_NAME"
```

## Monitoring Commands
```bash
# Check all deployed services
for server in mesh01 mesh02 mesh03; do
    echo "=== $server ==="
    ssh $server "docker compose -f /opt/$APP_NAME/docker-compose.yml ps"
done
```

### Post-Deployment Actions
- **Health Checks**: Verify application is responding on all servers
- **Load Testing**: Test application performance under load
- **Monitoring Setup**: Configure monitoring and alerting
- **Backup Strategy**: Implement backup procedures

### Scaling Recommendations

- **For High Traffic**: Deploy to mesh01-mesh05 with load balancer
- **For Development**: Use aidev.agenticoverlord.com for testing
- **For Production**: Use DigitalOcean servers (do-medium, do-small)

### Troubleshooting

#### SSH Connection Issues
```bash
# Test SSH connectivity
ssh -o ConnectTimeout=5 $SERVER "echo 'OK'"

# Check SSH config
grep -A 5 "$SERVER" ~/.ssh/config
```

#### Docker Issues
```bash
# Check Docker status on server
ssh $SERVER "docker ps && docker compose ls"

# View application logs
ssh $SERVER "cd /opt/$APP_NAME && docker compose logs"
```

#### Service Issues
```bash
# Restart services on specific server
ssh $SERVER "cd /opt/$APP_NAME && docker compose restart"

# Redeploy to specific server
ssh $SERVER "
cd /opt && rm -rf $APP_NAME
git clone https://github.com/$GITHUB_USERNAME/$APP_NAME.git
cd $APP_NAME && git checkout $BRANCH
docker compose up -d
"
```

## Server-Specific Notes

### Mesh Servers (192.168.2.x)
- **High Performance**: Local network, low latency
- **Full Control**: Complete administrative access
- **Resource Sharing**: Share resources with other applications

### AgenticOverlord Servers
- **Remote Access**: Cloudflare tunnel for secure access
- **Development Focus**: Ideal for testing and staging
- **Internet Access**: Direct internet connectivity

### DigitalOcean Servers
- **Production Ready**: Professional hosting environment
- **Scalability**: Easy scaling and resource management
- **Reliability**: 99.99% uptime SLA

Remember to always test deployments thoroughly and monitor application performance after deployment.

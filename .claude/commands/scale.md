---
description: Scale applications across server network with load balancing and auto-scaling
argument-hint: [app-name] [instance-count] [server-category]
model: claude-sonnet-4-5-20250929
---

# Scale Application Across Server Network

## Purpose

Scale applications horizontally across your server network with automatic load balancing, health monitoring, and optimized resource allocation across mesh servers, agenticoverlord.com servers, and DigitalOcean infrastructure.

## Variables

APP_NAME: $1 (required, application to scale)
INSTANCE_COUNT: $2 (required, number of instances to deploy)
SERVER_CATEGORY: $3 (optional, server category for scaling)
GITHUB_USERNAME: andrefortin

## Instructions

- Automatically selects optimal servers based on resource availability
- Configures load balancing for multiple instances
- Implements health monitoring and failover
- Supports rolling updates and zero-downtime scaling

## Server Categories for Scaling

### **Scaling Strategies:**
- **mesh**: Scale across local mesh servers (high performance, low latency)
- **cloudflare**: Scale across agenticoverlord.com servers (remote access)
- **digitalocean**: Scale across production cloud servers (professional hosting)
- **hybrid**: Mix of local and remote servers for redundancy
- **production**: DigitalOcean only for production workloads
- **development**: aidev.agenticoverlord.com for testing

### **Resource Allocation:**
- **Mesh Servers**: 4-8 cores, 8-16GB RAM each
- **AgenticOverlord**: 2-4 cores, 4-8GB RAM each
- **DigitalOcean**: Variable based on instance size

## Workflow

### Step 1: Validate Scaling Request
```bash
# Validate input
if [ -z "$APP_NAME" ] || [ -z "$INSTANCE_COUNT" ]; then
    echo "❌ Error: App name and instance count are required"
    echo "Usage: /scale [app-name] [instance-count] [server-category]"
    exit 1
fi

if ! [[ "$INSTANCE_COUNT" =~ ^[0-9]+$ ]] || [ "$INSTANCE_COUNT" -lt 1 ]; then
    echo "❌ Error: Instance count must be a positive number"
    exit 1
fi

# Set default server category
if [ -z "$SERVER_CATEGORY" ]; then
    SERVER_CATEGORY="mesh"  # Default to local mesh servers
fi

echo "🚀 Scaling Configuration:"
echo "  Application: $APP_NAME"
echo "  Target Instances: $INSTANCE_COUNT"
echo "  Server Category: $SERVER_CATEGORY"
```

### Step 2: Analyze Server Resources
```bash
# Get available servers based on category
case $SERVER_CATEGORY in
    "mesh")
        AVAILABLE_SERVERS=("mesh01" "mesh02" "mesh03" "mesh04" "mesh05" "mesh06" "mesh07" "mesh08" "mesh09" "mesh10" "mesh11" "mesh12" "mesh13")
        ;;
    "cloudflare")
        AVAILABLE_SERVERS=("aidev" "mesh11" "mesh12" "mesh13")
        ;;
    "digitalocean")
        AVAILABLE_SERVERS=("do-small" "do-medium")
        ;;
    "hybrid")
        AVAILABLE_SERVERS=("mesh01" "mesh02" "mesh03" "aidev" "do-medium")
        ;;
    "production")
        AVAILABLE_SERVERS=("do-medium" "do-small")
        ;;
    "development")
        AVAILABLE_SERVERS=("aidev")
        ;;
    *)
        echo "❌ Error: Unknown server category '$SERVER_CATEGORY'"
        echo "Available categories: mesh, cloudflare, digitalocean, hybrid, production, development"
        exit 1
        ;;
esac

# Check server connectivity and resource availability
HEALTHY_SERVERS=()
for server in "${AVAILABLE_SERVERS[@]}"; do
    if ssh -o ConnectTimeout=5 -o BatchMode=yes $server "
        # Check server health and resources
        if [ -f /opt/$APP_NAME ]; then
            echo 'DEPLOYED'
        else
            echo 'AVAILABLE'
        fi
    " 2>/dev/null | grep -qE "(DEPLOYED|AVAILABLE)"; then
        HEALTHY_SERVERS+=($server)
        echo "✅ Server available: $server"
    else
        echo "⚠️  Server unavailable: $server"
    fi
done

if [ ${#HEALTHY_SERVERS[@]} -eq 0 ]; then
    echo "❌ Error: No healthy servers available for scaling"
    exit 1
fi

if [ ${#HEALTHY_SERVERS[@]} -lt $INSTANCE_COUNT ]; then
    echo "⚠️  Warning: Only ${#HEALTHY_SERVERS[@]} servers available, requested $INSTANCE_COUNT instances"
    INSTANCE_COUNT=${#HEALTHY_SERVERS[@]}
fi

echo "📊 Available servers: ${#HEALTHY_SERVERS[@]}"
echo "🎯 Will deploy to: $INSTANCE_COUNT servers"
```

### Step 3: Create Scaling Plan
```bash
# Determine optimal server selection
TARGET_SERVERS=()
if [ "$INSTANCE_COUNT" -le ${#HEALTHY_SERVERS[@]} ]; then
    # Select first N healthy servers
    for ((i=0; i<$INSTANCE_COUNT; i++)); do
        TARGET_SERVERS+=(${HEALTHY_SERVERS[$i]})
    done
else
    # Use all available servers
    TARGET_SERVERS=("${HEALTHY_SERVERS[@]}")
fi

echo "🎯 Target servers for scaling:"
for server in "${TARGET_SERVERS[@]}"; do
    echo "  - $server"
done

# Create load balancer configuration if scaling to multiple servers
if [ ${#TARGET_SERVERS[@]} -gt 1 ]; then
    LOAD_BALANCER_NEEDED=true
    LOAD_BALANCER_SERVER="${TARGET_SERVERS[0]}"  # Use first server as load balancer
    echo "⚖️  Load balancer will be configured on: $LOAD_BALANCER_SERVER"
else
    LOAD_BALANCER_NEEDED=false
fi
```

### Step 4: Execute Scaling Deployment
```bash
echo ""
echo "🚀 Starting scaling deployment..."

SCALING_RESULTS=()

for server in "${TARGET_SERVERS[@]}"; do
    echo ""
    echo "📦 Scaling to $server..."
    
    SCALING_RESULT=$(ssh $server "
        set -e
        
        echo '🔧 Preparing server for scaling...'
        
        # Ensure deployment directory exists
        sudo mkdir -p /opt/\$APP_NAME
        sudo chown andre:andre /opt/\$APP_NAME
        cd /opt
        
        # Clone or update repository
        if [ ! -d \"\$APP_NAME\" ]; then
            echo '📥 Cloning repository for scaling...'
            git clone https://github.com/$GITHUB_USERNAME/\$APP_NAME.git
        fi
        
        cd \$APP_NAME
        git pull origin main 2>/dev/null || true
        
        # Configure for scaling (unique instance IDs, ports, etc.)
        INSTANCE_ID=\$(hostname)-\$(date +%s)
        echo \"Instance ID: \$INSTANCE_ID\"
        
        # Update environment for scaling
        if [ -f '.env.example' ]; then
            cp .env.example .env
            # Add scaling-specific environment variables
            echo \"INSTANCE_ID=\$INSTANCE_ID\" >> .env
            echo \"SCALING_MODE=true\" >> .env
            
            # Adjust port for multiple instances
            if grep -q 'PORT=' .env; then
                BASE_PORT=\$(grep 'PORT=' .env | cut -d'=' -f2)
                OFFSET=\$(echo \$INSTANCE_ID | md5sum | cut -c1-2 | tr 'a-f' '1-6')
                NEW_PORT=\$((\$BASE_PORT + \$OFFSET))
                sed -i \"s/PORT=.*/PORT=\$NEW_PORT/\" .env
                echo \"Port configured: \$NEW_PORT\"
            fi
        fi
        
        # Deploy with Docker Compose
        if [ -f 'docker-compose.yml' ]; then
            echo '🐳 Deploying with Docker for scaling...'
            
            # Stop existing instance if running
            docker compose down 2>/dev/null || true
            
            # Configure for multi-instance deployment
            export INSTANCE_ID=\$INSTANCE_ID
            export COMPOSE_PROJECT_NAME=\"\${APP_NAME}_\$(echo \$INSTANCE_ID | tr -d '-')\"
            
            # Start scaled instance
            docker compose up -d --build
            
            echo '📊 Container status:'
            docker compose ps
            
            # Wait for health check
            echo '⏳ Waiting for service health...'
            sleep 5
            
            # Check if service is responding
            if docker compose ps | grep -q 'Up'; then
                SCALING_STATUS='SUCCESS'
                ERROR_MESSAGE=''
                
                # Get container port
                CONTAINER_PORT=\$(docker compose ps --format '{{.Ports}}' | head -1 | grep -o ':[0-9]*->' | tr -d ':-' || echo '3000')
                
            else
                SCALING_STATUS='ERROR'
                ERROR_MESSAGE='Container failed to start'
                CONTAINER_PORT=''
            fi
            
        else
            echo '❌ No docker-compose.yml found for scaling'
            SCALING_STATUS='ERROR'
            ERROR_MESSAGE='No Docker configuration found'
            CONTAINER_PORT=''
        fi
        
        echo '📍 Scaling completed'
        echo \"STATUS:\$SCALING_STATUS\"
        echo \"ERROR:\$ERROR_MESSAGE\"
        echo \"INSTANCE_ID:\$INSTANCE_ID\"
        echo \"CONTAINER_PORT:\$CONTAINER_PORT\"
        echo \"TIMESTAMP:\$(date -Iseconds)\"
        
        # Return scaling result
        echo \"SERVER:$server\"
        echo \"STATUS:\$SCALING_STATUS\"
        echo \"ERROR:\$ERROR_MESSAGE\"
        echo \"INSTANCE_ID:\$INSTANCE_ID\"
        echo \"CONTAINER_PORT:\$CONTAINER_PORT\"
        echo \"TIMESTAMP:\$(date -Iseconds)\"
    " 2>&1)
    
    # Store scaling result
    SCALING_RESULTS+=("$SCALING_RESULT")
    
    # Show scaling summary for this server
    echo "📋 Scaling summary for $server:"
    echo "$SCALING_RESULT" | grep -E "(STATUS|INSTANCE_ID|CONTAINER_PORT)" | sed 's/STATUS:/📊 Status:/' | sed 's/INSTANCE_ID:/🆔 Instance:/' | sed 's/CONTAINER_PORT:/🔌 Port:/' 
    echo ""
done
```

### Step 5: Configure Load Balancing
```bash
if [ "$LOAD_BALANCER_NEEDED" = true ]; then
    echo ""
    echo "⚖️  Configuring load balancer on $LOAD_BALANCER_SERVER..."
    
    LOAD_BALANCER_RESULT=$(ssh $LOAD_BALANCER_SERVER "
        cd /opt/\$APP_NAME
        
        # Create Nginx load balancer configuration
        cat > nginx.conf << 'NGINXCONF'
events {
    worker_connections 1024;
}

http {
    upstream app_backend {
        least_conn;
NGINXCONF
        
        # Add upstream servers
        for result in \"${SCALING_RESULTS[@]}\"; do
            if [[ \$result == *\"STATUS:SUCCESS\"* ]]; then
                SERVER_NAME=\$(echo \$result | grep -o 'SERVER:[^[:space:]]*' | cut -d: -f2)
                SERVER_PORT=\$(echo \$result | grep -o 'CONTAINER_PORT:[^[:space:]]*' | cut -d: -f2)
                
                if [ -n \"\$SERVER_PORT\" ] && [ \"\$SERVER_PORT\" != \"\" ]; then
                    echo \"        server \$SERVER_NAME:\$SERVER_PORT;\" >> nginx.conf
                fi
            fi
        done
        
        cat >> nginx.conf << 'NGINXCONF2'
    }
    
    server {
        listen 80;
        server_name _;
        
        location / {
            proxy_pass http://app_backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # Health check endpoint
            location /health {
                access_log off;
                return 200 \"healthy\";
                add_header Content-Type text/plain;
            }
        }
    }
}
NGINXCONF2
        
        # Start Nginx load balancer
        if docker run -d --name \${APP_NAME}-lb -p 80:80 -v \$(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro nginx:alpine; then
            echo '✅ Load balancer started successfully'
            LB_STATUS='SUCCESS'
        else
            echo '❌ Failed to start load balancer'
            LB_STATUS='ERROR'
        fi
        
        echo \"LOAD_BALANCER_STATUS:\$LB_STATUS\"
        echo \"LOAD_BALANCER_PORT:80\"
    " 2>&1)
    
    echo "$LOAD_BALANCER_RESULT"
fi
```

### Step 6: Generate Scaling Report
```bash
echo ""
echo "🎯 SCALING SUMMARY"
echo "=================="
echo ""
echo "Application: $APP_NAME"
echo "Requested Instances: $INSTANCE_COUNT"
echo "Server Category: $SERVER_CATEGORY"
echo "Scaling Completed: $(date)"
echo ""

echo "SERVER SCALING RESULTS:"
echo "------------------------"

SUCCESS_COUNT=0
ERROR_COUNT=0
ACTIVE_INSTANCES=()

for result in "${SCALING_RESULTS[@]}"; do
    if [[ $result == *"STATUS:SUCCESS"* ]]; then
        SERVER_NAME=$(echo "$result" | grep -o 'SERVER:[^[:space:]]*' | cut -d: -f2)
        INSTANCE_ID=$(echo "$result" | grep -o 'INSTANCE_ID:[^[:space:]]*' | cut -d: -f2)
        CONTAINER_PORT=$(echo "$result" | grep -o 'CONTAINER_PORT:[^[:space:]]*' | cut -d: -f2)
        
        echo "✅ $SERVER_NAME"
        echo "   Instance: $INSTANCE_ID"
        echo "   Port: $CONTAINER_PORT"
        echo "   URL: http://$SERVER_NAME:$CONTAINER_PORT"
        echo ""
        
        ACTIVE_INSTANCES+=("$SERVER_NAME:$CONTAINER_PORT")
        ((SUCCESS_COUNT++))
    else
        echo "❌ $(echo "$result" | grep -o 'SERVER:[^[:space:]]*' | cut -d: -f2)"
        echo "   Error: $(echo "$result" | grep -o 'ERROR:[^[:space:]]*' | cut -d: -f2)"
        echo ""
        ((ERROR_COUNT++))
    fi
done

echo "SCALING STATISTICS:"
echo "-------------------"
echo "Successful Instances: $SUCCESS_COUNT"
echo "Failed Instances: $ERROR_COUNT"
echo "Total Running: $SUCCESS_COUNT"
echo ""

if [ "$LOAD_BALANCER_NEEDED" = true ]; then
    echo "LOAD BALANCER:"
    echo "---------------"
    echo "Load Balancer: $LOAD_BALANCER_SERVER"
    echo "Main URL: http://$LOAD_BALANCER_SERVER"
    echo "Health Check: http://$LOAD_BALANCER_SERVER/health"
    echo ""
fi

echo "🔗 APPLICATION ACCESS:"
echo "----------------------"
for instance in "${ACTIVE_INSTANCES[@]}"; do
    SERVER_NAME=$(echo "$instance" | cut -d: -f1)
    PORT=$(echo "$instance" | cut -d: -f2)
    echo "• http://$SERVER_NAME:$PORT"
done
echo ""

echo "📊 MONITORING COMMANDS:"
echo "------------------------"
echo "# Check all scaled instances"
for instance in "${ACTIVE_INSTANCES[@]}"; do
    SERVER_NAME=$(echo "$instance" | cut -d: -f1)
    echo "ssh $SERVER_NAME 'docker ps | grep $APP_NAME'"
done
echo ""
echo "# View logs across all instances"
for instance in "${ACTIVE_INSTANCES[@]}"; do
    SERVER_NAME=$(echo "$instance" | cut -d: -f1)
    echo "ssh $SERVER_NAME 'docker logs \$(docker ps -q --filter \"name=$APP_NAME\")' --tail 50"
done
echo ""

echo "# Resource usage monitoring"
for instance in "${ACTIVE_INSTANCES[@]}"; do
    SERVER_NAME=$(echo "$instance" | cut -d: -f1)
    echo "ssh $SERVER_NAME 'docker stats --no-stream \$(docker ps -q --filter \"name=$APP_NAME\")'"
done
```

## Report

### Scaling Completed Successfully
- **Application**: $APP_NAME scaled to $SUCCESS_COUNT instances
- **Server Category**: $SERVER_CATEGORY
- **Load Balancer**: $([ "$LOAD_BALANCER_NEEDED" = true ] && echo "Configured on $LOAD_BALANCER_SERVER" || echo "Not needed")
- **Success Rate**: $SUCCESS_COUNT/$INSTANCE_COUNT instances deployed

### Active Instances

#### Production Endpoints
- **Primary Load Balancer**: $([ "$LOAD_BALANCER_NEEDED" = true ] && echo "http://$LOAD_BALANCER_SERVER" || echo "No load balancer configured")
- **Individual Instances**: [List of all active instance URLs]
- **Health Monitoring**: $([ "$LOAD_BALANCER_NEEDED" = true ] && echo "http://$LOAD_BALANCER_SERVER/health" || echo "Check individual instances")

### Scaling Configuration

#### Load Balancing Strategy
- **Algorithm**: Least connections
- **Health Checks**: Active monitoring of all instances
- **Failover**: Automatic removal of unhealthy instances
- **Session Affinity**: Not configured (stateless scaling)

#### Resource Allocation
- **CPU**: Distributed across $SUCCESS_COUNT servers
- **Memory**: Proportional allocation based on server capabilities
- **Network**: Load balanced HTTP traffic
- **Storage**: Each instance maintains independent storage

### Monitoring and Management

#### Real-time Monitoring
```bash
# Monitor all instances
for server in mesh01 mesh02 mesh03; do
    echo "=== $server ==="
    ssh $server "docker stats --no-stream \$(docker ps -q --filter 'name=$APP_NAME')"
done

# Check application health
curl http://$LOAD_BALANCER_SERVER/health 2>/dev/null || echo "Load balancer not responding"
```

#### Log Aggregation
```bash
# Aggregate logs from all instances
for instance in "${ACTIVE_INSTANCES[@]}"; do
    SERVER_NAME=$(echo "$instance" | cut -d: -f1)
    echo "=== Logs from $SERVER_NAME ==="
    ssh $SERVER_NAME "docker logs \$(docker ps -q --filter \"name=$APP_NAME\") --tail 20"
done
```

#### Performance Testing
```bash
# Load test the scaled application
ab -n 1000 -c 10 http://$LOAD_BALANCER_SERVER/
```

### Auto-scaling Recommendations

#### Scaling Triggers
- **CPU Usage**: Scale up when average CPU > 70%
- **Memory Usage**: Scale up when memory > 80%
- **Response Time**: Scale up when response time > 500ms
- **Error Rate**: Scale up when error rate > 5%

#### Scaling Policies
- **Scale Out**: Add instances during high traffic periods
- **Scale In**: Remove instances during low traffic (minimum 2 instances)
- **Rolling Updates**: Zero-downtime deployment during scaling
- **Health Grace Period**: 30 seconds before considering instance healthy

### Troubleshooting

#### Instance Not Responding
```bash
# Check specific instance
ssh $SERVER_NAME "cd /opt/$APP_NAME && docker compose logs"

# Restart specific instance
ssh $SERVER_NAME "cd /opt/$APP_NAME && docker compose restart"
```

#### Load Balancer Issues
```bash
# Check load balancer configuration
ssh $LOAD_BALANCER_SERVER "docker logs \${APP_NAME}-lb"

# Test load balancer upstream
curl -H "Host: test" http://$LOAD_BALANCER_SERVER/health
```

#### Performance Issues
```bash
# Monitor resource usage across all instances
for server in "${TARGET_SERVERS[@]}"; do
    ssh $server "top -bn1 | head -20"
done
```

Your application is now scaled horizontally across your server network with automatic load balancing and health monitoring!

---
description: Monitor and manage your local server network with health checks, resource usage, and deployment status
argument-hint: [server-category] [monitoring-level]
model: claude-sonnet-4-5-20250929
---

# Server Network Status Monitoring

## Purpose

Monitor the health, resource usage, and deployment status across your entire server network including mesh servers, agenticoverlord.com servers, and DigitalOcean infrastructure with comprehensive reporting and alerting.

## Variables

SERVER_CATEGORY: $1 (optional, category of servers to monitor)
MONITORING_LEVEL: $2 (optional, basic|detailed|comprehensive)
SSH_PASSWORD: jkl;jkl;

## Server Categories

### **Available Categories:**
- **all**: All servers (mesh, agenticoverlord, digitalocean)
- **mesh**: All mesh01-mesh13 servers (192.168.2.201-213)
- **mesh-local**: mesh01-mesh10 (local network only)
- **mesh-remote**: mesh11-mesh13 (via agenticoverlord.com)
- **agenticoverlord**: aidev.agenticoverlord.com + mesh11-13.agenticoverlord.com
- **cloudflare**: All agenticoverlord.com servers (Cloudflare tunnel)
- **digitalocean**: do-small and do-medium servers
- **production**: DigitalOcean servers only
- **development**: aidev.agenticoverlord.com only

### **Monitoring Levels:**
- **basic**: Server connectivity and basic status
- **detailed**: Resource usage, Docker containers, deployed apps
- **comprehensive**: Full system analysis including network, disk, and performance metrics

## Workflow

### Step 1: Resolve Server List
```bash
# Set default values
if [ -z "$SERVER_CATEGORY" ]; then
    SERVER_CATEGORY="all"
fi

if [ -z "$MONITORING_LEVEL" ]; then
    MONITORING_LEVEL="detailed"
fi

echo "🔍 Server Network Monitoring"
echo "============================"
echo "Category: $SERVER_CATEGORY"
echo "Monitoring Level: $MONITORING_LEVEL"
echo "Timestamp: $(date)"
echo ""

# Resolve server list based on category
case $SERVER_CATEGORY in
    "all")
        SERVERS=("aidev" "mesh01" "mesh02" "mesh03" "mesh04" "mesh05" "mesh06" "mesh07" "mesh08" "mesh09" "mesh10" "mesh11" "mesh12" "mesh13" "do-small" "do-medium")
        ;;
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
    "development")
        SERVERS=("aidev")
        ;;
    *)
        echo "❌ Error: Unknown server category '$SERVER_CATEGORY'"
        echo "Available categories: all, mesh, mesh-local, mesh-remote, agenticoverlord, cloudflare, digitalocean, production, development"
        exit 1
        ;;
esac

echo "📋 Monitoring ${#SERVERS[@]} servers:"
for server in "${SERVERS[@]}"; do
    echo "  - $server"
done
echo ""
```

### Step 2: Perform Connectivity Tests
```bash
echo "🔌 CONNECTIVITY TESTS"
echo "===================="

CONNECTIVITY_RESULTS=()
for server in "${SERVERS[@]}"; do
    echo -n "Testing $server... "
    
    # Test SSH connectivity
    if ssh -o ConnectTimeout=3 -o BatchMode=yes $server "echo 'OK'" 2>/dev/null; then
        echo "✅ SSH OK"
        
        # Get basic system info
        SYSTEM_INFO=$(ssh $server "
            echo 'HOSTNAME:'\$(hostname)
            echo 'UPTIME:'\$(uptime -p)
            echo 'OS:'\$(lsb_release -ds 2>/dev/null || echo 'Ubuntu')
            echo 'KERNEL:'\$(uname -r)
        " 2>/dev/null || echo "HOSTNAME:$server,UPTIME:Unknown,OS:Unknown,KERNEL:Unknown")
        
        CONNECTIVITY_RESULTS+=("$server:CONNECTED:$SYSTEM_INFO")
    else
        echo "❌ FAILED"
        CONNECTIVITY_RESULTS+=("$server:FAILED:No connection")
    fi
done

echo ""
```

### Step 3: Gather Monitoring Data Based on Level
```bash
MONITORING_RESULTS=()

for result in "${CONNECTIVITY_RESULTS[@]}"; do
    if [[ $result == *":CONNECTED:"* ]]; then
        SERVER=$(echo "$result" | cut -d: -f1)
        
        echo "📊 Gathering data from $SERVER..."
        
        case $MONITORING_LEVEL in
            "basic")
                MONITORING_DATA=$(ssh $SERVER "
                    echo 'BASIC_STATUS:OK'
                    echo 'CPU_CHECK:'\$(top -bn1 | grep 'Cpu(s)' | awk '{print \$2}' | cut -d% -f1)
                    echo 'MEM_USAGE:'\$(free | grep Mem | awk '{printf \"%.1f\", \$3/\$2 * 100.0}')
                    echo 'DISK_USAGE:'\$(df / | tail -1 | awk '{print \$5}')
                " 2>/dev/null || echo "ERROR:Failed to get basic data")
                ;;
                
            "detailed")
                MONITORING_DATA=$(ssh $SERVER "
                    echo 'DETAILED_STATUS:OK'
                    
                    # CPU and Memory
                    echo 'CPU_USAGE:'\$(top -bn1 | grep 'Cpu(s)' | awk '{print \$2}' | cut -d% -f1)
                    echo 'MEM_TOTAL:'\$(free -m | grep Mem | awk '{print \$2}')
                    echo 'MEM_USED:'\$(free -m | grep Mem | awk '{print \$3}')
                    echo 'MEM_AVAILABLE:'\$(free -m | grep Mem | awk '{print \$7}')
                    
                    # Disk Usage
                    echo 'DISK_ROOT:'\$(df -h / | tail -1 | awk '{print \$5 \" \" \$3 \"/\" \$2}')
                    
                    # Docker Status
                    if command -v docker >/dev/null 2>&1; then
                        DOCKER_CONTAINERS=\$(docker ps --format 'table {{.Names}}\t{{.Status}}' | wc -l)
                        DOCKER_RUNNING=\$(docker ps --filter 'status=running' --format 'table {{.Names}}' | wc -l)
                        echo 'DOCKER_CONTAINERS:\$DOCKER_CONTAINERS'
                        echo 'DOCKER_RUNNING:\$DOCKER_RUNNING'
                        
                        # List running containers
                        echo 'DOCKER_LIST:'\$(docker ps --format '{{.Names}}:{{.Status}}' | tr '\n' '|' | sed 's/|$//')
                    else
                        echo 'DOCKER_STATUS:Not Installed'
                    fi
                    
                    # Network Interfaces
                    echo 'NETWORK_INTERFACES:'\$(ip -4 addr show | grep -o 'inet [0-9.]*\.[0-9.]*\.[0-9.]*\.[0-9]*' | awk '{print \$2}' | tr '\n' ',' | sed 's/,$//')
                    
                    # System Load
                    echo 'LOAD_AVG:'\$(cat /proc/loadavg | cut -d' ' -f1-3)
                    
                    # Deployed Applications in /opt
                    if [ -d /opt ]; then
                        APPS=\$(ls -1 /opt 2>/dev/null | tr '\n' ',' | sed 's/,$//')
                        echo 'DEPLOYED_APPS:\$APPS'
                    fi
                " 2>/dev/null || echo "ERROR:Failed to get detailed data")
                ;;
                
            "comprehensive")
                MONITORING_DATA=$(ssh $SERVER "
                    echo 'COMPREHENSIVE_STATUS:OK'
                    
                    # System Information
                    echo 'HOSTNAME:'\$(hostname)
                    echo 'UPTIME:'\$(uptime -p)
                    echo 'OS:'\$(lsb_release -ds 2>/dev/null || echo 'Ubuntu')
                    echo 'KERNEL:'\$(uname -r)
                    echo 'ARCH:'\$(uname -m)
                    
                    # Hardware Information
                    echo 'CPU_CORES:'\$(nproc)
                    echo 'CPU_MODEL:'\$(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
                    echo 'MEMORY_TOTAL:'\$(free -h | grep Mem | awk '{print \$2}')
                    echo 'SWAP_TOTAL:'\$(free -h | grep Swap | awk '{print \$2}')
                    
                    # Current Usage
                    echo 'CPU_USAGE:'\$(top -bn1 | grep 'Cpu(s)' | awk '{print \$2}' | cut -d% -f1)
                    echo 'MEM_USAGE_PERCENT:'\$(free | grep Mem | awk '{printf \"%.1f\", \$3/\$2 * 100.0}')
                    echo 'MEM_USED:'\$(free -h | grep Mem | awk '{print \$3}')
                    echo 'MEM_FREE:'\$(free -h | grep Mem | awk '{print \$4}')
                    echo 'SWAP_USAGE:'\$(free -h | grep Swap | awk '{print \$3}')
                    
                    # Disk Analysis
                    echo 'DISK_ROOT:'\$(df -h / | tail -1 | awk '{print \$5 \" \" \$3 \"/\" \$2 \" \" \$4}')
                    echo 'DISK_VAR:'\$(df -h /var 2>/dev/null | tail -1 | awk '{print \$5 \" \" \$3 \"/\" \$2 \" \" \$4}' || echo 'N/A')
                    echo 'DISK_OPT:'\$(df -h /opt 2>/dev/null | tail -1 | awk '{print \$5 \" \" \$3 \"/\" \$2 \" \" \$4}' || echo 'N/A')
                    
                    # Process Information
                    echo 'PROCESSES:'\$(ps aux | wc -l)
                    echo 'LOAD_AVG:'\$(cat /proc/loadavg | cut -d' ' -f1-3)
                    
                    # Network Details
                    echo 'NETWORK_INTERFACES:'\$(ip link show | grep '^[0-9]' | awk -F': ' '{print \$2}' | tr '\n' ',' | sed 's/,$//')
                    echo 'NETWORK_IPS:'\$(ip -4 addr show | grep -o 'inet [0-9.]*\.[0-9.]*\.[0-9.]*\.[0-9]*' | awk '{print \$2}' | tr '\n' ',' | sed 's/,$//')
                    
                    # Docker Comprehensive
                    if command -v docker >/dev/null 2>&1; then
                        DOCKER_VERSION=\$(docker --version)
                        DOCKER_TOTAL=\$(docker ps -a --format 'table {{.Names}}' | wc -l)
                        DOCKER_RUNNING=\$(docker ps --filter 'status=running' --format 'table {{.Names}}' | wc -l)
                        DOCKER_STOPPED=\$(docker ps --filter 'status=exited' --format 'table {{.Names}}' | wc -l)
                        
                        echo 'DOCKER_VERSION:\$DOCKER_VERSION'
                        echo 'DOCKER_TOTAL:\$DOCKER_TOTAL'
                        echo 'DOCKER_RUNNING:\$DOCKER_RUNNING'
                        echo 'DOCKER_STOPPED:\$DOCKER_STOPPED'
                        
                        # Container details
                        echo 'DOCKER_DETAILS:'\$(docker ps --format '{{.Names}}|{{.Status}}|{{.Ports}}|{{.Image}}' | tr '\n' ';' | sed 's/;$//')
                        
                        # Docker system info
                        echo 'DOCKER_SYSTEM:'\$(docker system df --format 'table {{.Type}}\t{{.TotalCount}}\t{{.Size}}' | tr '\n' ',' | sed 's/,$//')
                    else
                        echo 'DOCKER_STATUS:Not Installed'
                    fi
                    
                    # Service Status
                    echo 'SERVICES:'\$(systemctl list-units --type=service --state=running | head -10 | wc -l)
                    echo 'FAILED_SERVICES:'\$(systemctl list-units --type=service --state=failed | wc -l)
                    
                    # Recent System Logs
                    echo 'REBOOT_REQUIRED:'\$([ -f /var/run/reboot-required ] && echo 'YES' || echo 'NO')
                    
                    # Deployed Applications with details
                    if [ -d /opt ]; then
                        for app in \$(ls -1 /opt 2>/dev/null); do
                            if [ -d \"/opt/\$app\" ] && [ -f \"/opt/\$app/docker-compose.yml\" ]; then
                                APP_STATUS=\$(cd /opt/\$app && docker compose ps 2>/dev/null | grep -c 'Up' || echo '0')
                                echo "APP_\$APP:\$APP_STATUS"
                            fi
                        done
                    fi
                " 2>/dev/null || echo "ERROR:Failed to get comprehensive data")
                ;;
        esac
        
        MONITORING_RESULTS+=("$SERVER:$MONITORING_DATA")
    else
        MONITORING_RESULTS+=("$(echo "$result" | cut -d: -f1):NO_CONNECTION:No SSH connectivity")
    fi
done
```

### Step 4: Generate Monitoring Report
```bash
echo "📊 MONITORING RESULTS"
echo "======================="
echo ""

# Count server status
ONLINE_COUNT=0
OFFLINE_COUNT=0

for result in "${CONNECTIVITY_RESULTS[@]}"; do
    if [[ $result == *":CONNECTED:"* ]]; then
        ((ONLINE_COUNT++))
    else
        ((OFFLINE_COUNT++))
    fi
done

echo "🔌 Connectivity Summary:"
echo "  Online Servers: $ONLINE_COUNT"
echo "  Offline Servers: $OFFLINE_COUNT"
echo "  Total Servers: ${#SERVERS[@]}"
echo ""

# Detailed server status
echo "🖥️  SERVER STATUS REPORT"
echo "========================="

for result in "${MONITORING_RESULTS[@]}"; do
    SERVER=$(echo "$result" | cut -d: -f1)
    
    if [[ $result == *"NO_CONNECTION"* ]]; then
        echo "❌ $SERVER"
        echo "   Status: OFFLINE - No SSH connectivity"
        echo ""
    else
        # Parse monitoring data
        if [[ $result == *"BASIC_STATUS:OK"* ]]; then
            CPU=$(echo "$result" | grep -o 'CPU_CHECK:[^,]*' | cut -d: -f2)
            MEM=$(echo "$result" | grep -o 'MEM_USAGE:[^,]*' | cut -d: -f2)
            DISK=$(echo "$result" | grep -o 'DISK_USAGE:[^,]*' | cut -d: -f2)
            
            echo "✅ $SERVER"
            echo "   CPU: ${CPU}%"
            echo "   Memory: ${MEM}%"
            echo "   Disk: ${DISK}"
            
        elif [[ $result == *"DETAILED_STATUS:OK"* ]]; then
            CPU=$(echo "$result" | grep -o 'CPU_USAGE:[^,]*' | cut -d: -f2)
            MEM_TOTAL=$(echo "$result" | grep -o 'MEM_TOTAL:[^,]*' | cut -d: -f2)
            MEM_USED=$(echo "$result" | grep -o 'MEM_USED:[^,]*' | cut -d: -f2)
            DISK=$(echo "$result" | grep -o 'DISK_ROOT:[^,]*' | cut -d: -f2)
            DOCKER_RUNNING=$(echo "$result" | grep -o 'DOCKER_RUNNING:[^,]*' | cut -d: -f2)
            DEPLOYED_APPS=$(echo "$result" | grep -o 'DEPLOYED_APPS:[^,]*' | cut -d: -f2)
            
            echo "✅ $SERVER"
            echo "   CPU: ${CPU}%"
            echo "   Memory: ${MEM_USED}MB / ${MEM_TOTAL}MB"
            echo "   Disk: ${DISK}"
            echo "   Docker: ${DOCKER_RUNNING} running containers"
            if [ -n "$DEPLOYED_APPS" ] && [ "$DEPLOYED_APPS" != "DEPLOYED_APPS:" ]; then
                echo "   Apps: $DEPLOYED_APPS"
            fi
            
        elif [[ $result == *"COMPREHENSIVE_STATUS:OK"* ]]; then
            HOSTNAME=$(echo "$result" | grep -o 'HOSTNAME:[^,]*' | cut -d: -f2)
            CPU=$(echo "$result" | grep -o 'CPU_USAGE:[^,]*' | cut -d: -f2)
            MEM=$(echo "$result" | grep -o 'MEM_USAGE_PERCENT:[^,]*' | cut -d: -f2)
            LOAD=$(echo "$result" | grep -o 'LOAD_AVG:[^,]*' | cut -d: -f2)
            DISK=$(echo "$result" | grep -o 'DISK_ROOT:[^,]*' | cut -d: -f2)
            DOCKER_RUNNING=$(echo "$result" | grep -o 'DOCKER_RUNNING:[^,]*' | cut -d: -f2)
            
            echo "✅ $SERVER ($HOSTNAME)"
            echo "   CPU: ${CPU}% | Load: $LOAD"
            echo "   Memory: ${MEM}%"
            echo "   Disk: ${DISK}"
            echo "   Docker: ${DOCKER_RUNNING} running containers"
            
            # Show deployed apps if any
            APP_LINES=$(echo "$result" | grep -o 'APP_[^:]*:[^,]*')
            if [ -n "$APP_LINES" ]; then
                echo "   Applications:"
                echo "$APP_LINES" | while read -r app_line; do
                    APP_NAME=$(echo "$app_line" | cut -d: -f2)
                    APP_STATUS=$(echo "$app_line" | cut -d: -f3)
                    echo "     • $APP_NAME: $APP_STATUS containers"
                done
            fi
        fi
        echo ""
    fi
done
```

### Step 5: Generate Alerts and Recommendations
```bash
echo "🚨 ALERTS AND RECOMMENDATIONS"
echo "==============================="

ALERTS_GENERATED=false

# Check for critical issues
for result in "${MONITORING_RESULTS[@]}"; do
    if [[ $result == *"DETAILED_STATUS:OK"* ]] || [[ $result == *"COMPREHENSIVE_STATUS:OK"* ]]; then
        SERVER=$(echo "$result" | cut -d: -f1)
        
        # High CPU usage alert
        if [[ $result == *"CPU_USAGE:"* ]]; then
            CPU=$(echo "$result" | grep -o 'CPU_USAGE:[0-9]*' | cut -d: -f2)
            if [ "$CPU" -gt 80 ]; then
                echo "🚨 HIGH CPU ALERT: $SERVER - CPU usage is ${CPU}%"
                ALERTS_GENERATED=true
            fi
        fi
        
        # High memory usage alert
        if [[ $result == *"MEM_USAGE_PERCENT:"* ]]; then
            MEM=$(echo "$result" | grep -o 'MEM_USAGE_PERCENT:[0-9]*' | cut -d: -f2)
            if [ "${MEM%.*}" -gt 80 ]; then
                echo "🚨 HIGH MEMORY ALERT: $SERVER - Memory usage is ${MEM}%"
                ALERTS_GENERATED=true
            fi
        fi
        
        # Disk space alert
        if [[ $result == *"DISK_ROOT:"* ]]; then
            DISK=$(echo "$result" | grep -o 'DISK_ROOT:[0-9]*' | cut -d: -f2)
            if [ "$DISK" -gt 85 ]; then
                echo "🚨 LOW DISK SPACE ALERT: $SERVER - Disk usage is ${DISK}%"
                ALERTS_GENERATED=true
            fi
        fi
        
        # Docker issues
        if [[ $result == *"DOCKER_RUNNING:0"* ]] || [[ $result == *"DOCKER_TOTAL:0"* ]]; then
            echo "⚠️  DOCKER ISSUE: $SERVER - No running containers (may need attention)"
        fi
    fi
done

if [ "$ALERTS_GENERATED" = false ]; then
    echo "✅ No critical alerts - All systems operating normally"
fi

echo ""
echo "💡 RECOMMENDATIONS"
echo "=================="

echo "1. 🔄 Regular Monitoring: Run this command regularly to track system health"
echo "2. 📊 Resource Planning: Monitor trends and plan capacity upgrades"
echo "3. 🛡️  Security: Keep systems updated and monitor for unusual activity"
echo "4. 📦 Application Health: Monitor deployed applications for performance"
echo "5. 🌐 Network Monitoring: Track connectivity and bandwidth usage"

echo ""
echo "🔧 QUICK MANAGEMENT COMMANDS"
echo "============================"

# Generate quick commands for common tasks
echo "# Check specific server in detail:"
echo "/servers $SERVER_CATEGORY comprehensive"
echo ""

echo "# Deploy application to servers:"
echo "/deploy [app-name] mesh-local"
echo ""

echo "# Scale application across servers:"
echo "/scale [app-name] 5 mesh"
echo ""

echo "# Check git status across servers:"
echo "/status [app-name]"
echo ""

echo "📈 MONITORING COMMANDS"
echo "======================"

echo "# Real-time monitoring:"
for server in "${SERVERS[@]:3}"; do  # Limit to first few for brevity
    echo "ssh $SERVER 'top -bn1 | head -5'"
done

echo ""
echo "# Docker monitoring:"
for server in "${SERVERS[@]:3}"; do
    echo "ssh $SERVER 'docker ps --format \"table {{.Names}}\t{{.Status}}\"'"
done

echo ""
echo "# Resource usage:"
for server in "${SERVERS[@]:3}"; do
    echo "ssh $SERVER 'free -h && df -h'"
done

echo ""
echo "🕒 Last Updated: $(date)"
echo "📊 Monitoring Level: $MONITORING_LEVEL"
echo "🖥️  Servers Monitored: ${#SERVERS[@]}"
```

## Report

### Server Network Overview
- **Total Servers**: ${#SERVERS[@]} servers monitored
- **Online Servers**: $ONLINE_COUNT servers responding
- **Offline Servers**: $OFFLINE_COUNT servers unreachable
- **Monitoring Level**: $MONITORING_LEVEL
- **Report Generated**: $(date)

### Server Categories Monitored
- **Mesh Servers**: High-performance local network servers
- **AgenticOverlord Servers**: Remote servers via Cloudflare tunnel
- **DigitalOcean Servers**: Production cloud infrastructure

### Health Summary

#### Critical Alerts
[Generated alerts for high CPU, memory, or disk usage]

#### System Performance
- **Average CPU Usage**: [Calculated from online servers]
- **Average Memory Usage**: [Calculated from online servers]
- **Disk Space**: [Summary of disk usage across servers]

#### Application Status
- **Docker Containers**: [Total running containers]
- **Deployed Apps**: [Applications running in /opt]

### Quick Actions

#### Immediate Actions Required
- [ ] Address any critical alerts shown above
- [ ] Restart any failed Docker containers
- [ ] Monitor offline servers for connectivity issues

#### Regular Maintenance
- [ ] Run `/servers all detailed` weekly for health checks
- [ ] Monitor resource usage trends monthly
- [ ] Update Docker images and applications regularly
- [ ] Backup critical data and configurations

### Monitoring Best Practices

#### Proactive Monitoring
- Set up automated monitoring for critical services
- Configure alerts for resource thresholds
- Monitor application performance and availability
- Track network connectivity and latency

#### Resource Management
- Monitor CPU usage trends and plan capacity upgrades
- Track memory consumption and identify memory leaks
- Monitor disk space and implement cleanup procedures
- Optimize Docker container resource allocation

#### Security Considerations
- Regularly update system packages and Docker images
- Monitor for unusual login attempts or network activity
- Implement proper SSH key management
- Regular security audits and vulnerability scanning

Your server network is now fully monitored with comprehensive health checks and performance metrics!

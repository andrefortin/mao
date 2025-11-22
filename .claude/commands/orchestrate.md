---
description: Orchestrate distributed agents across server network using LAVINMQ message queues
argument-hint: [action] [app-name] [servers] [parameters]
model: claude-sonnet-4-5-20250929
---

# Distributed Agent Orchestration

## Purpose

Coordinate and manage distributed agents across your server network using LAVINMQ message queues for scalable, fault-tolerant orchestration and task distribution.

## Variables

ACTION: \$1 (deploy, scale, command, status, stop)
APP_NAME: \$2 (application to orchestrate)
SERVERS: \$3 (target servers or category)
PARAMETERS: \$4 (additional parameters)
LAVINMQ_HOST: rabbit.lmq.cloudamqp.com
LAVINMQ_USER: hkmovykq
LAVINMQ_PASSWORD: 18FVePEZ4QVq_YSv6zUkEXNZQwxfgxBj

## Workflow

### Step 1: Validate Input
if [ -z "\$ACTION" ]; then
    echo "Error: Action is required"
    echo "Usage: /orchestrate [action] [app-name] [servers] [parameters]"
    echo "Actions: deploy, scale, command, status, stop"
    exit 1
fi

echo "🤖 Distributed Agent Orchestration"
echo "================================="
echo "Action: \$ACTION"
echo "App: \${APP_NAME:-All Apps}"
echo "Servers: \${SERVERS:-All Servers}"
echo "Timestamp: \$(date)"
echo ""

### Step 2: Execute Orchestration Action
case "\$ACTION" in
    "deploy")
        if [ -z "\$APP_NAME" ]; then
            echo "Error: App name is required for deploy action"
            exit 1
        fi
        
        echo "🚀 Deploying distributed agents for: \$APP_NAME"
        
        # Create worker queue
        WORKER_QUEUE="workers.\$APP_NAME.orchestrated"
        
        echo "📦 Creating worker queue: \$WORKER_QUEUE"
        python3 -c "
import subprocess
import sys
try:
    result = subprocess.run(['rabbitmqadmin', '-q', '-p', '\$LAVINMQ_VHOST', '-u', '\$LAVINMQ_USER', '-p', '\$LAVINMQ_PASSWORD', '-H', '\$LAVINMQ_HOST', 'declare', 'queue', '\$WORKER_QUEUE', 'durable', 'true'], 
                          capture_output=True, text=True, check=True)
    print('✅ Worker queue created')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
        ;;
        
    "status")
        echo "📊 Checking distributed agent status..."
        
        python3 -c "
import subprocess
import sys
try:
    result = subprocess.run(['rabbitmqadmin', '-q', '-p', '\$LAVINMQ_VHOST', '-u', '\$LAVINMQ_USER', '-p', '\$LAVINMQ_PASSWORD', '-H', '\$LAVINMQ_HOST', 'list', 'queues', 'name', 'messages'], 
                          capture_output=True, text=True, check=True)
    
    print('📊 Distributed Agent Status')
    print('=' * 30)
    print(result.stdout)
    
    # Count worker queues
    worker_count = result.stdout.count('workers.')
    print(f'👥 Active Worker Queues: {worker_count}')
    
except Exception as e:
    print(f'❌ Error checking status: {e}')
    sys.exit(1)
"
        ;;
        
    "command")
        if [ -z "\$APP_NAME" ] || [ -z "\$PARAMETERS" ]; then
            echo "Error: App name and parameters are required for command action"
            exit 1
        fi
        
        echo "⚡ Sending command: \$PARAMETERS to \$APP_NAME"
        
        python3 -c "
import subprocess
import json
import uuid
import sys

try:
    command_id = str(uuid.uuid4())
    command_msg = {
        'command_id': command_id,
        'command_type': 'custom',
        'app_name': '\$APP_NAME',
        'command': '\$PARAMETERS',
        'timestamp': '2025-01-01T00:00:00Z'
    }
    
    # Send command via rabbitmqadmin
    cmd = ['rabbitmqadmin', '-q', '-p', '\$LAVINMQ_VHOST', '-u', '\$LAVINMQ_USER', '-p', '\$LAVINMQ_PASSWORD', '-H', '\$LAVINMQ_HOST']
    cmd.extend(['publish', 'exchange=amq.default', 'routing_key=commands.\$APP_NAME'])
    cmd.extend(['properties={\"message_id\": \"' + command_id + '\"}'])
    cmd.extend(['payload=' + json.dumps(command_msg)])
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print('✅ Command sent successfully')
    print(f'Command ID: {command_id}')
    
except Exception as e:
    print(f'❌ Error sending command: {e}')
    sys.exit(1)
"
        ;;
        
    *)
        echo "Error: Unknown action '\$ACTION'"
        echo "Available actions: deploy, scale, command, status"
        exit 1
        ;;
esac

echo ""
echo "📊 Monitoring Commands"
echo "===================="
echo "# Monitor queue status"
echo "/queues list"
echo ""
echo "# Monitor specific queue"
echo "/queues monitor workers.\${APP_NAME:-app-name}.orchestrated"
echo ""
echo "# LAVINMQ Management"
echo "# Connect to LAVINMQ web console"
echo "# URL: https://rabbit.lmq.cloudamqp.com"
echo "# User: \$LAVINMQ_USER"

---
description: Manage LAVINMQ message queues for distributed agent orchestration and server communication
argument-hint: [action] [queue-name] [parameters]
model: claude-sonnet-4-5-20250929
---

# LAVINMQ Queue Management

## Purpose

Manage LAVINMQ message queues for distributed agent orchestration, remote server communication, and worker agent coordination across your server network.

## Variables

ACTION: \$1 (create, delete, list, monitor, purge)
QUEUE_NAME: \$2 (queue name or pattern)
PARAMETERS: \$3 (additional parameters for the action)
LAVINMQ_HOST: rabbit.lmq.cloudamqp.com
LAVINMQ_USER: hkmovykq
LAVINMQ_PASSWORD: 18FVePEZ4QVq_YSv6zUkEXNZQwxfgxBj
LAVINMQ_VHOST: hkmovykq
LAVINMQ_PORT: 5671 (SSL)

## LAVINMQ Queue Naming Conventions

### Queue Categories:
- workers.{app-name}.{server-category} (e.g., workers.sec-detective.mesh)
- health.{server-name} (e.g., health.mesh01)
- commands.{server-name} (e.g., commands.mesh01)
- responses.{task-id} (e.g., responses.task-12345)
- events.{event-type} (e.g., events.agent-status)
- dlq.{queue-name}.errors (dead letter queues)

## Workflow

### Step 1: Validate Action
if [ -z "\$ACTION" ]; then
    echo "Error: Action is required"
    echo "Usage: /queues [action] [queue-name] [parameters]"
    exit 1
fi

echo "LAVINMQ Queue Management"
echo "Action: \$ACTION"
echo "Queue: \${QUEUE_NAME:-All Queues}"
echo "Host: \$LAVINMQ_HOST"
echo "Timestamp: \$(date)"
echo ""

### Step 2: Execute Operation
case "\$ACTION" in
    "create")
        if [ -z "\$QUEUE_NAME" ]; then
            echo "Error: Queue name is required for create action"
            exit 1
        fi
        
        echo "Creating queue: \$QUEUE_NAME"
        
        # Create queue using rabbitmqadmin
        rabbitmqadmin -q -p "\$LAVINMQ_VHOST" -u "\$LAVINMQ_USER" -p "\$LAVINMQ_PASSWORD" \
            -H "\$LAVINMQ_HOST" \
            declare queue "\$QUEUE_NAME" durable true \
            arguments '{"x-message-ttl":3600000,"x-dead-letter-exchange":"dlq","x-dead-letter-routing-key":"\$QUEUE_NAME.errors"}'
        
        if [ \$? -eq 0 ]; then
            echo "✅ Queue created successfully: \$QUEUE_NAME"
        else
            echo "❌ Failed to create queue: \$QUEUE_NAME"
        fi
        ;;
        
    "list")
        echo "Listing all queues:"
        
        rabbitmqadmin -q -p "\$LAVINMQ_VHOST" -u "\$LAVINMQ_USER" -p "\$LAVINMQ_PASSWORD" \
            -H "\$LAVINMQ_HOST" list queues name messages consumers
        ;;
        
    "monitor")
        echo "Monitoring queue health..."
        
        if [ -n "\$QUEUE_NAME" ]; then
            # Monitor specific queue
            rabbitmqadmin -q -p "\$LAVINMQ_VHOST" -u "\$LAVINMQ_USER" -p "\$LAVINMQ_PASSWORD" \
                -H "\$LAVINMQ_HOST" show queue "\$QUEUE_NAME"
        else
            # Monitor all queues
            echo "Monitoring all queues (Ctrl+C to stop)..."
            while true; do
                clear
                echo "LAVINMQ Queue Monitor - \$(date)"
                echo "================================"
                echo ""
                rabbitmqadmin -q -p "\$LAVINMQ_VHOST" -u "\$LAVINMQ_USER" -p "\$LAVINMQ_PASSWORD" \
                    -H "\$LAVINMQ_HOST" list queues name messages consumers | \
                    awk 'NR>1 {printf "%-30s %10s %10s\n", $1, $2, $3}'
                echo ""
                echo "Last updated: \$(date)"
                sleep 5
            done
        fi
        ;;
        
    "purge")
        if [ -z "\$QUEUE_NAME" ]; then
            echo "Error: Queue name is required for purge action"
            exit 1
        fi
        
        echo "Purging queue: \$QUEUE_NAME"
        rabbitmqadmin -q -p "\$LAVINMQ_VHOST" -u "\$LAVINMQ_USER" -p "\$LAVINMQ_PASSWORD" \
            -H "\$LAVINMQ_HOST" purge queue "\$QUEUE_NAME"
        
        if [ \$? -eq 0 ]; then
            echo "✅ Queue purged successfully"
        else
            echo "❌ Failed to purge queue"
        fi
        ;;
        
    "delete")
        if [ -z "\$QUEUE_NAME" ]; then
            echo "Error: Queue name is required for delete action"
            exit 1
        fi
        
        echo "Deleting queue: \$QUEUE_NAME"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ \$REPLY =~ ^[Yy]$ ]]; then
            rabbitmqadmin -q -p "\$LAVINMQ_VHOST" -u "\$LAVINMQ_USER" -p "\$LAVINMQ_PASSWORD" \
                -H "\$LAVINMQ_HOST" delete queue "\$QUEUE_NAME"
            
            if [ \$? -eq 0 ]; then
                echo "✅ Queue deleted successfully"
            else
                echo "❌ Failed to delete queue"
            fi
        else
            echo "Delete cancelled"
        fi
        ;;
        
    *)
        echo "Error: Unknown action '\$ACTION'"
        echo "Available actions: create, delete, list, monitor, purge"
        exit 1
        ;;
esac

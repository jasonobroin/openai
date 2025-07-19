#!/bin/bash

APP_PATH_DISCORD=/home/wastedye/python/openai/discordbot.py
APP_PATH_SLACK=/home/wastedye/python/openai/slackbot.py
APP_NAME_DISCORD=discordbot
APP_NAME_SLACK=slackbot
LOG_FILE="/tmp/aictrl.log"
MONITOR_PID_FILE="/tmp/aictrl_monitor.pid"

# Log function to timestamp and log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Start a specific application
start_app() {
    local app_path=$1
    local app_name=$2
    
    log "Starting $app_name..."
    "$app_path" &
    local pid=$!
    
    # Wait a moment to ensure process started properly
    sleep 2
    
    if ps -p $pid > /dev/null; then
        log "$app_name started successfully with PID: $pid"
        return 0
    else
        log "ERROR: Failed to start $app_name"
        return 1
    fi
}

# Start both applications
start() {
    log "=== Starting all applications ==="
    start_app "$APP_PATH_DISCORD" "$APP_NAME_DISCORD"
    start_app "$APP_PATH_SLACK" "$APP_NAME_SLACK"
    
    # Start the monitoring service in the background
    start_monitoring
}

# Stop the application
stop() {
    # First stop the monitoring service
    stop_monitoring
    
    log "=== Stopping all applications ==="
    
    log "Stopping $APP_NAME_DISCORD..."
    pkill -f "$APP_PATH_DISCORD"
    
    log "Stopping $APP_NAME_SLACK..."
    pkill -f "$APP_PATH_SLACK"
    
    # Give processes time to shut down gracefully
    sleep 2
    
    # Force kill if still running
    if pgrep -f "$APP_PATH_DISCORD" > /dev/null; then
        log "Force killing $APP_NAME_DISCORD..."
        pkill -9 -f "$APP_PATH_DISCORD"
    fi
    
    if pgrep -f "$APP_PATH_SLACK" > /dev/null; then
        log "Force killing $APP_NAME_SLACK..."
        pkill -9 -f "$APP_PATH_SLACK"
    fi
}

# Check if a specific application is running
check_app() {
    local app_path=$1
    local app_name=$2
    
    if pgrep -f "$app_path" > /dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Check if all applications are running
status() {
    local discord_status="not running"
    local slack_status="not running"
    local monitor_status="not running"
    
    if check_app "$APP_PATH_DISCORD" "$APP_NAME_DISCORD"; then
        discord_status="running"
    fi
    
    if check_app "$APP_PATH_SLACK" "$APP_NAME_SLACK"; then
        slack_status="running"
    fi
    
    # Check if monitor is running
    if [ -f "$MONITOR_PID_FILE" ]; then
        MONITOR_PID=$(cat "$MONITOR_PID_FILE")
        if ps -p "$MONITOR_PID" > /dev/null; then
            monitor_status="running (PID: $MONITOR_PID)"
        fi
    fi
    
    log "$APP_NAME_DISCORD is $discord_status"
    log "$APP_NAME_SLACK is $slack_status"
    log "Monitoring service is $monitor_status"
    
    echo "$APP_NAME_DISCORD is $discord_status"
    echo "$APP_NAME_SLACK is $slack_status"
    echo "Monitoring service is $monitor_status"
    
    if [[ "$discord_status" == "running" ]] && [[ "$slack_status" == "running" ]]; then
        return 0
    else
        return 1
    fi
}

# Monitor function to be run in the background
monitor_function() {
    log "Starting monitoring service with PID $$..."
    echo $$ > "$MONITOR_PID_FILE"
    
    # Ensure all apps are running initially
    if ! check_app "$APP_PATH_DISCORD" "$APP_NAME_DISCORD" || ! check_app "$APP_PATH_SLACK" "$APP_NAME_SLACK"; then
        log "Some applications are not running. Starting all..."
        start_app "$APP_PATH_DISCORD" "$APP_NAME_DISCORD"
        start_app "$APP_PATH_SLACK" "$APP_NAME_SLACK"
    fi
    
    while true; do
        # Check Discord bot
        if ! check_app "$APP_PATH_DISCORD" "$APP_NAME_DISCORD"; then
            log "ALERT: $APP_NAME_DISCORD died unexpectedly. Restarting..."
            start_app "$APP_PATH_DISCORD" "$APP_NAME_DISCORD"
        fi
        
        # Check Slack bot
        if ! check_app "$APP_PATH_SLACK" "$APP_NAME_SLACK"; then
            log "ALERT: $APP_NAME_SLACK died unexpectedly. Restarting..."
            start_app "$APP_PATH_SLACK" "$APP_NAME_SLACK"
        fi
        
        # Wait before checking again
        sleep 30
    done
}

# Start the monitoring service in the background
start_monitoring() {
    # Check if monitoring is already running
    if [ -f "$MONITOR_PID_FILE" ]; then
        MONITOR_PID=$(cat "$MONITOR_PID_FILE")
        if ps -p "$MONITOR_PID" > /dev/null; then
            log "Monitoring service is already running with PID: $MONITOR_PID"
            return 0
        else
            log "Stale monitoring PID file found. Removing..."
            rm -f "$MONITOR_PID_FILE"
        fi
    fi
    
    log "Starting monitoring service in the background..."
    # Start the monitor function in the background
    nohup bash -c "$(declare -f log check_app start_app monitor_function); monitor_function" > /dev/null 2>&1 &
    
    # Wait a moment to ensure monitoring started properly
    sleep 2
    
    if [ -f "$MONITOR_PID_FILE" ]; then
        MONITOR_PID=$(cat "$MONITOR_PID_FILE")
        if ps -p "$MONITOR_PID" > /dev/null; then
            log "Monitoring service started successfully with PID: $MONITOR_PID"
            return 0
        fi
    fi
    
    log "ERROR: Failed to start monitoring service"
    return 1
}

# Stop the monitoring service
stop_monitoring() {
    if [ -f "$MONITOR_PID_FILE" ]; then
        MONITOR_PID=$(cat "$MONITOR_PID_FILE")
        if ps -p "$MONITOR_PID" > /dev/null; then
            log "Stopping monitoring service (PID: $MONITOR_PID)..."
            kill "$MONITOR_PID"
            rm -f "$MONITOR_PID_FILE"
            return 0
        else
            log "Stale monitoring PID file found. Removing..."
            rm -f "$MONITOR_PID_FILE"
        fi
    fi
    
    log "No monitoring service found to stop."
    return 1
}

# Parse command line arguments
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
    status)
        status
        ;;
    monitor_only)  # Hidden command for debugging
        monitor_function
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
#!/bin/bash

APP_PATH_DISCORD=/home/wastedye/python/openai/discordbot.py
APP_PATH_SLACK=/home/wastedye/python/openai/slackbot.py
APP_NAME_DISCORD=discordbot
APP_NAME_SLACK=slackbot
LOG_FILE="/tmp/aictrl.log"
MONITOR_PID_FILE="/tmp/aictrl_monitor.pid"
DEBUG_FILE="/tmp/aictrl_debug.log"  # Debug file for troubleshooting

# Log function to timestamp and log messages
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message"
    echo "$message" >> "$LOG_FILE"
}

# Debug log function - use for troubleshooting
debug_log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] DEBUG: $1"
    echo "$message" >> "$DEBUG_FILE"
}

# Initialize log files
touch "$LOG_FILE" "$DEBUG_FILE"
chmod 666 "$LOG_FILE" "$DEBUG_FILE"
log "=== Script started at $(date) ==="
debug_log "=== Debug log initialized ==="

# Start a specific application
start_app() {
    local app_path=$1
    local app_name=$2

    log "Starting $app_name..."
    debug_log "Attempting to start $app_name from path: $app_path"

    "$app_path" &
    local pid=$!

    # Wait a moment to ensure process started properly
    sleep 2

    if ps -p $pid > /dev/null; then
        log "$app_name started successfully with PID: $pid"
        debug_log "$app_name started with PID: $pid"
        return 0
    else
        log "ERROR: Failed to start $app_name"
        debug_log "Failed to start $app_name. PID $pid not found after 2 seconds"
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

    echo "Status as of $(date):"
    echo "- $APP_NAME_DISCORD is $discord_status"
    echo "- $APP_NAME_SLACK is $slack_status"
    echo "- Monitoring service is $monitor_status"
    echo "- Log file: $LOG_FILE"
    echo "- Debug file: $DEBUG_FILE"

    if [[ "$discord_status" == "running" ]] && [[ "$slack_status" == "running" ]]; then
        return 0
    else
        return 1
    fi
}

# The actual monitoring loop function
monitor_loop() {
    debug_log "Starting monitor_loop function with PID: $$"
    echo $$ > "$MONITOR_PID_FILE"
    chmod 666 "$MONITOR_PID_FILE"

    log "Monitoring service started with PID: $$"

    # Ensure all apps are running initially
    if ! check_app "$APP_PATH_DISCORD" "$APP_NAME_DISCORD"; then
        log "Starting $APP_NAME_DISCORD since it's not running..."
        start_app "$APP_PATH_DISCORD" "$APP_NAME_DISCORD"
    fi

    if ! check_app "$APP_PATH_SLACK" "$APP_NAME_SLACK"; then
        log "Starting $APP_NAME_SLACK since it's not running..."
        start_app "$APP_PATH_SLACK" "$APP_NAME_SLACK"
    fi

    log "Monitor is actively checking apps every 30 seconds"

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

        # Log a heartbeat every 5 minutes (300 seconds)
        if (( SECONDS % 300 < 30 )); then
            log "Monitor heartbeat - still running"
        fi

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
    debug_log "Attempting to start monitor service in background"

    # Use a much simpler approach - run this script again with a direct command
    # This avoids issues with function passing to background processes
    nohup "$0" run_monitor > /dev/null 2>&1 &

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
    debug_log "Failed to start monitor. PID file: $(ls -la $MONITOR_PID_FILE 2>/dev/null)"
    return 1
}

# Stop the monitoring service
stop_monitoring() {
    if [ -f "$MONITOR_PID_FILE" ]; then
        MONITOR_PID=$(cat "$MONITOR_PID_FILE")
        if ps -p "$MONITOR_PID" > /dev/null; then
            log "Stopping monitoring service (PID: $MONITOR_PID)..."
            kill "$MONITOR_PID"
            sleep 1
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
    run_monitor)
        # This is a special command used internally to run the monitor
        # It's called by the start_monitoring function
        monitor_loop
        ;;
    debug)
        echo "Debug info:"
        echo "- Script path: $0"
        echo "- Log file: $LOG_FILE"
        echo "- Monitor PID file: $MONITOR_PID_FILE"
        echo "- Debug log: $DEBUG_FILE"

        echo "Log file contents:"
        cat "$LOG_FILE"

        echo "Debug file contents:"
        cat "$DEBUG_FILE"

        echo "Monitor PID file:"
        if [ -f "$MONITOR_PID_FILE" ]; then
            cat "$MONITOR_PID_FILE"
        else
            echo "PID file does not exist"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|debug}"
        exit 1
        ;;
esac

exit 0
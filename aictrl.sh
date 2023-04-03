#!/bin/bash

APP_PATH_DISCORD=/home/wastedye/python/openai/discordbot.py
APP_PATH_SLACK=/home/wastedye/python/openai/slackbot.py
APP_NAME_DISCORD=discordbot
APP_NAME_SLACK=slackbot

# Start the application
start() {
    echo "Starting $APP_NAME_DISCORD ..."
#    /home/wastedye/virtualenv/python/discord-bot/3.10/bin/python3.10_bin "$APP_PATH_DISCORD" &
    "$APP_PATH_DISCORD" &
    echo "Starting $APP_NAME_SLACK ..."
#    /home/wastedye/virtualenv/python/discord-bot/3.10/bin/python3.10_bin "$APP_PATH_SLACK" &
    "$APP_PATH_SLACK" &
}

# Stop the application
stop() {
    echo "Stopping $APP_NAME_DISCORD ..."
    pkill -f "$APP_PATH_DISCORD"
    echo "Stopping $APP_NAME_SLACK ..."
    pkill -f "$APP_PATH_SLACK"
}

# Check if the application is running
status() {
    pgrep -f "$APP_PATH_DISCORD" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "$APP_NAME_DISCORD is running"
    else
        echo "$APP_NAME_DISCORD is not running"
    fi

    pgrep -f "$APP_PATH_SLACK" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "$APP_NAME_SLACK is running"
    else
        echo "$APP_NAME_SLACK is not running"
    fi
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
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0

#!/usr/bin/env python3

"""Slack frontend to chatGPT interface

Manages conversations, organized by Slack user and channel

TODO

* Pass some sensible default args in - how should we structure this? Is there an args module
  which is included by either this python module if called as __main__ and chatai.py if called
  as __main__ -- that feels like the right sort of approach
* Add /commands to allow changing of parameters (such as temperature)
  and regenerating responses. Perhaps look at automatically threading conversations should there is
  natural interface for multiple conversations
* Define a few default system roles that can be easily selected
* Allow interface to different models, such as images

"""


import argparse
import chatai
from datetime import datetime
import json
import logging
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

import pprint as pp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-7s | %(levelname)-8s | %(module)s:%(lineno)-4d | %(message)s",
    datefmt='%a %d %b %Y %I:%M:%S %p %z',
    filename='slack.log',
)
botlog = logging.getLogger('sbot')

# Create a dictionary of conversations
conversations = {}

# Initialize the Slack app with your bot token
app = App(token=os.environ["SLACK_BOT_TOKEN"])

def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description="Interface to chatGPT discord-bot",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-f", "--directory", help="Directory to store chats", default="slack_chats")
    parser.add_argument("-m", "--model", help="Select the model to use", default="gpt-4") # gpt-4

    return parser.parse_args()


def set_system_role(conversation, system_role=None):
    if system_role is None:
        conversation.set_system_role("You are a helpful assistant")
    else:
        conversation.set_system_role(system_role)

def get_system_role(conversation):
    return conversation.get_system_role()


def get_conversation(user_id, channel_id, thread_id, add_final_msg = True):
#    print(f'get_conversation user {user_id} {thread_id}')

    if user_id not in conversations:
        conversations[user_id] = {}
    if channel_id not in conversations[user_id]:
        conversations[user_id][channel_id] = {}
    if thread_id not in conversations[user_id][channel_id]:
        conversations[user_id][channel_id][thread_id] = chatai.Conversation()
        set_system_role(conversations[user_id][channel_id][thread_id])

        # Reload the conversation if we don't have it in memory
        result = slack_web_client.conversations_replies(channel=channel_id, ts=thread_id)
        conversation_history = result["messages"]
        if conversation_history:
            load_conversation(conversations[user_id][channel_id][thread_id], conversation_history, add_final_msg)

    return conversations[user_id][channel_id][thread_id]


def process_chat_turn(conversation, message, model):
    botlog.info(f"user asks: {message}")
    response = chatai.take_turn(conversation, model, message)
    botlog.info(f"assistant responses: {response}")

    # This should be its own helper function. One issue here is that there
    # will be a line break if the split is midline

    # Discord has a 2000 character response limit - Split the response into
    # chunks of 1900 characters or less, and also prevent splitting in the
    # middle of a line; we use 1900 to give plenty of room for any additional
    # message overhead

    response_chunks = []
    chunk = ""
    for line in response.split("\n"):
        if len(chunk) + len(line) + 1 > 1900:
            response_chunks.append(chunk)
            chunk = ""
        chunk += line + "\n"
    response_chunks.append(chunk)

    return response_chunks

def load_conversation(conversation, conversation_history, add_final_msg):
    """
    Load a slack conversation thread into our conversation object
    """

    # We might want to skip the final message depending what circumstances
    # we have reloaded the conversation
    end = None if add_final_msg else -1
    for i, entry in enumerate(conversation_history[:end]):
        if entry['type'] == 'message':
            role = 'assistant' if 'bot_id' in entry else 'user'
            conversation.add_turn(role, entry['text'])
        if i == 0:
            botlog.info(f"Reloaded conversation from slack '{entry['text'][:20]} ... ")


# Define a function to handle incoming messages
@app.event("message")
def handle_message(event, say, client):
    msg = event["text"]
    user = event['user']
    channel = event['channel']

    thread_ts = event.get('thread_ts', event.get('event_ts'))

    # Different response / thread depending on whether this is the first message or not
    if thread_ts != event.get('event_ts'):
        slack_web_client.chat_postEphemeral(channel=channel, thread_ts=thread_ts, text='ChatGPT is thinking...',
                                            user=user)
    else:
        slack_web_client.chat_postEphemeral(channel=channel, text='ChatGPT is thinking... will create new thread',
                                            user=user)

    conversation = get_conversation(user, channel, thread_ts, False)

    botlog.debug(f"user={user} channel={channel} thread_id={thread_ts}: {conversation.num_turns()} entries")
    response_chunks = process_chat_turn(conversation, msg, args.model)

    for chunk in response_chunks:
        client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=chunk)

def handle_new_command(ack, body, respond):

#    print(f"user {body['user_id']} channel {body['channel_id']}")
    user = body['user_id']
    channel = body['channel_id']
    thread_ts = body.get('thread_ts', body.get('event_ts'))
    conversation = get_conversation(user, channel, thread_ts)
    conversation.clear()
    set_system_role(conversation)
    respond("Starting a new conversation")

def handle_report_command(ack, body, respond):
    """Provide a JSON report of the current conversation"""
    # This should be its own helper function. One issue here is that there
    # will be a line break if the split is midline

    user = body['user_id']
    channel = body['channel_id']
    thread_ts = body.get('thread_ts', body.get('event_ts'))
    conversation = get_conversation(user, channel, thread_ts)
    response = conversation.to_message()

    # Convert the dictionary to a JSON string so it displays nicer
    json_str = json.dumps(response, indent=4)

    # Split the response into chunks of 1900 characters or less as discord has
    # a 2000 character response limit, and we want to also provide extra room
    # for any additional response overhead.
    # Note: We don't split on line breaks as the response here is in JSON and
    # may be a single line
    response_chunks = [json_str[i:i + 1900] for i in range(0, len(json_str), 1900)]

    # Send each chunk as a separate message
    for chunk in response_chunks:
        respond(chunk)
    botlog.info("Sent .report response")


def handle_chat_command(ack, body, respond):
    """Report summary information on all chats"""
    for user in conversations:
        for chan in conversations[user]:
            for thread in conversations[user][chan]:
                msg = f"Chat stored User: {user} Chan: {chan} Thread {thread} with {int(conversations[user][chan][thread].num_turns())} entries"
                respond (msg)
    respond("End of chats")

def save_command(user, channel, thread_ts):
    """Store a chat to a file"""
    save_time = datetime.now()
    save_time = save_time.strftime("%Y-%m-%d %H:%M:%S")
    # TODO: Would be nice if we had a one line summary of conversation in the title

    conversation = get_conversation(user, channel, thread_ts)
    filename = chatai.write_chat(args.directory, save_time, conversation)
    msg = f'Chat written to {filename}'
    botlog.info(msg)

# The open_modal shortcut opens a plain old modal
# Shortcuts require the command scope
@app.shortcut("save_thread")
def open_modal(ack, shortcut, client, logger):
    # Acknowledge shortcut request
    ack()

    user = shortcut['user']['id']
    channel = shortcut['channel']['id']
    thread_ts = shortcut['message']['thread_ts']

    try:
        # Call the views.open method using the WebClient passed to listeners
        # Look at a way where we can export the JSON and store file on user's file system rather than backend
        result = client.views_open(
            trigger_id=shortcut["trigger_id"],
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "ChatGPT - Save Thread"},
                "close": {"type": "plain_text", "text": "Close"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "The current conversation thread has been saved to the server's slack_chats directory",
                        },
                    },
                ],
            },
        )
        # logger.info(f"shortcut = {shortcut['message']['thread_ts']}")
        logger.info(f"result = {result}")

    except SlackApiError as e:
        logger.error("Error creating conversation: {}".format(e))

    # TODO: We should do this after confirming the modal conversation box, rather than here
    save_command(user, channel, thread_ts)


# TODO: Most of these commands only make sense in the context of a thread
# but slack doesn't support slack commands in a thread
# One option is to have an ability to list the threads via a slash command and then be able
# to select an operation via a GUI element... don't know how to do that yet
#
# Another option is to do it by recognizing a command in a thread, such as .save
#
# A third option is to pass the thread ID in, but that's rather sad!!
chatgpt_cmds = {
    # 'save': handle_save_command,
    'chats': handle_chat_command,
    # 'report': handle_report_command,
    # 'new': handle_new_command
}

@app.command("/chatgpt")
def handle_chatgpt_command(ack, body, respond):
    ack()

    text = body['text']

    cmd = text.split(' ')[0].lower()

    if cmd in chatgpt_cmds:
        function = chatgpt_cmds[cmd]
        return function(ack, body, respond)
    else:
        botlog.info('Invalid /chatgpt command specified')
        respond(f"Unknown command: Try one of {[cmd for cmd in chatgpt_cmds]}")


def main():
    global args
    args = get_args()

    # Initialize a Web API client
    global slack_web_client
    slack_web_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

    # Start the Socket Mode handler
    global handler
    handler = SocketModeHandler(app, app_token=os.environ["SLACK_APP_TOKEN"])
    handler.start()

if __name__ == "__main__":
    main()



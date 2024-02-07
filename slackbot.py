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


def get_conversation(user_id, channel_id, thread_id):
#    print(f'get_conversation user {user_id} {thread_id}')

    if user_id not in conversations:
        conversations[user_id] = {}
    if channel_id not in conversations[user_id]:
        conversations[user_id][channel_id] = {}
    if thread_id not in conversations[user_id][channel_id]:
        conversations[user_id][channel_id][thread_id] = chatai.Conversation()
        set_system_role(conversations[user_id][channel_id][thread_id])
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

def load_conversation(conversation, conversation_history):
    """
    Load a slack conversation thread into our conversation object
    """

    for entry in conversation_history[:-1]:
        if entry['type'] == 'message':
            role = 'assistant' if 'bot_id' in entry else 'user'
            conversation.add_turn(role, entry['text'])

    if conversation.num_turns() > 1:
        turn = conversation.get_entry(1).content
        botlog.info(f"Reloaded conversation from slack '{turn[:20]} ... ")


# Define a function to handle incoming messages
@app.event("message")
def handle_message(event, say):
    msg = event["text"]
    user = event['user']
    channel = event['channel']

    thread_ts = event.get('thread_ts', event.get('event_ts'))

    conversation = get_conversation(user, channel, thread_ts)
    if conversation.num_turns() == 0:
        # Reload the conversation if we don't have it in memory
        result = slack_web_client.conversations_replies(channel=channel, ts=thread_ts)
        conversation_history = result["messages"]
        load_conversation(conversation, conversation_history)

    botlog.debug(f"user={user} channel={channel} thread_id={thread_ts}: {conversation.num_turns()} entries")
    response_chunks = process_chat_turn(conversation, msg, args.model)

    for chunk in response_chunks:
        say(thread_ts=thread_ts, text=chunk)

    # print(f"rx message {text}")
    # if "hello" in text.lower():
    #     say(f"Hi there, <@{event['user']}>!")

@app.command("/new")
def handle_new_command(ack, body, respond):
    ack()

#    print(f"user {body['user_id']} channel {body['channel_id']}")
    user = body['user_id']
    channel = body['channel_id']
    thread_ts = body.get('thread_ts', body.get('event_ts'))
    conversation = get_conversation(user, channel, thread_ts)
    conversation.clear()
    set_system_role(conversation)
    respond("Starting a new conversation")

@app.command("/report")
def handle_report_command(ack, body, respond):
    """Provide a JSON report of the current conversation"""
    # This should be its own helper function. One issue here is that there
    # will be a line break if the split is midline
    ack()

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


@app.command("/chats")
def handle_chat_command(ack, body, respond):
    """Report summary information on all chats"""
    ack()
    for user in conversations:
        for chan in conversations[user]:
            for thread in conversations[user][chan]:
                msg = f"Chat stored User: {user} Chan: {chan} Thread {thread} with {int(conversations[user][chan][thread].num_turns())} entries"
                respond (msg)
    respond("End of chats")

@app.command("/save")
def handle_save_command(ack, body, respond):
    """Store a chat to a file"""
    save_time = datetime.now()
    save_time = save_time.strftime("%Y-%m-%d %H:%M:%S")

    ack()

    user = body['user_id']
    channel = body['channel_id']
    thread_ts = body.get('thread_ts', body.get('event_ts'))
    conversation = get_conversation(user, channel, thread_ts)
    filename = chatai.write_chat(args.directory, save_time, conversation)
    msg = f'Chat written to {filename}'
    respond(msg)


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



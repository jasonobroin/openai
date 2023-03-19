#!/usr/bin/env python3

"""Discord frontend to chatGPT interface

Manages conversations, organized by Discord channel

TODO

* Pass some sensible default args in - how should we structure this? Is there an args module
  which is included by either this python module if called as __main__ and chatai.py if called
  as __main__ -- that feels like the right sort of approach
* Add . commands to allow changing of parameters (such as temperature)
  and regenerating responses. Perhaps look at automatically threading conversations should there is
  natural interface for multiple conversations
* Define a few default system roles that can be easily selected
* Allow interface to different models, such as images
* Log output into different chats

"""

# Notes
# Installed discord and python-dotenv packages

from datetime import datetime
import argparse
import logging
import json
import os

import discord
from discord.ext import commands
import chatai

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

DESCRIPTION = '''Discord frontend to openAI'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

COMMAND_PREFIX = '.'

client = commands.Bot(command_prefix=COMMAND_PREFIX, description=DESCRIPTION, intents=intents)

token = os.getenv('DISCORD_CHATGPT_BOT_TOKEN')

# Create a dictionary of conversations, keyed off the Discord channel name
conversation = {}

def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description="Interface to chatGPT discord-bot",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-f", "--directory", help="Directory to store chats", default="discord_chats")
    parser.add_argument("-m", "--model", help="Select the model to use", default="gpt-3.5-turbo") # gpt-4

    return parser.parse_args()


def set_system_role(conversation, system_role=None):
    if system_role is None:
        conversation.set_system_role("You are a helpful assistant")
    else:
        conversation.set_system_role(system_role)

def get_system_role(conversation):
    return conversation.get_system_role()

@client.event
async def on_ready():
    print("Logged in as a bot {0.user}".format(client))
    for channel in client.get_all_channels():
        if isinstance(channel, discord.TextChannel):
            conversation[channel.name] = chatai.Conversation()
            print(f'Created a conversation for {channel.name}')
            # channels[channel.id] = {
            #     'name': channel.name,
            #     'topic': channel.topic,
            #     'type': 'text'
            # }
            set_system_role(conversation[channel.name])
        # Not handling VoiceChannel or CategoryChannel
    # Not recommended to do this in on_ready()
#    await client.change_presence(status=discord.Status.idle, activity=discord.Game('Hello there'))

@client.event
async def on_member_join(member):
    print(f'{member} has joined a server')

@client.event
async def on_member_remove(member):
    print(f'{member} has left a server')

def process_chat_turn(channel, message, model):
    print(f"user asks: {message}")
    response = chatai.take_turn(conversation[channel], model, message)
    print(f"assistant responses: {response}")

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


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Ensure we can handle commands; if not a command, treat it as chat input
    # We also ignore slash commands... note we don't ignore the response from
    # something like /giphy - presumably that comes from a different client?
    if message.content[0] == COMMAND_PREFIX or message.content[0] == '/':
        await client.process_commands(message)
    else:
        # Now interface with chatai
        print(f'conversation on channel {message.channel.name}')
        response_chunks = process_chat_turn(message.channel.name, message.content, args.model)

        # Send each chunk as a separate message
        for chunk in response_chunks:
            await message.channel.send(chunk)

@client.command()
async def test(ctx):
    '''Test stuff!!'''
    message = f"Author: {ctx.author}\nServer: {ctx.guild}\nChannel: {ctx.channel}\nMessage: {ctx.message.content}"
    await ctx.send(message)

@client.command(aliases=['new', 'newconv', 'reset'])
async def clear(ctx):
    """Start a new conversation"""
    conversation[ctx.channel.name].clear()
    set_system_role(conversation[ctx.channel.name])
    await ctx.send("Starting a new conversation")

@client.command(aliases=['system_role', 'sysrole', 'system'])
async def role(ctx, *sysrole):
    """Specify what role chatGPT should take and start a new conversation"""
    if len(sysrole) == 0:
        msg = f"Current system role: {get_system_role(conversation[ctx.channel.name])}"
    else:
        role_str = ' '.join(sysrole)
        conversation[ctx.channel.name].clear()
        set_system_role(conversation[ctx.channel.name], role_str)
        msg = f"Starting a new conversation with system role: {role_str}"
    await ctx.send(msg)


@client.command(aliases=['store', 'record'])
async def save(ctx, *sysrole):
    """Store a chat to a file"""
    save_time = datetime.now()
    save_time = save_time.strftime("%Y-%m-%d %H:%M:%S")

    filename = chatai.write_chat(args.directory, save_time, conversation[ctx.channel.name])
    msg = f'Chat written to {filename}'
    await ctx.send(msg)


@client.command()
async def report(ctx):
    """Provide a JSON report of the current conversation"""
    # This should be its own helper function. One issue here is that there
    # will be a line break if the split is midline

    response = conversation[ctx.channel.name].to_message()

    # Convert the dictionary to a JSON string so it displays nicer
    json_str = json.dumps(response, indent=4)

    # TODO: The commented out section below tries to display as discord embed
    # object, but we still have our 2K message limit - not entirely sure how
    # to return an embed object of >2K over multiple messages. It might need
    # to be sent as multiple embed messages, which would likely be fine.

    # i.e. we have our JSON response, we split it at our 1900 limit, probably
    # with the line breaking code, and then return each one as an embed.

    # Create an embedded message with the JSON string as the message content
#    embed = discord.Embed(title='Conversation report', description=f'```json\n{json_str}\n```')

    # Send the message to Discord
#    await ctx.send(embed=embed)

    # Split the response into chunks of 1900 characters or less as discord has
    # a 2000 character response limit, and we want to also provide extra room
    # for any additional response overhead.
    # Note: We don't split on line breaks as the response here is in JSON and
    # may be a single line
    response_chunks = [json_str[i:i + 1900] for i in range(0, len(json_str), 1900)]

    # Send each chunk as a separate message
    for chunk in response_chunks:
        await ctx.send(chunk)
    print("Sent .report response")


def main():
    global args
    args = get_args()

    client.run(token, log_handler=handler)


if __name__ == "__main__":
    main()


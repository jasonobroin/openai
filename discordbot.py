#!/usr/bin/env python3

"""Discord frontend to chatGPT interface

Manages conversations, organized by Discord server, author and channel

TODO

* Pass some sensible default args in - how should we structure this? Is there an args module
  which is included by either this python module if called as __main__ and chatai.py if called
  as __main__ -- that feels like the right sort of approach
* Add . commands to allow changing of parameters (such as temperature)
  and regenerating responses. Perhaps look at automatically threading conversations should there is
  natural interface for multiple conversations
* Define a few default system roles that can be easily selected
* Allow interface to different models, such as images

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-7s | %(levelname)-8s | %(module)s:%(lineno)-4d | %(message)s",
    datefmt='%a %d %b %Y %I:%M:%S %p %z',
    filename='discord.log',
)
botlog = logging.getLogger('dbot')


DESCRIPTION = '''Discord frontend to openAI'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

COMMAND_PREFIX = '.'

client = commands.Bot(command_prefix=COMMAND_PREFIX, description=DESCRIPTION, intents=intents)

token = os.getenv('DISCORD_CHATGPT_BOT_TOKEN')

# Create a dictionary of conversations
conversations = {}

def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description="Interface to chatGPT discord-bot",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-f", "--directory", help="Directory to store chats", default="discord_chats")
    parser.add_argument("-m", "--model", help="Select the model to use", default="gpt-4") # gpt-4

    return parser.parse_args()


def set_system_role(conversation, system_role=None):
    if system_role is None:
        conversation.set_system_role("You are a helpful assistant")
    else:
        conversation.set_system_role(system_role)

def get_system_role(conversation):
    return conversation.get_system_role()

def get_conversation(author_id, server_id, channel_id):
#    print(f'get_conversation on server {server_id} author {author_id} channel {channel_id}')

    if server_id not in conversations:
        conversations[server_id] = {}
    if author_id not in conversations[server_id]:
        conversations[server_id][author_id] = {}
    if channel_id not in conversations[server_id][author_id]:
        conversations[server_id][author_id][channel_id] = chatai.Conversation()
        set_system_role(conversations[server_id][author_id][channel_id])
    return conversations[server_id][author_id][channel_id]

@client.event
async def on_ready():
    botlog.info("Logged in as a bot {0.user}".format(client))
    # Not recommended to do this in on_ready()
#    await client.change_presence(status=discord.Status.idle, activity=discord.Game('Hello there'))

@client.event
async def on_member_join(member):
    botlog.info(f'{member} has joined a server')

@client.event
async def on_member_remove(member):
    botlog.info(f'{member} has left a server')

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


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Don't process responses from bots
    if message.author.bot:
        return

    # Ensure we can handle commands; if not a command, treat it as chat input
    # We also ignore slash commands... note we don't ignore the response from
    # something like /giphy - presumably that comes from a different client?
    if message.content[0] == COMMAND_PREFIX or message.content[0] == '/':
        await client.process_commands(message)
    else:
        # Now interface with chatai
        await message.channel.typing()  # Simulate typing

        conversation = get_conversation(message.author.name, message.guild.name, message.channel.name)
        response_chunks = process_chat_turn(conversation, message.content, args.model)

        # Send each chunk as a separate message
        for chunk in response_chunks:
            await message.channel.send(chunk)

@client.command()
async def test(ctx):
    '''Test stuff!!'''
    message = f"Author: {ctx.author.name}\nServer: {ctx.guild.name}\nChannel: {ctx.channel.name}\nMessage: {ctx.message.content}"
    await ctx.send(message)

@client.command(aliases=['new', 'newconv', 'reset'])
async def clear(ctx):
    """Start a new conversation"""
    conversation = get_conversation(ctx.author.name, ctx.guild.name, ctx.channel.name)
    conversation.clear()
    set_system_role(conversation)
    await ctx.send("Starting a new conversation")

@client.command(aliases=['system_role', 'sysrole', 'system'])
async def role(ctx, *sysrole):
    """Specify what role chatGPT should take and start a new conversation"""
    conversation = get_conversation(ctx.author.name, ctx.guild.name, ctx.channel.name)

    if len(sysrole) == 0:
        msg = f"Current system role: {get_system_role(conversation)}"
    else:
        role_str = ' '.join(sysrole)
        conversation.clear()
        set_system_role(conversation, role_str)
        msg = f"Starting a new conversation with system role: {role_str}"
    await ctx.send(msg)


@client.command(aliases=['store', 'record'])
async def save(ctx, *sysrole):
    """Store a chat to a file"""
    save_time = datetime.now()
    save_time = save_time.strftime("%Y-%m-%d %H:%M:%S")

    conversation = get_conversation(ctx.author.name, ctx.guild.name, ctx.channel.name)
    filename = chatai.write_chat(args.directory, save_time, conversation)
    msg = f'Chat written to {filename}'
    await ctx.send(msg)


@client.command()
async def report(ctx):
    """Provide a JSON report of the current conversation"""
    # This should be its own helper function. One issue here is that there
    # will be a line break if the split is midline

    conversation = get_conversation(ctx.author.name, ctx.guild.name, ctx.channel.name)
    response = conversation.to_message()

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
    botlog.info("Sent .report response")

@client.command()
async def chats(ctx):
    """Report summary information on all chats"""
    for serv in conversations:
        for auth in conversations[serv]:
            for chan in conversations[serv][auth]:
                msg = f"Chat stored for Server: {serv} Author: {auth} Chan: {chan} with {int(conversations[serv][auth][chan].num_turns())} entries"
                await ctx.send(msg)
    await ctx.send("End of chats")

def main():
    global args
    args = get_args()

    client.run(token)


if __name__ == "__main__":
    main()


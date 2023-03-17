#!/usr/bin/env python3

"""Discord frontend to openAI interface

TODO

* Pass some sensible default args in - how should we structure this? Is there an args module
  which is included by either this python module if called as __main__ and chatai.py if called
  as __main__ -- that feels like the right sort of approach
* Add . commands to allow changing of parameters (such as temperature)
  and regenerating responses. Perhaps look at automatically threading conversations should there is
  natural interface for multiple conversations
* Add .commands to set the system role, and possibly define a few default ones that can be specified
* Allow interface to different models, such as images
* Log output into different chats

"""

# Notes
# Installed discord and python-dotenv packages

import discord
from discord.ext import commands
import chatai
import json
import os
import random

import subprocess
import logging

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

description = '''Discord frontend to openAI'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

command_prefix = '.'

client = commands.Bot(command_prefix=command_prefix, description=description, intents=intents)

token = os.getenv('DISCORD_TOKEN')

conversation = chatai.Conversation()

def set_system_role():
    conversation.set_system_role("You are a helpful assistant")

@client.event
async def on_ready():
    print("Logged in as a bot {0.user}".format(client))
    set_system_role()
    # Not recommended to do this in on_ready()
#    await client.change_presence(status=discord.Status.idle, activity=discord.Game('Hello there'))

@client.event
async def on_member_join(member):
    print(f'{member} has joined a server')

@client.event
async def on_member_remove(member):
    print(f'{member} has left a server')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Ensure we can handle commands; if not a command, treat it as chat input
    # We also ignore slash commands... note we don't ignore the response from
    # something like /giphy - presumably that comes from a different client?
    if message.content[0] == command_prefix or message.content[0] == '/':
        await client.process_commands(message)
    else:
        # Now interface with chatai
        print(f"user asks: {message.content}")
        response = chatai.take_turn(conversation, message.content)
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

        # Send each chunk as a separate message
        for chunk in response_chunks:
            await message.channel.send(chunk)

@client.command()
async def test(ctx):
    '''Test stuff!!'''
    message = f"Author: {ctx.author}\nServer: {ctx.guild}\nChannel: {ctx.channel}\nMessage: {ctx.message.content}"
    await ctx.send(message)

@client.command(aliases=['new', 'newconv'])
async def clear(ctx):
    conversation.clear()
    set_system_role()
    await ctx.send("Starting a new conversation")


@client.command()
async def report(ctx):
    # This should be its own helper function. One issue here is that there
    # will be a line break if the split is midline

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
    print("Sent .report response")

client.run(token, log_handler=handler)

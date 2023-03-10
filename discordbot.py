#!/usr/bin/env python3

"""Discord frontend to openAI interface

TODO

* Pass some sensible default args in - how should we structure this? Is there an args module
  which is included by either this python module if called as __main__ and chatai.py if called
  as __main__ -- that feels like the right sort of approach
* Add . commands to allow changing of parameters (such as temperature)
  and regenerating responses. Perhaps look at automatically threading conversations should there is
  natural interface for multiple conversations
* Allow interface to different models, such as images
* Log output into different chats

"""

# Notes
# Installed discord and python-dotenv packages

import discord
from discord.ext import commands
import chatai
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
        # TODO: Move to a model where we can take turns
        print(f"user asks: {message.content}")
        response = chatai.take_turn(conversation, message.content)
        print(f"assistant responses: {response}")
        await message.channel.send(response)

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
    await ctx.send(conversation.to_message())

client.run(token, log_handler=handler)

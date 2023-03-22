# openai interface

Interface and example code for using openAI's python AI, including original completion interface,
image interface and chat interface. An example Discord chatGPT bot is provided.

**OPENAI_API_KEY** needs to be set appropriate

# Discord ChatGPT Bot

application: [discordbot.py](discordbot.py)

```
./discordbot.py --help
usage: discordbot.py [-h] [-f DIRECTORY] [-m MODEL]

Interface to chatGPT discord-bot

optional arguments:
  -h, --help            show this help message and exit
  -f DIRECTORY, --directory DIRECTORY
                        Directory to store chats (default: discord_chats)
  -m MODEL, --model MODEL
                        Select the model to use (default: gpt-3.5-turbo)
```

## Usage

* Have a conversation in any channel on your server; currently discord-bot is not restricted to particular channels
* To start a new conversation, use **.clear**, **.new**, **.reset**, **.newconv**
* To report the current system role, use **.role**, **.system**, **.sysrole**, **.system_role**
* To change the system role and start a new conversation, use **.role** _<system role info>_, or alias
* To save the current conversation use **.save**, **.store**, **.record**
  * Conversations are stored as JSON objects in the _**discord_chats**_ directory
  * Conversations are named using the time the conversation is stored
  * The log directory can be specified as a command parameter when discordbot.py is run
* Use **.report** to show the complete conversation as a JSON object

## Create a new bot in Discord

Firstly you need to create the bot

1. Go to the Discord Developer Portal website: https://discord.com/developers/applications
2. Click the "New Application" button in the top right corner.
3. Enter a name for your application and click "Create".
4. Enter bot name, description etc. If you want an app icon, use [ChatGPT_bot_icon.png](resources/ChatGPT_bot_icon.png) (created with Midjourney)
5. On the left-hand side of the screen, click "Bot".
6. Click the "Add Bot" button (you may need to go through 2FA to do this)
7. Customize your bot by giving it a name and profile picture.
8. Under the "Token" section, click "Copy" to copy the bot token. 
9. This token should be stored in **DISCORD_CHATGPT_BOT_TOKEN**

## Adding the bot to your Discord

Additionally, you need to allow the bot access to your Discord via OAuth2

1. In the application in the Discord Developer Portal, go to OAuth2 -> URL Generator
2. Select the following scopes: **bot**, **applications.commands**
3. In the Bot Permissions window, select _all_ **Text Permissions**
4. Copy the Generated URL and go to that address and accept the permissions to allow your bot to be used on you discord server

# Slack ChatGPT Bot 

application: [slashbot.py](slashbot.py)

## Create a new bot in Slack

1. Go to https://api.slack.com/, and select Create an app
2. Select from scratch, select name and workspace, then create the app
3. Select a Bot
4. Add scopes: **chat.write**, **commands**, **chat:write.customize**, **channels.join**
5. Get App Credentials from Basic Information
6. Get **SLACK_BOT_TOKEN** from OAuth & Permissions tab in _OAuth Tokens for Your Workspace_ section
7. Also see https://slack.dev/bolt-python/tutorial/getting-started
8. _**Basic Information -> App Token**_ section. Generate Token and scopes. Add **connections:write**
9. Use this token as **SLACK_APP_TOKEN**
10. Go to socket mode and Enable Socket Mode
11. Ensure _Allow users to send Slash commands and messages from the messages tab_ is enabled in _**App Home->Show Tabs**_
12. You can now add the app to your Slack (OAuth Tokens for Your Workspace -> Reinstall to Workspace )

## Adding commands

* Slash command entries need to be added for the bot on https://api.slack.com/
  * Add **/new**, **/report**, **/chats**

## Event API

Not sure this is relevant yet, but to enable Events

1. Ensure **_Event Subscriptions->Enable Events_** is on
2. Subscribe to bot events: **app_mention**, **message.channels**, **message.im**

## Other notes

* If you make a change to bot (such as permission), reinstall the bot using Apple-R (on Mac)

# TODO

* Refactor code into more of a helper library model so code can be reused
* Option to display previous chats, or restart previous chats
* Open viewer for images
* Auto-summarize at end of chat
* Add slash command support - see https://stackoverflow.com/questions/71165431/how-do-i-make-a-working-slash-command-in-discord-py
  * Looks like its better to have a tree to attach commands too rather than using the command.Bot approach
  * Need to use a GUILD_ID - don't understand that yet

* Discord front-end
  * Use .commands to do operations like start/stop conversations, change temperature, regenerate responses etc.
  * Allow multiple threads for multiple chats
  * .commands to change behavior to different models (like images)
  * The bot will respond on any channel in the server; it would be better it is monitor specific channels
  * There is only one global conversation; there should be unique conversations to each channel (or possibly thread)

* Slack front-end
  * Basic implementation

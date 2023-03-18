# openai interface

Interface and example code for using openAI's python AI, including original completion interface,
image interface and chat interface. An example Discord chatbot is provided.

# Discord Chat Bot

application: [discordbot.py](discordbot.py)

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

# TODO

* Refactor code into more of a helper library model so code can be reused
* Option to display previous chats, or restart previous chats
* Open viewer for images
* Auto-summarize at end of chat

* Discord front-end
  * Use .commands to do operations like start/stop conversations, change temperature, regenerate responses etc.
  * Allow multiple threads for multiple chats
  * .commands to change behavior to different models (like images)


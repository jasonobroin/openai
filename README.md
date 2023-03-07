# openai interface

Interface and example code for using openAI's python AI, including original completion interface,
image interface and chat interface.

# TODO

* Refactor code into more of a helper library model so code can be reused
* Option to record chats in a directory (as JSON), and option to display previous chats
* Pretty printer for chats (i.e. show code blocks in a cleaner fashion)
* Open viewer for images
* Auto-summarize at end of chat
* Ability to restart a chat

* Discord front-end
  * Use on_message() model to allow regular flow
  * Use .commands to do operations like start/stop conversations, change temperature, regenerate responses etc.
  * Allow multiple threads for multiple chats
  * .commands to change behavior to different models (like images)


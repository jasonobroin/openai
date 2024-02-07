#!/usr/bin/env python3

"""
Code to interface with the OpenAI system chatGPT model and provide a conversation.

Command options allow temperature to be changed and the system role to be specified

Notes

* Need to enabling billing when used all free credits
* The current chatGPT model is called gpt-3.5-turbo, and is incrementally improved
* It uses a different calling interface to the older completion models, aimed at support conversations

"""

from datetime import datetime

import argparse
import json
import os
import textwrap
from openai import OpenAI

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])


# Set the API key and model




class Turn:
    """Define an turn in a conversation"""

    def __init__(self, role, content):
        self.role = role
        self.content = content

    def to_dict(self):
        """Convert a Turn into a dictionary entry"""
        return {"role": self.role, "content": self.content}


class Conversation:
    def __init__(self):
        self.turns = []

    def add_turn(self, role, content):
        turn = Turn(role, content)
        self.turns.append(turn)

    def to_message(self):
        """Convert a Conversation into a message list"""
        message = []
        for conv in self.turns:
            message.append({"role": conv.role, "content": conv.content})
        return message

    def to_dict(self):
        """Convert a Conversation into a dictionary"""
        return {"chat": [obj.to_dict() for obj in self.turns]}

    def clear(self):
        """Clear the list"""
        self.turns.clear()

    def set_system_role(self, role):
        """Set the system role for this conversation"""
        # TODO: Perhaps always do this in the first slot?
        self.add_turn("system", role)

    def get_system_role(self):
        """Get the current system role for this conversation"""
        return self.turns[0].content

    def num_turns(self):
        """Return the number of turns in the conversation"""
        return int((len(self.turns)-1) / 2)

    def get_entry(self, num):
        return self.turns[num] if num <= len(self.turns) else Turn("","")

    def __str__(self):
        conversation_str = ""
        for turn in self.turns:
            conversation_str += f"{turn.role}: {turn.content}\n"
        return conversation_str



_print = print


def pprint(*args, **kw):
    _print("[%s]" % (datetime.now()), *args, **kw)


def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description="Interface to openAI API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-l", "--list-models", help="List available models", action="store_true")
    parser.add_argument("-t", "--temperature", help="Set the model's temperature from 0 to 1. 0 is more predictable; 1 more creative", type=float, default=0.6)
    parser.add_argument("-m", "--model", help="Select the model to use", default="gpt-4") # gpt-4
    parser.add_argument("-u", "--usage", help="Report usage", action="store_true")
    parser.add_argument("-d", "--debug", help="Report debug info", action="store_true")
    parser.add_argument("-r", "--role", help="Describe the system's role", default="You are a helpful assistant")
    parser.add_argument("-s", "--store", help="Store conversation", action="store_false")
    parser.add_argument("-f", "--directory", help="Directory to store chats", default="chats")

    return parser.parse_args()


def list_models():
    """List the various model types - current flat, but would be interesting to show hierarchy"""
    models = client.models.list()
#    print(models)

    for model in models["data"]:
        print(model["id"])
    print()


def write_chat(directory, conv_time, conversation):
    """Write a chat to a file, creating the directory if required"""

    # Create directory if required
    if not os.path.exists(directory):
        os.makedirs(directory)

    my_dict = conversation.to_dict()

    file_path = directory + "/" + conv_time
    print(f"write to {file_path}")

    with open(file_path, "w") as file:
        json.dump(my_dict, file)

    print(f"stored chat as {file_path}")
    return file_path


def take_turn(conversation, model, message):
    """Interface to support discord - record user message, ask openai and record (and return) response"""
    conversation.add_turn("user", message)
    messages = conversation.to_message()
    response = client.chat.completions.create(model=model, messages=messages, n=1, stop=None,
                                            temperature=0.6)
    reply = response.choices[0].message.content
    conversation.add_turn("assistant", reply)
    return reply

def chat(args):
    """Provide a bidirectional user chat interface to openAPI's chat model"""
    print(f"System role: {args.role}")

    conversation = Conversation()
    conversation.add_turn("system", args.role)
    try:
        while True:
            # Set the prompt and generate text
            prompt = input('openai> ')

            end_markers = ["stop", "end", "finish", "done", "complete", "exit", "quit"]
            if prompt.lower() in end_markers:
                print("Chat finished")
                if args.store:
                    write_chat(args.directory, start_time, conversation)
                break

            conversation.add_turn("user", prompt)
            messages = conversation.to_message()
            if args.debug:
                print(messages)
            response = client.chat.completions.create(model=args.model, messages=messages, n=1, stop=None,
                                                    temperature=args.temperature)
            reply = response.choices[0].message.content
            conversation.add_turn("assistant", reply)

            paragraph = str.splitlines(reply)
            for lines in paragraph:
                wrapper = textwrap.TextWrapper(width=80, break_long_words=True)
                msg = wrapper.wrap(lines)
                for line in msg:
                    print(line)
                print()
            if args.usage:
                print(f'[Prompt tokens: {response.usage.prompt_tokens} Completion tokens: {response.usage.completion_tokens} '
                      f'Total tokens: {response.usage.total_tokens}]')
    except KeyboardInterrupt:
        print('exiting')
        if args.store:
            write_chat(args.directory, start_time, conversation)
    except EOFError:
        print('exiting')
        if args.store:
            write_chat(args.directory, start_time, conversation)


def main():
    """A turn based conversation interface to openAI's chat API"""

    args = get_args()

    if args.list_models:
        list_models()

    global start_time
    start_time = datetime.now()
    start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
    chat(args)


if __name__ == "__main__":
    main()

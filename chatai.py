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
import openai
import os
import textwrap


# Set the API key and model

openai.api_key = os.environ['OPENAI_API_KEY']


class Conversation:
    """Define an entry in a conversation"""
    # TODO: Perhaps this isn't a Conversation, but a Turn?

    def __init__(self, role, content):
        self.role = role
        self.content = content

    def to_dict(self):
        """Convert a Conversation (really a Turn) into a dictionary entry"""
        # Note I think we really want this class to contain a list, and to_dict should walk the whole list
        return {"role": self.role, "content": self.content}


def getMessage(conversation: Conversation):
    """Convert a Conversation into a message list"""
    message = []
    for conv in conversation:
        message.append({"role": conv.role, "content": conv.content})
    return message


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
    parser.add_argument("-m", "--model", help="Select the model to use", default="gpt-3.5-turbo")
    parser.add_argument("-u", "--usage", help="Report usage", action="store_true")
    parser.add_argument("-d", "--debug", help="Report debug info", action="store_true")
    parser.add_argument("-r", "--role", help="Describe the system's role", default="You are a helpful assistant")
    parser.add_argument("-s", "--store", help="Store conversation", action="store_false")
    parser.add_argument("-f", "--directory", help="Directory to store chats", default="chats")

    return parser.parse_args()


def list_models():
    """List the various model types - current flat, but would be interesting to show hierarchy"""
    models = openai.Model.list()
#    print(models)

    for model in models["data"]:
        print(model["id"])
    print()


def write_chat(args, conversation):
    """Write a chat to a file, creating the directory if required"""

    # Create directory if required
    if not os.path.exists(args.directory):
        os.makedirs(args.directory)

    # convert list of objects to dictionary
    # TODO: Make this a function? On the Conversation?
    my_dict = {"chat": [obj.to_dict() for obj in conversation]}

    file_path = args.directory + "/" + start_time

    with open(file_path, "w") as file:
        json.dump(my_dict, file)

    print(f"stored chat as {file_path}")


def chat(args):
    """Provide a bidirectional user chat interface to openAPI's chat model"""
    print(f"System role: {args.role}")

    # TODO: We have a list of Conversation objects - but isn't that our conversation?
    # I think we want Turns, and have Conversation be a list of Turns?
    conversation = [Conversation("system", args.role)]
    try:
        while True:
            # Set the prompt and generate text
            prompt = input('openai> ')

            end_markers = ["stop", "end", "finish", "done", "complete"]
            if prompt.lower() in end_markers:
                print("Chat finished")
                if args.store:
                    write_chat(args, conversation)
                break

            conversation.append(Conversation("user", prompt))
            messages = getMessage(conversation)
            if args.debug:
                print(messages)
            response = openai.ChatCompletion.create(model=args.model, messages=messages, n=1, stop=None,
                                                    temperature=args.temperature)
            reply = response.choices[0].message.content
            conversation.append(Conversation("assistant", reply))

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
            write_chat(args, conversation)
    except EOFError:
        print('exiting')
        if args.store:
            write_chat(args, conversation)


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

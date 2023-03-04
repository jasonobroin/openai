#!/usr/bin/env python3

'''
Code to interface with the OpenAI system chatGPT model and provide a conversation.

Command options allow temperature to be changed and the system role to be specified

Notes

* Need to enabling billing when used all free credits
* The current chatGPT model is called gpt-3.5-turbo, and is incrementally improved
* It uses a different calling interface to the older completion models, aimed at support conversations

'''

import argparse
import textwrap
import openai
import os
import time

from datetime import datetime, timedelta, timezone

# Set the API key and model

openai.api_key = os.environ['OPENAI_API_KEY']

class Conversation:
    def __init__(self, role, content):
        self.role = role
        self.content = content

def getMessage(conversation : Conversation):
    message = []
    for conv in conversation:
        message.append({"role":conv.role, "content":conv.content})
    return message

_print = print
def pprint(*args, **kw):
    _print("[%s]" % (datetime.now()),*args, **kw)

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



    return parser.parse_args()

def list_models():
    '''List the various model types - current flat, but would be interesting to show hierarchy'''
    models = openai.Model.list()
#    print(models)

    for model in models["data"]:
        print(model["id"])
    print()

def main():

    args = get_args()

    if args.list_models == True:
        list_models()

    print(f"System role: {args.role}")
    conversation = [Conversation("system", args.role)]
    while True:
        # Set the prompt and generate text
        prompt = input('openai> ')
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

if __name__ == "__main__":
    main()
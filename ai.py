#!/usr/bin/env python3

'''
Code to interface with the OpenAI system, using non-chat models

Notes

* Need to enabling billing when used all free credits

Issues

* There isn't the chatGPT model - its using the older interface (v1/completions) rather than (v1/chat/completions)
  and provides access to underlying models (such as text completion, code help etc). The interface is not intended
  for a chat style usage.
'''

import argparse
import textwrap
import openai
import os
import time

from datetime import datetime, timedelta, timezone

# Set the API key and model

openai.api_key = os.environ['OPENAI_API_KEY']

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
    parser.add_argument("-m", "--model", help="Select the model to use", default="text-davinci-003")

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

    while True:
        # Set the prompt and generate text
        prompt = input('openai> ')
        #prompt = "What is the best way to work out the value of PI"
        completions = openai.Completion.create(engine=args.model, prompt=prompt, max_tokens=1024, n=1, stop=None,
                                               temperature=args.temperature)
        message = completions.choices[0].text

        paragraph = str.splitlines(message)
        for lines in paragraph:
            wrapper = textwrap.TextWrapper(width=80, break_long_words=True)
            msg = wrapper.wrap(lines)
            for line in msg:
                print(line)
            print()

if __name__ == "__main__":
    main()
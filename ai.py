#!/usr/bin/env python3

'''
Code to interface with the OpenAI system, such as chatGPT

Notes

* Need to enabling billing when used all free credits

Issues

* There isn't an chatGPT model - there are access to underlying models (such as text completion, code help etc.
* These don't have history - you need to feel back in previous responses to do that (which might use tokens?)

'''

import argparse
import textwrap
import openai
import os
import time

from datetime import datetime, timedelta, timezone

# Set the API key and model

openai.api_key = os.environ['OPENAI_API_KEY']

model_engine = "text-davinci-003" # "chatGPT"

_print = print
def pprint(*args, **kw):
    _print("[%s]" % (datetime.now()),*args, **kw)

def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description="Interface to openAI API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-m", "--models", help="List available models", action="store_true")

    return parser.parse_args()

def list_models():
    '''List the various model types - current flat, but would be interesting to show hierarchy'''
    models = openai.Model.list()
    print(models)

    for model in models["data"]:
        print(model["id"])
    print()

def main():

    args = get_args()

    if args.models == True:
        list_models()

    while True:
        # Set the prompt and generate text
        prompt = input('openai> ')
        #prompt = "What is the best way to work out the value of PI"
        completions = openai.Completion.create(engine=model_engine, prompt=prompt, max_tokens=1024, n=1, stop=None, temperature=0.5)
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
#!/usr/bin/env python3

'''
Code to interface with the OpenAI system, such as chatGPT

Notes

* Need to enabling billing when used all free credits

Issues

* There isn't an chatGPT model - there are access to underlying models (such as text completion, code help etc.
* These don't have history - you need to feel back in previous responses to do that (which might use tokens?)

'''

import openai
import os

# Set the API key and model

openai.api_key = os.environ['OPENAI_API_KEY']

model_engine = "text-davinci-003" # "chatGPT"

#print(openai.Model.list())

# Set the prompt and generate text
prompt = "What is the best way to work out the value of PI"
completions = openai.Completion.create(engine=model_engine, prompt=prompt, max_tokens=1024, n=1, stop=None, temperature=0.5)
message = completions.choices[0].text
print(message)
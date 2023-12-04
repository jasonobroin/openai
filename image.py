from openai import OpenAI

from flask import Flask, send_file, make_response
import io
import webbrowser
import time
import threading

import os
import base64

# Replace YOUR_API_KEY with your OpenAI API key
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Specify the model to use
model = 'dall-e-3'

# Specify the image size
size = '1024x1024'

# Specify image quality
quality = 'hd' # Could be 'standard'

app = Flask(__name__)

img_ready = False

def ask_input():
    global img_ready

    time.sleep(1)

    while True:
        prompt = input('dalle3> ')

        img_ready = False

        response = client.images.generate(prompt=prompt,
                                          model=model,
                                          size=size,
                                          quality=quality,
                                          response_format="b64_json")

        global image_data
        image_data = response.data[0].b64_json
        with open('image.png', 'wb') as handler:
            handler.write(base64.b64decode(image_data))
        img_ready = True

@app.route('/status')
def status():
    return jsonify({'ready': img_ready})

@app.route('/')
def display_image():
    if img_ready:
    #    img_b64 = "..."  # Your base64 string here.
        img_bytes = base64.b64decode(image_data)
        img = io.BytesIO(img_bytes)
        return send_file(img, mimetype='image/png')
    else:
        return "Image is not ready yet. Please refresh later."

if __name__ == '__main__':
    threading.Thread(target=ask_input).start()
    webbrowser.open("http://127.0.0.1:5000/")
    app.run()
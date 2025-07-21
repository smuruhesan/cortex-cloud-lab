# app.py
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    # Get the environment variable for a dynamic message
    message = os.environ.get('GREETING_MESSAGE', 'Hello from Cortex Cloud Lab!')
    return f"<h1>{message}</h1>"

if __name__ == '__main__':
    # Listen on all available network interfaces on port 5000
    app.run(host='0.0.0.0', port=5000)

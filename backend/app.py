from flask import Flask, jsonify
import os

# Test

app = Flask(__name__)

@app.route('/')
def home():
    # Simple endpoint to check if the backend is running
    return "Backend is running!"

@app.route('/api/message')
def get_message():
    # A simple API endpoint returning a message
    # In a real app, this might fetch data from a database
    message = os.environ.get("MESSAGE_FROM_CONFIG", "Default message from backend")
    return jsonify({"message": message})

if __name__ == '__main__':
    # Run the app on port 5000, accessible from any IP within the container
    app.run(host='0.0.0.0', port=5000)
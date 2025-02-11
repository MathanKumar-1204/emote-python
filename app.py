from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import joblib
import pandas as pd
from datetime import datetime

from groq import Groq
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase Admin SDK (ensure you have your service account JSON)
cred = credentials.Certificate("emote-2aaca-firebase-adminsdk-fbsvc-186a7bd101.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://emote-2aaca-default-rtdb.firebaseio.com/'
})

# Initialize the Groq client
client = Groq(
    api_key = "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"
)

# Set up the Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set up the conversation history
conversation_history = [
    {
        "role": "system",
        "content": "You are a conversational AI chatbot for real-time support and guidance. The chatbot should respond immediately with short, helpful messages."
    }
]

def ask(user_input):
    conversation_history.append({
        "role": "user",
        "content": user_input
    })

    try:
        chat_completion = client.chat.completions.create(
            messages=conversation_history,
            model="llama3-70b-8192",
            temperature=0.5,
            max_tokens=1024,
            top_p=1,
            stop=None,
            stream=False,
        )

        response = chat_completion.choices[0].message.content
        conversation_history.append({
            "role": "assistant",
            "content": response
        })

        print("Groq API Response:", response)  # Debugging step
        return response

    except Exception as e:
        print(f"Error calling Groq API: {str(e)}")
        return "Sorry, I encountered an error."

@app.route('/get_answer', methods=['POST'])
def get_answer():
    data = request.json
    user_message = data.get('question', '')

    print("User question received:", user_message)  # Debugging step

    # Use the Groq-based AI model to get a response
    ai_response = ask(user_message)

    print("AI Response to be sent:", ai_response)  # Debugging step

    return jsonify({'answer': ai_response})

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    answers = data.get('answers')
    username = data.get('username')

    # Define answer mapping and threshold for "depressed"
    answer_map = {
        'Never': 0,
        'Rarely': 1,
        'Sometimes': 2,
        'Often': 3,
        'Always': 4
    }

    # Convert the answers to numerical values
    scores = [answer_map.get(answer, 0) for answer in answers]
    threshold = 40  # You can adjust this threshold
    total_score = sum(scores)

    # Determine the result
    result = "You are depressed" if total_score > threshold else "You are fine"

    # Get the current date
    current_date = datetime.now().strftime("%d-%m-%Y")

    # Save result to Firebase
    try:
        ref = db.reference(f'users/{username}/{current_date}')
        ref.set({
            'score': total_score,
            'state': result
        })
        return jsonify({"message": "Result saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
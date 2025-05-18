from groq import Groq
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from pdf_loader import load_pdf_text

# Load environment variables
load_dotenv()

# Initialize the Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# Add a check for the API key
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in .env file or environment variables.")

app = Flask(__name__, static_folder='../', static_url_path='')

# Load PDF text
pdf_text = None

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    global pdf_text
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    if file:
        file_path = os.path.join(app.static_folder, 'uploads', file.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        pdf_text = load_pdf_text(file_path)
        if pdf_text is None:
            return jsonify({'success': False, 'message': 'Failed to process PDF'})
        return jsonify({'success': True, 'message': 'File uploaded successfully'})
    return jsonify({'success': False, 'message': 'Upload failed'})

@app.route('/chat', methods=['POST'])
def chat():
    global pdf_text
    data = request.json
    message = data.get('message', '')
    if not pdf_text:
        return jsonify({'response': 'Please upload a PDF first.'})
    
    # Create the system prompt with the medical record
    system_prompt = """
You are Deha AI, a compassionate and knowledgeable medical case manager.
Your primary responsibility is to assist the individual in understanding and managing their health based on their provided medical record.
You should engage in a continuous conversation, answering questions directly and providing relevant information and guidance derived *only* from the medical data.

Maintain a warm, empathetic, and encouraging tone throughout the conversation.
Explain medical terms and concepts in a clear and accessible way, avoiding jargon where possible.
When responding to questions, always consider the specific conditions, medications, and recent lab results presented in the medical record.

Instead of simply stating facts, weave them into your responses naturally as part of the ongoing dialogue.
Offer practical advice and considerations tailored to the individual's situation.
For example, when discussing diet or exercise, highlight aspects relevant to their conditions, cholesterol levels, and blood pressure.
Encourage them to take an active role in their health management and always suggest consulting their doctor for any significant changes or concerns.

Avoid explicitly stating that you are 'thinking' or outlining your internal reasoning steps.
Your responses should flow naturally as if you are genuinely engaged in a conversation.

Your goal is to make the individual feel supported, informed, and empowered in managing their health.
"""
    
    try:
        # Create messages for the chat
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\nMedical Record:\n{pdf_text}"},
            {"role": "user", "content": message}
        ]
        
        # Get response from Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=200,
            stream=False
        )
        
        ai_response = response.choices[0].message.content.strip()
        return jsonify({'response': ai_response})
        
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({'response': 'Sorry, I encountered an error while processing your request.'})

def medical_chatbot(initial_prompt, medical_record):
    """
    A continuous conversation medical chatbot that uses a provided medical record.

    Parameters:
      - initial_prompt: The system prompt to guide the chatbot's behavior.
      - medical_record: The text content of the patient's medical record.
    """
    system_prompt_with_record = f"{initial_prompt}\n\nMedical Record:\n{medical_record}"
    messages = [{"role": "system", "content": system_prompt_with_record}]
    print("Deha AI Medical Chatbot Activated (Text Mode)")
    print("Type 'exit' to end the conversation.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            break

        messages.append({"role": "user", "content": user_input})

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,  # Adjust for desired randomness
                max_tokens=200,     # Adjust for desired response length
                stream=False
            )
            ai_response = response.choices[0].message.content.strip()
            print(f"Deha AI: {ai_response}\n")
            messages.append({"role": "assistant", "content": ai_response})

        except Exception as e:
            print(f"An error occurred: {e}\n")

if __name__ == "__main__":
    app.run(debug=True)
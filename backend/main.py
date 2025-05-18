from flask import Flask, request, jsonify, send_from_directory, Response, send_file
from datetime import datetime
from flask_cors import CORS
import os
import logging
from pdf_loader import load_pdf_text
import groq
from dotenv import load_dotenv
import tempfile
from audio import transcribe_audio, client as elevenlabs_client, listen, speak
from io import BytesIO
import json
from event_extractor import extract_events

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Groq client
client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__, static_folder='../', static_url_path='')
CORS(app)

# Global variable to store PDF text
pdf_text = None

@app.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())
    logger.debug('Files: %s', request.files)
    logger.debug('Form: %s', request.form)

@app.after_request
def log_response_info(response):
    # Only log response data for JSON responses
    if response.mimetype == 'application/json':
        logger.debug('Response: %s', response.get_data())
    return response

@app.route('/')
def index():
    logger.info('Serving index.html')
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        logger.error('Error serving index.html: %s', str(e))
        return str(e), 500

@app.route('/<path:path>')
def serve_static(path):
    logger.info('Serving static file: %s', path)
    try:
        return send_from_directory(app.static_folder, path)
    except Exception as e:
        logger.error('Error serving static file %s: %s', path, str(e))
        return str(e), 404

@app.route('/test', methods=['GET'])
def test():
    logger.info('Test endpoint called')
    return jsonify({"message": "Server is working!"})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.pdf'):
        # Save the file temporarily
        temp_path = os.path.join('temp', file.filename)
        os.makedirs('temp', exist_ok=True)
        file.save(temp_path)
        
        # Process the PDF
        text = load_pdf_text(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({'text': text})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    try:
        logger.info('Received chat request')
        data = request.json
        message = data.get('message', '')
        
        if not pdf_text:
            logger.error('No PDF loaded')
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
        
        # Create messages for the chat
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\nMedical Record:\n{pdf_text}"},
            {"role": "user", "content": message}
        ]
        
        logger.info('Sending request to Groq')
        # Get response from Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=200,
            stream=False
        )
        
        ai_response = response.choices[0].message.content.strip()
        logger.info('Received response from Groq')
        return jsonify({'response': ai_response})
        
    except Exception as e:
        logger.error('Error in chat: %s', str(e), exc_info=True)
        return jsonify({'response': 'Sorry, I encountered an error while processing your request.'})

@app.route('/voice', methods=['POST'])
def voice():
    try:
        logger.info('Received voice request')
        
        if 'audio_file' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio_file']
        
        if not pdf_text:
            logger.error('No PDF loaded')
            return jsonify({'response': 'Please upload a PDF first.'})
        
        # Save the audio file temporarily
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        audio_file.save(temp_audio.name)
        
        # Transcribe the audio using Groq's Whisper
        transcript = transcribe_audio(temp_audio.name)
        
        # Clean up the temporary audio file after transcription
        os.unlink(temp_audio.name)

        if not transcript:
            return jsonify({'error': 'Failed to transcribe audio'}), 400
            
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
        
        # Create messages for the chat
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\nMedical Record:\n{pdf_text}"},
            {"role": "user", "content": transcript}
        ]
        
        logger.info('Sending transcribed text to Groq')
        # Get response from Groq (using the main client)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=200,
            stream=False
        )
        
        ai_response = response.choices[0].message.content.strip()
        logger.info('Received response from Groq')
        
        # We don't perform TTS here, the frontend will call the /tts endpoint
        
        return jsonify({
            'transcript': transcript,
            'response': ai_response
        })
        
    except Exception as e:
        logger.error('Error in voice: %s', str(e), exc_info=True)
        # Ensure temp file is cleaned up even on error if it was created
        if 'temp_audio' in locals() and os.path.exists(temp_audio.name):
            os.unlink(temp_audio.name)
        return jsonify({'error': 'Sorry, I encountered an error while processing your request.'}), 500

@app.route('/tts', methods=['POST'])
def text_to_speech():
    try:
        data = request.json
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        logger.info('Converting text to speech with ElevenLabs')
        # Convert text to speech using ElevenLabs (using the imported client)
        audio = elevenlabs_client.text_to_speech.convert(
            text=text,
            voice_id="19STyYD15bswVz51nqLf",  # Default voice ID
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        
        # Create a temporary file to store the audio
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        # ElevenLabs convert returns bytes directly, no need to read
        temp_audio.write(audio)
        temp_audio.close()
        
        logger.info('Sending audio file to frontend')
        # Send the audio file
        return send_file(
            temp_audio.name,
            mimetype='audio/mpeg',
            # Don't send as attachment for playback
            # as_attachment=True,
            # download_name='response.mp3'
        )
        
    except Exception as e:
        logger.error('Error in TTS: %s', str(e), exc_info=True)
        # Ensure temp file is cleaned up even on error if it was created
        if 'temp_audio' in locals() and os.path.exists(temp_audio.name):
            os.unlink(temp_audio.name)
        return jsonify({'error': 'Sorry, I encountered an error while processing your request.'}), 500

@app.route('/listen', methods=['POST'])
def listen_endpoint():
    logger.info("=== Starting /listen endpoint ===")
    try:
        if not pdf_text:
            logger.error("No PDF loaded")
            return jsonify({"error": "Please upload a PDF first"}), 400

        logger.info("Calling listen() function")
        # The listen() function now handles recording and transcribing
        transcript = listen()
        
        # Explicitly log the received transcript value and its type
        logger.info(f"Received transcript value: '{transcript}', Type: {type(transcript)}")
        
        # Check if transcript is empty or very short after logging
        # Consider single characters or very short strings as potentially failed transcription
        if not transcript or len(transcript.strip()) < 2:
            logger.warning(f"Transcript is empty or too short: '{transcript}'. Treating as no speech detected.")
            # Return a specific message if no speech is detected, as this is expected behavior if user doesn't speak
            return jsonify({"message": "No speech detected"}), 200 # Return 200 as it's not a fatal error

        # Create system prompt for Groq
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


Medical Record:
""" + pdf_text

        logger.info(f"Sending request to Groq with transcript: '{transcript}'")
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript}
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=200,
            stream=False,
            temperature=0.7
        )
        logger.info("Received response from Groq")
        ai_response = response.choices[0].message.content.strip()

        # Convert response to speech using ElevenLabs client directly
        logger.info("Converting response to speech using ElevenLabs")
        # Assuming elevenlabs_client.text_to_speech.convert returns a generator
        audio_generator = elevenlabs_client.text_to_speech.convert(
            text=ai_response,
            voice_id="19STyYD15bswVz51nqLf",  # Default voice ID
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        # Collect audio bytes from the generator
        audio_bytes = b''.join(list(audio_generator))
        logger.info(f"Collected {len(audio_bytes)} bytes from ElevenLabs generator")

        # Use BytesIO to create an in-memory binary stream
        audio_stream = BytesIO(audio_bytes)
        audio_stream.seek(0) # Rewind to the beginning of the stream

        # Send audio file
        logger.info("Sending audio stream")
        # send_file can handle BytesIO objects
        return send_file(
            audio_stream,
            mimetype='audio/mpeg',
            as_attachment=False, # Set to False for direct playback in browser
            download_name='response.mp3'
        )

    except Exception as e:
        logger.error(f"Error in /listen endpoint: {str(e)}")
        # We should return an error response if something goes wrong in the backend processing
        return jsonify({"error": "An error occurred while processing your request."}), 500
    finally:
        logger.info("=== Ending /listen endpoint ===")

@app.route('/extract-events', methods=['POST'])
def get_events():
    try:
        # For now, return some sample events
        events = [
            {
                'date': '2024-03-20',
                'time': '10:00 AM',
                'type': 'appointment',
                'description': 'Annual physical checkup with Dr. Smith',
                'priority': 'high'
            },
            {
                'date': '2024-03-25',
                'time': '02:30 PM',
                'type': 'test',
                'description': 'Blood work at City Lab',
                'priority': 'medium'
            },
            {
                'date': '2024-03-15',
                'time': '09:00 AM',
                'type': 'medication',
                'description': 'Take blood pressure medication',
                'priority': 'high',
                'recurring': True
            }
        ]
        return jsonify({'events': events})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    logger.info("Starting server...")
    app.run(debug=True, host='127.0.0.1', port=5000)
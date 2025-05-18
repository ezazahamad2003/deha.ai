#this is a deepgram tts 

# audio.py

import pyaudio
import wave
import tempfile
import numpy as np
from collections import deque
import webrtcvad
import time
import speech_recognition as sr
import simpleaudio as sa
import pygame
from PyQt5.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import logging
import threading
import asyncio
import os
from groq import Groq
from pathlib import Path
import sounddevice as sd
import soundfile as sf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variable
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable is not set")

# Initialize ElevenLabs client
client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def speak(text: str) -> None:
    """
    Converts text to speech using ElevenLabs API and plays it.
    
    Args:
        text (str): The text to convert to speech
    """
    try:
        logger.info("Converting text to speech: %s", text)
        
        # Convert text to speech
        audio = client.text_to_speech.convert(
            text=text,
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Default voice ID
            model_id="eleven_monolingual_v1"
        )
        
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(audio)
            temp_file_path = temp_file.name
        
        # Play the audio
        play(temp_file_path)
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error("ElevenLabs TTS Error: %s", str(e))
        raise

def record_audio(samplerate=16000, channels=1, chunk=320, silence_duration=2.0):
    """
    Records audio from the microphone and stops when silence is detected.

    Parameters:
      - samplerate: The sample rate for recording (must be 8000, 16000, 32000, or 48000).
      - channels: Number of audio channels (must be 1 for VAD).
      - chunk: The number of frames per buffer (must align with 10ms audio length for VAD).
      - silence_duration: Time (in seconds) of silence required to stop recording.

    Returns:
      The filename of the recorded WAV file.
    """
    logger.info("Starting audio recording...")

    p = None
    stream = None
    temp_wav = None

    try:
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=samplerate,
                        input=True,
                        frames_per_buffer=chunk)

        # Initialize WebRTC VAD
        vad = webrtcvad.Vad()
        vad.set_mode(1)  # Less aggressive mode for better speech detection

        frames = []
        silence_count = 0
        speech_detected = False
        total_frames = 0
        silence_threshold = int(silence_duration * samplerate / chunk)  # Convert silence time to chunks

        logger.info("Listening for speech... (VAD mode 1, silence threshold %.2f sec)", silence_duration)
        
        start_time = time.time()
        timeout = 15 # seconds

        while True:
            if time.time() - start_time > timeout:
                logger.warning("Recording timed out after %d seconds", timeout)
                break

            try:
                # Read data, catching potential overflow errors
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)
                total_frames += 1
                
                # Convert audio to PCM16 little-endian format for VAD
                # Check if data has enough bytes for int16 conversion
                if len(data) < 2:
                     logger.debug("Skipping VAD check, data too short: %d bytes", len(data))
                     continue # Skip VAD for tiny chunks
                pcm_data = np.frombuffer(data, dtype=np.int16)

                # Check VAD only if chunk size aligns with 10ms audio length (chunk=320 for 16000Hz)
                # 16000 samples/sec * 0.01 sec = 160 samples. 160 samples * 2 bytes/sample = 320 bytes.
                # So chunk=320 is 10ms for 16kHz.
                if chunk * 2 == len(data):
                     is_speech = vad.is_speech(pcm_data.tobytes(), samplerate)

                     if is_speech:
                         speech_detected = True
                         silence_count = 0  # Reset silence count when speech is detected
                         logger.debug("Speech detected. Silence count reset.")
                     elif speech_detected: # Only increment silence after speech has been detected
                         silence_count += 1  # Increment silence count when no speech is detected
                         if silence_count % 10 == 0: # Log every 10 silent chunks after speech
                             logger.debug(f"Silence after speech count: {silence_count}/{silence_threshold}")
                     else:
                          logger.debug("No speech detected yet. Silence count: %d", silence_count)

                     # Only stop if we've detected speech and then silence for the required duration
                     if speech_detected and silence_count > silence_threshold:
                         logger.info(f"Silence detected after speech for > {silence_duration} sec, stopping recording. Total frames: {total_frames}")
                         break
                else:
                    logger.debug("Skipping VAD check, chunk size %d does not align with 10ms for %dHz", chunk, samplerate)

            except IOError as e:
                 # Handle potential input overflow specifically
                 if e.errno == pyaudio.paInputOverflowed:
                     logger.warning("Input overflowed: %s", str(e))
                 else:
                     logger.error("Error during audio stream read: %s", str(e))
                 # Continue recording despite error? Or break?
                 # For now, let's break to avoid infinite loops on persistent errors
                 break
            except Exception as e:
                logger.error("Unexpected error during audio recording loop: %s", str(e))
                break # Break on unexpected errors

        # Cleanup PyAudio resources
        logger.info("Recording stopped. Total frames collected: %d", total_frames)
        if stream and stream.is_active():
             stream.stop_stream()
        if stream:
             stream.close()
        if p:
             p.terminate()
        logger.info("PyAudio resources cleaned up.")

        if not frames:
            logger.error("No audio frames recorded.")
            return None

        if not speech_detected: # Return None if no speech was ever detected
             logger.warning("No speech detected throughout recording.")
             return None

        # Save to a temporary WAV file
        try:
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            with wave.open(temp_wav.name, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16)) # Re-initialize PyAudio just for size info, safe here
                wf.setframerate(samplerate)
                wf.writeframes(b''.join(frames))

            logger.info(f"Audio recorded and saved successfully: {temp_wav.name} ({len(frames)} frames)")
            return temp_wav.name
        except Exception as e:
             logger.error(f"Error saving temporary WAV file: {str(e)}")
             # Clean up temp file if created but saving failed
             if temp_wav and os.path.exists(temp_wav.name):
                  os.unlink(temp_wav.name)
             return None

    except Exception as e:
        logger.error("Error initializing or during recording setup: %s", str(e))
        # Ensure resources are closed even if setup fails early
        if stream and stream.is_active():
             stream.stop_stream()
        if stream:
             stream.close()
        if p:
             p.terminate()
        # Clean up temp file if created during setup but failed
        if temp_wav and os.path.exists(temp_wav.name):
             os.unlink(temp_wav.name)
        return None

def transcribe_audio(file_path):
    """
    Transcribes the recorded audio file using Groq's Whisper model.
    
    Parameters:
      - file_path: The path to the audio file to transcribe.
    
    Returns:
      The transcribed text, or None if an error occurs.
    """
    logger.info("Starting audio transcription for file: %s", file_path)
    try:
        # Log file size before opening
        file_size = os.path.getsize(file_path)
        logger.info(f"Audio file size: {file_size} bytes")

        with open(file_path, "rb") as file:
            logger.info("Sending audio file to Groq Whisper for transcription.")
            # Create a transcription using Groq's Whisper model
            transcription = groq_client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo",  # Using the fastest multilingual model
                response_format="text",  # Get just the text output
                language="en",  # Optional: specify language for better accuracy
                temperature=0.0  # Keep it deterministic
            )
            
            # The response is already a string when using response_format="text"
            logger.info("Groq transcription successful. Result: '%s'", transcription)
            return transcription

    except Exception as e:
        logger.error("Groq Transcription Error: %s", str(e))
        return None
    finally:
        # Clean up the temporary audio file after transcription
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary audio file after transcription: {file_path}")
            except PermissionError:
                 logger.warning(f"Could not unlink temporary audio file {file_path} immediately after transcription due to PermissionError. It might be cleaned up later.")
            except Exception as e:
                 logger.error(f"Error unlinking temporary audio file {file_path} after transcription: {str(e)}")

def listen():
    """
    Records audio from the microphone and returns the transcribed text.
    
    Returns:
      The transcribed text as a string, or an empty string on failure.
    """
    logger.info("Starting listen function")
    audio_file_path = None
    try:
        logger.info("Calling record_audio()")
        audio_file_path = record_audio()
        
        if not audio_file_path:
            logger.warning("record_audio() returned None")
            return "" # Return empty string if recording failed or no speech detected
            
        logger.info("Calling transcribe_audio() with file: %s", audio_file_path)
        transcript = transcribe_audio(audio_file_path)
        
        # transcribe_audio already cleans up the file

        if not transcript:
            logger.warning("transcribe_audio() returned None or empty string")
            return "" # Return empty string if transcription failed
            
        logger.info("Listen function completed successfully with transcript")
        return transcript.strip() # Return stripped transcript
        
    except Exception as e:
        logger.error("Error in listen function: %s", str(e))
        # Ensure temp file is cleaned up if listen failed before transcribe_audio was called
        if audio_file_path and os.path.exists(audio_file_path):
             try:
                os.unlink(audio_file_path)
                logger.info(f"Cleaned up temporary audio file in listen() exception: {audio_file_path}")
             except PermissionError:
                  logger.warning(f"Could not unlink temporary audio file {audio_file_path} in listen() exception immediately due to PermissionError.")
             except Exception as e:
                  logger.error(f"Error unlinking temporary audio file {audio_file_path} in listen() exception: {str(e)}")
        return ""


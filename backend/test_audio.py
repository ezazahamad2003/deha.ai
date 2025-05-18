from audio import speak, listen
import time

def main():
    # Welcome message
    speak("Hello! I'm Deha AI. How can I help you today?")
    
    while True:
        # Listen for user input
        user_input = listen()
        
        if user_input:
            # Echo back what was heard
            response = f"I heard you say: {user_input}"
            speak(response)
            
            # Check for exit command
            if "exit" in user_input.lower() or "quit" in user_input.lower():
                speak("Goodbye!")
                break
        
        time.sleep(0.5)  # Small delay between interactions

if __name__ == "__main__":
    main() 
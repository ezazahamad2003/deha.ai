# Deha AI

A medical record analysis and management application that allows users to upload their medical records, chat with an AI assistant, and view calendar events and reminders.

## Features

- **PDF Upload**: Upload your medical records in PDF format.
- **Chat Interface**: Discuss your medical records with an AI assistant.
- **Calendar View**: View upcoming events and reminders extracted from your medical records.
- **Voice Call**: Start a voice call with the AI assistant to discuss your medical records.

## Prerequisites

- Node.js (v14 or higher)
- Python (v3.8 or higher)
- npm (v6 or higher)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Deha AI
   ```

2. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd ../frontend
   npm install
   ```

## Running the Application

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Start the Flask server:
   ```bash
   python main.py
   ```

   The backend server will run on `http://localhost:5000`.

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Start the React development server:
   ```bash
   npm start
   ```

   The frontend application will run on `http://localhost:3000`.

## Usage

1. Open your browser and go to `http://localhost:3000`.
2. Upload your medical record in PDF format.
3. Use the chat interface to discuss your medical records with the AI assistant.
4. View your calendar events and reminders in the Calendar view.

## Notes

- The chat interface is currently limited to voice calls. A text chat interface will be added in future updates.
- The calendar events are currently sample data. Real event extraction from PDFs will be implemented in future updates.

## License

This project is licensed under the MIT License.
# Deha AI - Medical Record Assistant

Deha AI is an intelligent desktop application designed to help users understand their medical records by providing clear, empathetic, and personalized responses to their health-related questions.

## Features

- 📄 PDF Medical Record Analysis
- 💬 Natural Language Interaction
- 🏥 Medical Term Explanation
- 🤝 Empathetic and Supportive Responses
- 🔒 Secure and Private

## Prerequisites

- Python 3.8 or higher
- Groq API key
- PyPDF2 library

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ezazahamad2003/deha-ai.git
cd deha-ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your Groq API key:
```
GROQ_API_KEY=your_api_key_here
```

## Usage

1. Place your medical record PDF in the project directory
2. Run the application:
```bash
cd backend
python main.py path/to/your/medical_record.pdf
```

3. Start chatting with Deha AI about your medical record
4. Type 'exit' to end the conversation

## Project Structure

```
deha-ai/
├── backend/
│   ├── main.py           # Main application logic
│   └── pdf_loader.py     # PDF processing utilities
├── .env                  # Environment variables (not tracked by git)
├── .gitignore           # Git ignore rules
├── requirements.txt     # Project dependencies
└── README.md           # This file
```

## Security

- API keys and sensitive data are stored in `.env` file
- `.env` file is not tracked by git
- Medical records are processed locally

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Your Name - [@your_twitter](https://x.com/Zaz_Labs)

Project Link: [https://github.com/ezazahamad2003/deha-ai](https://github.com/ezazahamad2003/deha-ai)

## Backend Development Scope (Hackathon)

This section outlines the technical details for the backend implementation.

### 1. Absolute MVP (3 REST endpoints + 1 background worker)

| Endpoint         | Purpose                                      | Notes                                                              |
|------------------|----------------------------------------------|--------------------------------------------------------------------|
| `POST /upload`   | Accept 1 × PDF/PNG (multipart/form-data)   | Saves file to `/data/{patient_uuid}/raw/` and queues job ID        |
| `POST /query`    | `{patient_id, question}` → `answer` JSON     | Does RAG retrieval + Groq R1 call                                  |
| `GET /healthz`   | Liveness/DB ping                             | For Docker/CI                                                      |

**Background worker** (FastAPI BackgroundTasks or Celery):
1. Load file → Gemini Vision OCR/structure
2. Chunk → 512-token windows
3. Call Groq Embed 4k-512
4. Upsert to Qdrant (collection = `patient_id`)

### 2. Minimal Tech Stack

*   FastAPI `0.111`
*   qdrant-client `1.x`
*   google-generativeai `0.5`
*   groq `0.4`
*   pypdf, pdfplumber (for page-level PDF extraction fallback)
*   python-multipart (for file uploads)
*   Docker / docker-compose

All async, single container except Qdrant.

### 3. Directory Layout

```
deha-backend/
 ├ app/
 │   ├ main.py          # FastAPI init, routers
 │   ├ routers/
 │   │   ├ upload.py
 │   │   └ query.py
 │   ├ etl/
 │   │   └ ingest.py    # OCR → chunk → embed → upsert
 │   └ rag.py           # Retriever + answer builder
 ├ Dockerfile
 ├ docker-compose.yml   # api + qdrant
 └ requirements.txt
```

### 4. Prompt & Retrieval Strategy

**Retriever (Qdrant):**
```python
retriever = qdrant_client.scroll(
    collection_name=patient_id,
    query_vector=embedding, # This should be qdrant_client.search for vector similarity
    limit=6,
    score_threshold=0.15
)
```
*Note: For vector similarity search, `qdrant_client.search` is more appropriate than `scroll`.*

**Prompt (Groq):**
```python
prompt = f"""
You are Deha AI, a personal AI medical case manager.
Your purpose is to help users understand their medical records by providing clear, accurate answers to their questions.
Use the following medical record to answer patient questions.
Show your chain of thought in <think>…</think> tags, then give the final concise answer.

QUESTION: {question}

CONTEXT:
{snippets}
"""
groq.chat.completions.create(model="deepseek-r1-70b-chat",
                              messages=[{"role":"user","content":prompt}],
                              temperature=0.2, max_tokens=512)
```

### 5. Security Quick-Wins

*   Use `.env` files for secrets; never hard-code API keys.
*   Document local disk & Qdrant volume encryption (e.g., using `cryptsetup`) in this README.
*   Optional: JWT middleware (e.g., Auth0 test tenant) – can be <20 lines with FastAPI.

**Local Data Encryption (Conceptual for README):**
To encrypt the `/data` volume on the host machine (Linux example):
1.  **Install cryptsetup:** `sudo apt-get install cryptsetup`
2.  **Create a file to be used as a block device:** `sudo dd if=/dev/zero of=/path/to/encrypted_data.img bs=1M count=1024` (e.g., 1GB)
3.  **Format with LUKS:** `sudo cryptsetup luksFormat /path/to/encrypted_data.img` (Set a strong passphrase)
4.  **Open the LUKS container:** `sudo cryptsetup luksOpen /path/to/encrypted_data.img deha_data_volume`
5.  **Create a filesystem:** `sudo mkfs.ext4 /dev/mapper/deha_data_volume`
6.  **Mount:** `sudo mkdir /mnt/deha_data` and `sudo mount /dev/mapper/deha_data_volume /mnt/deha_data`
7.  Update `docker-compose.yml` to mount `/mnt/deha_data` to `/data` in the `api` service and the Qdrant storage path to a directory within `/mnt/deha_data`.
8.  **To unmount and close:** `sudo umount /mnt/deha_data` then `sudo cryptsetup luksClose deha_data_volume`.
    *This setup needs to be done manually on the host. For Qdrant's own storage, it persists to a Docker volume (`qdrant_storage`), which can also be pointed to an encrypted partition on the host.*

### 6. How to Run (Development)

1.  **Create `.env` file:** In the `deha-backend/` directory, create a `.env` file with your API keys:
    ```env
    GEMINI_API_KEY=your_gemini_api_key_here
    GROQ_API_KEY=your_groq_api_key_here
    # QDRANT_API_KEY=your_qdrant_api_key_if_any
    # JWT_SECRET_KEY=a_very_strong_secret_key_for_jwt
    # AUTH0_DOMAIN=your-auth0-domain.auth0.com
    # AUTH0_AUDIENCE=your_auth0_api_audience
    ```
2.  **Build and run containers:**
    ```bash
    cd deha-backend
    docker compose up --build -d
    ```
3.  **Test endpoints:**
    *   **Upload:**
        ```bash
        # Create a dummy PDF or PNG file, e.g., /tmp/report.pdf
        curl -F "file=@/tmp/report.pdf" \
             -F "patient_id=abc123" \
             http://localhost:8000/upload
        ```
    *   **Query:**
        ```bash
        curl -X POST http://localhost:8000/query \
             -H "Content-Type: application/json" \
             -d '{"patient_id":"abc123","question":"What medications am I on?"}'
        ```
    *   **Health Check:**
        ```bash
        curl http://localhost:8000/healthz
        ```

### 7. Stretch Goals (If Time Permits)

*   Add Deepgram STT/TTS WebSocket proxy (`/voice` endpoint).
*   Switch background tasks from FastAPI `BackgroundTasks` to Celery-Redis for retries and better scalability.
*   Stream Groq responses (`text/event-stream`) for a more interactive demo.

---
*This project scope is designed for a hackathon setting (24-48 hours).*
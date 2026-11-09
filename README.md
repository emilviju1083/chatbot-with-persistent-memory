# Chatbot with Persistent Memory

## Project Overview
This project is an AI chatbot that can maintain conversation history using a PostgreSQL database. Users can start conversations, continue previous conversations, and summarize their chats.

## Features
- Chatbot with a command-line interface (CLI).
- Persistent conversation history stored in PostgreSQL.
- Resume conversations using conversation IDs.
- Supports Ollama and Google Gemini as LLM providers.
- Configurable system prompt.
- Streaming chatbot responses.
- Conversation summarization with validated JSON output.
- Logs token usage for each assistant message.
- FastAPI backend with interactive API documentation.

## Technologies Used
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Ollama
- Google Gemini API
- Requests

## Project Structure
```text
chatbot/
├── app/
│   ├── routers/
│   ├── services/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── cli.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup Instructions

### 1. Clone the repository
```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd chatbot
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file using `.env.example` as a template.

Add your PostgreSQL connection details and LLM configuration.

### 5. Start PostgreSQL
Make sure your PostgreSQL server is running and the project database exists.

### 6. Start the FastAPI server
```bash
uvicorn app.main:app --reload
```

Open the API documentation at:
`http://127.0.0.1:8000/docs`

### 7. Run the CLI
Open a second terminal and run:
```bash
python -m app.cli
```

## Usage
- Enter a message in the CLI to chat with the assistant.
- Continue chatting in the same session to retain conversation context.
- Type `exit` to close the CLI.
- Use the API endpoints to retrieve conversations and generate summaries.

## Security
API keys and database credentials must be stored in `.env`. Never commit `.env` or other secret files to GitHub.

## Author
Emil Viju
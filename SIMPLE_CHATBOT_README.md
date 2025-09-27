# Simple Chatbot

A clean, dark-mode chatbot application with AI model switching and RAG (Retrieval-Augmented Generation) capabilities.

## Features

- 🌙 **Dark Mode Interface**: Clean, modern dark theme
- ⚡ **Model Switching**: Toggle between fast (Groq) and premium (OpenAI) models
- 📄 **Document Upload**: Upload PDFs, text files, and markdown for RAG
- 🔍 **Vector Search**: Find relevant context from uploaded documents
- 💬 **Chat History**: Persistent chat history during session
- 📊 **Real-time Stats**: Monitor document processing and model status

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Copy the environment template:
```bash
cp .env.simple_chatbot .env
```

Edit `.env` and add your API keys:
- **Supabase**: Create a project at [supabase.com](https://supabase.com)
- **OpenAI**: Get API key from [platform.openai.com](https://platform.openai.com)
- **Groq**: Get API key from [console.groq.com](https://console.groq.com)

### 3. Set Up Database

Create the following table in your Supabase database:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create document_chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding VECTOR(384),  -- Adjust dimension based on your embedding model
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

### 4. Run the Application

```bash
streamlit run simple_app.py
```

## Core Files

- **`simple_app.py`**: Main Streamlit application
- **`models.py`**: AI model management (Groq + OpenAI)
- **`rag.py`**: Document processing and vector search
- **`database.py`**: Supabase database operations

## Usage

1. **Chat**: Type messages in the chat input
2. **Switch Models**: Use the sidebar toggle to switch between fast/premium models
3. **Upload Documents**: Upload files in the sidebar to enhance responses with your content
4. **Monitor Status**: Check connection status and document stats in the info panel

## Model Types

- **Fast (Groq)**: Mixtral-8x7B model for quick responses
- **Premium (OpenAI)**: GPT-3.5-turbo for higher quality responses

## Supported File Types

- PDF files (`.pdf`)
- Text files (`.txt`)
- Markdown files (`.md`)

## Troubleshooting

1. **API Key Issues**: Ensure all API keys are correctly set in `.env`
2. **Database Connection**: Verify Supabase URL and key are correct
3. **File Upload**: Check file format is supported and file size is reasonable
4. **Model Unavailable**: Check API key validity and account credits

## Architecture

The application follows a simple, modular architecture:

```
simple_app.py (UI) → models.py (AI) → rag.py (Documents) → database.py (Storage)
```

Each module handles a specific concern, making the codebase easy to understand and maintain.
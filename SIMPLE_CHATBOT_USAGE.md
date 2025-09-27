# Simple Chatbot Usage Guide

## Overview

The Simple Chatbot is a clean, dark-mode Streamlit application with AI model switching and RAG (Retrieval-Augmented Generation) capabilities.

## Features

### ✨ Core Features
- **Dark Mode Interface**: Clean, responsive dark theme
- **Model Switching**: Toggle between Fast (Groq Gemma2) and Premium (Groq GPT-OSS) models
- **Document Upload**: Upload PDF, TXT, or MD files for RAG functionality
- **Chat History**: Persistent conversation history during session
- **Real-time Responses**: Streaming AI responses with context

### 🎯 User Interface Components

#### Header
- Application title and description
- Connection status indicator (🟢 Connected / 🔴 Disconnected)

#### Sidebar Controls
- **AI Model Selection**: Radio buttons to switch between Fast and Premium models
- **Document Upload**: File uploader for RAG documents
- **Chat Controls**: Clear chat and test database connection buttons

#### Main Chat Area
- **Message History**: Displays user and assistant messages with model indicators
- **Message Input**: Chat input field at the bottom

## Getting Started

### 1. Prerequisites

Ensure you have the required environment variables set:

```bash
# Required for AI models
GROQ_API_KEY=your_groq_api_key_here

# Required for database (RAG functionality)
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Optional for OpenAI embeddings (fallback to sentence-transformers)
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Database Setup

Before using RAG functionality, set up your Supabase database:

1. Create a new Supabase project
2. Run the SQL from `simple_chatbot_schema.sql` in your Supabase SQL Editor
3. This creates the `document_chunks` table and vector search functions

### 3. Running the Application

```bash
# Start the simple chatbot
streamlit run simple_app.py

# Test the application components
python test_simple_app.py
```

## Usage Instructions

### Basic Chat
1. Open the application in your browser
2. Type your message in the chat input at the bottom
3. Press Enter or click Send to get an AI response
4. Messages appear in the chat history with user (👤) and assistant (⚡/💎) indicators

### Model Switching
1. Use the sidebar radio buttons to switch between models:
   - **⚡ Fast Model**: Groq Gemma2 (faster, cost-effective)
   - **💎 Premium Model**: Groq GPT-OSS (higher quality)
2. The current model is displayed below the selection
3. Model changes take effect immediately for new messages

### Document Upload (RAG)
1. Click "Choose files" in the Document Upload section
2. Select PDF, TXT, or MD files (multiple files supported)
3. Click "Process Documents" to upload and process
4. Processing status shows in the sidebar
5. Uploaded documents enhance AI responses with relevant context

### Chat Management
- **Clear Chat**: Removes all messages from current session
- **Test Database**: Verifies database connection for RAG functionality

## Model Information

### Fast Model (Groq Gemma2)
- **Use Case**: Quick responses, general questions
- **Speed**: Very fast
- **Cost**: Lower cost per request
- **Quality**: Good for most use cases

### Premium Model (Groq GPT-OSS)
- **Use Case**: Complex questions, detailed analysis
- **Speed**: Moderate
- **Cost**: Higher cost per request  
- **Quality**: Superior reasoning and context understanding

## RAG (Document Context)

When you upload documents:
1. Documents are split into chunks
2. Embeddings are generated for each chunk
3. Relevant chunks are retrieved based on your questions
4. AI responses include context from your documents

### Supported File Types
- **PDF**: Text extraction from PDF documents
- **TXT**: Plain text files
- **MD**: Markdown files

## Troubleshooting

### Common Issues

#### "Model not available" Error
- Check that `GROQ_API_KEY` is set correctly
- Verify your Groq API key is valid and has credits

#### "Database connection failed" Error
- Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set
- Verify your Supabase project is active
- Run the database schema setup if not done

#### Document Upload Fails
- Ensure database is properly configured
- Check file format is supported (PDF, TXT, MD)
- Verify file is not corrupted

#### No Context in Responses
- Upload and process documents first
- Ask questions related to your uploaded content
- Check that document processing completed successfully

### Getting Help

1. **Test Components**: Run `python test_simple_app.py` to verify setup
2. **Check Logs**: Look at Streamlit terminal output for error details
3. **Database Test**: Use the "Test Database" button in the sidebar
4. **Model Status**: Check model availability indicators in the sidebar

## Technical Details

### Architecture
- **Frontend**: Streamlit with custom dark mode CSS
- **AI Models**: Groq API (Gemma2 and GPT-OSS)
- **Database**: Supabase with pgvector for embeddings
- **Document Processing**: LangChain for text splitting and processing
- **Embeddings**: OpenAI embeddings (primary) or SentenceTransformers (fallback)

### File Structure
- `simple_app.py`: Main Streamlit application
- `models.py`: AI model management and integration
- `rag.py`: Document processing and retrieval system
- `database.py`: Supabase database operations
- `simple_chatbot_schema.sql`: Database schema setup
- `test_simple_app.py`: Application testing script

### Session Management
- Messages stored in Streamlit session state (not persistent)
- Model preferences maintained during session
- Document uploads persist in database across sessions
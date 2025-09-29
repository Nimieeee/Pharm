# PharmGPT - AI-Powered Pharmacology Assistant

A sophisticated Streamlit-based chatbot application designed for pharmaceutical and medical queries, featuring RAG (Retrieval-Augmented Generation) capabilities, multi-conversation support, and specialized pharmacology expertise.

## ✨ Features

- **⚕️ Pharmacology Expertise**: Specialized system prompts for pharmaceutical and medical queries
- **📚 RAG System**: Upload and query PDF, DOCX, TXT, and MD documents with vector search
- **💬 Multi-Conversation**: Manage multiple chat sessions with separate knowledge bases
- **🌙 Modern UI**: Dark mode interface with responsive design and accessibility features
- **🗄️ Persistent Storage**: Supabase backend for conversations, messages, and document chunks
- **🔍 Vector Search**: Semantic document search using sentence transformers
- **📱 Responsive Design**: Works seamlessly across mobile, tablet, and desktop

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Supabase account (for database)
- Any LLM API key (for primary AI model)


### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nimieeee/phhh.git
   cd phhh
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Configure Streamlit secrets**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit with your credentials
   ```

5. **Set up the database**
   - Go to your Supabase Dashboard
   - Navigate to SQL Editor
   - Run the complete schema from `simple_chatbot_schema.sql`

6. **Run the application**
   ```bash
   # Full-featured app with multi-conversation support
   streamlit run simple_app.py
   
   # Or minimal streaming interface
   streamlit run minimal_app.py
   ```

## 📋 Configuration

### Environment Variables (.env)

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# AI Model APIs
MISTRAL_API_KEY=your_mistral_api_key
GROQ_API_KEY=your_groq_api_key  # Optional for fast model
```

### Streamlit Secrets (.streamlit/secrets.toml)

```toml
SUPABASE_URL = "your_supabase_project_url"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
MISTRAL_API_KEY = "your_mistral_api_key"
GROQ_API_KEY = "your_groq_api_key"
```

## 🗄️ Database Schema

The application uses Supabase with the following tables:

- **`conversations`**: Multi-conversation management
- **`messages`**: Chat history with metadata
- **`document_chunks`**: RAG document storage with vector embeddings

Key features:
- Vector similarity search using pgvector extension
- Conversation-scoped document knowledge bases
- Message metadata for enhanced context

## 🤖 AI Models & Capabilities

### Primary Model: Mistral Medium
- **Purpose**: Detailed pharmacology responses
- **Specialization**: Drug interactions, mechanisms, clinical applications
- **System Prompt**: Specialized for pharmaceutical expertise


### RAG System
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Chunking**: Recursive text splitting with overlap
- **Search**: Vector similarity with configurable thresholds
- **Formats**: PDF, DOCX, TXT, MD support

## 📱 Application Variants

### 1. Full Application (`simple_app.py`)
- Multi-conversation management
- Document upload and RAG
- Model switching
- Persistent chat history
- Advanced error handling

### 2. Minimal Interface (`minimal_app.py`)
- Streamlined chat interface
- Fast streaming responses
- Single conversation mode
- Lightweight and responsive

### 3. Database Setup (`setup_database.py`)
- Schema validation
- Migration assistance
- Development utilities

## 🔧 Project Structure

```
├── simple_app.py              # Main application with full features
├── minimal_app.py             # Minimal streaming interface
├── models.py                  # AI model management (Mistral/Groq)
├── rag.py                     # RAG system with document processing
├── database.py                # Supabase database operations
├── conversation_manager.py    # Multi-conversation support
├── prompts.py                 # Specialized system prompts
├── setup_database.py          # Database setup utilities
├── simple_chatbot_schema.sql  # Complete database schema
├── requirements.txt           # Python dependencies
└── .streamlit/
    └── secrets.toml.example   # Configuration template
```

## 🚀 Deployment Options

### Streamlit Cloud
1. Fork this repository
2. Connect to Streamlit Cloud
3. Add secrets in dashboard
4. Deploy automatically

### Local Development
```bash
pip install -r requirements.txt
cp .env.example .env
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run simple_app.py
```

### Docker (Optional)
```bash
docker build -t pharmgpt .
docker run -p 8501:8501 --env-file .env pharmgpt
```

## 🎯 Use Cases

### Pharmaceutical Research
- Drug interaction analysis
- Mechanism of action explanations
- Clinical trial information
- Regulatory guidance

### Medical Education
- Pharmacokinetics and pharmacodynamics
- Therapeutic classifications
- Adverse effect profiles
- Dosing guidelines

### Document Analysis
- Research paper analysis
- Clinical protocol review
- Regulatory document processing
- Literature synthesis

## 🛠️ Advanced Features

### Error Handling
- Graceful API failure recovery
- Database connection fallbacks
- User-friendly error messages
- Comprehensive logging

### Performance Optimization
- Parallel document processing
- Efficient vector search
- Streaming responses
- Caching strategies

### Security & Privacy
- Input sanitization
- XSS protection
- Secure API key management
- Data encryption at rest

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Troubleshooting

### Common Issues
- **API Key Errors**: Verify keys in `.env` and `secrets.toml`
- **Database Connection**: Check Supabase URL and credentials
- **Import Errors**: Ensure all dependencies are installed
- **Schema Issues**: Run the complete SQL schema in Supabase

### Getting Help
1. Check error messages for specific guidance
2. Verify environment configuration
3. Review database schema setup
4. Test with minimal app first

## 🎯 Roadmap

- [ ] User authentication and profiles
- [ ] Advanced document management
- [ ] API endpoint for external integration
- [ ] Multi-language support
- [ ] Voice input/output capabilities
- [ ] Advanced analytics and insights

---

**Built with ❤️ for the pharmaceutical and medical community**

*Powered by Streamlit, Supabase, Mistral AI, and modern ML technologies*

# PharmGPT - AI-Powered Pharmacology Assistant

A modern web application designed for pharmaceutical and medical queries, featuring RAG (Retrieval-Augmented Generation) capabilities, user authentication, multi-conversation support, and specialized pharmacology expertise.

## 🚀 Modern Web Application

Complete web application with:
- **React Frontend** (deployed on Netlify)
- **FastAPI Backend** (deployed on Render) 
- **User Authentication** with JWT tokens
- **Admin Panel** for system management
- **Support System** for user assistance
- **Secure Deployment** configuration

## ✨ Features

- **⚕️ Pharmacology Expertise**: Specialized system prompts for pharmaceutical and medical queries
- **📚 RAG System**: LangChain + Supabase pgvector for optimized document processing and search
- **💬 Multi-Conversation**: Manage multiple chat sessions with separate knowledge bases
- **🌙 Modern UI**: Dark mode interface with responsive design and accessibility features
- **🗄️ Persistent Storage**: Supabase backend for conversations, messages, and document chunks
- **🔍 Vector Search**: HNSW-indexed semantic search with HuggingFace embeddings
- **📱 Responsive Design**: Works seamlessly across mobile, tablet, and desktop

## 🚀 Quick Start

### Web Application (Recommended)

The new web application provides a modern, secure, and scalable solution:

1. **Frontend (React + Netlify)**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Backend (FastAPI + Render)**
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

3. **Database Setup**
   - Create a Supabase project
   - Run migrations from `backend/migrations/`
   - Configure environment variables

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

### Demo Credentials

For testing the deployed application:
- **Admin**: admin@pharmgpt.com / admin123
- **User**: Register a new account to test user features

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
- **Framework**: LangChain with Supabase pgvector integration
- **Embeddings**: HuggingFace all-MiniLM-L6-v2 (384 dimensions)
- **Indexing**: HNSW + IVFFlat for optimized similarity search
- **Chunking**: Recursive text splitting with overlap
- **Search**: Vector similarity with user isolation and metadata filtering
- **Formats**: PDF, DOCX, TXT, MD, PPTX support

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
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/            # Page components
│   │   ├── contexts/         # React contexts (Auth, etc.)
│   │   └── lib/              # Utilities and API client
│   ├── package.json
│   └── netlify.toml          # Netlify deployment config
├── backend/                   # FastAPI backend application
│   ├── app/
│   │   ├── api/v1/endpoints/ # API endpoints
│   │   ├── core/             # Core configuration
│   │   ├── models/           # Pydantic models
│   │   └── services/         # Business logic services
│   ├── migrations/           # Database migrations
│   ├── main.py              # FastAPI application entry point
│   ├── requirements.txt     # Python dependencies
│   └── render.yaml          # Render deployment config
├── .kiro/specs/             # Development specifications
├── DEPLOYMENT.md            # Deployment guide
├── PharmGPT.png            # Application logo
└── README.md               # This file
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

### Completed ✅
- [x] User authentication and profiles
- [x] Modern web application architecture
- [x] API endpoints for external integration
- [x] Admin panel for system management
- [x] Support system for user assistance
- [x] Secure deployment configuration

### In Progress 🚧
- [ ] Complete chat interface implementation
- [ ] Advanced document management features
- [ ] Real-time notifications
- [ ] Enhanced admin analytics

### Planned 📋
- [ ] Multi-language support
- [ ] Voice input/output capabilities
- [ ] Mobile application
- [ ] Advanced AI model integration
- [ ] Enterprise features

---

**Built with ❤️ for the pharmaceutical and medical community**

*Powered by Streamlit, Supabase, Mistral AI, and modern ML technologies*

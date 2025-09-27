# 💬 Simple Chatbot

A clean, modern Streamlit chatbot application with dark mode styling, model switching, and RAG (Retrieval-Augmented Generation) functionality.

## ✨ Features

- **🌙 Dark Mode UI**: Consistent dark theme with enhanced accessibility
- **🧠 Mistral AI Integration**: Powered by Mistral Small for detailed, elaborate responses
- **📚 Document Upload**: Upload PDF, DOCX, TXT, and MD files for RAG functionality
- **🔍 Smart Search**: Vector-based document search with context-aware responses
- **📝 Custom System Prompts**: Personalize the AI assistant's behavior and expertise
- **⚕️ Pharmacology Focus**: Specialized for pharmaceutical and medical queries
- **📱 Responsive Design**: Works seamlessly on mobile, tablet, and desktop
- **🛡️ Error Handling**: Comprehensive error handling with user-friendly messages
- **♿ Accessibility**: WCAG 2.1 compliant with focus indicators and high contrast

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Supabase account (for database)
- Mistral AI API key (for AI responses)

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
   # Edit .env with your credentials
   ```

4. **Configure Streamlit secrets**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit .streamlit/secrets.toml with your credentials
   ```

5. **Set up the database**
   - Go to your Supabase Dashboard
   - Navigate to SQL Editor
   - Run the SQL from `simple_chatbot_schema.sql`

6. **Run the application**
   ```bash
   streamlit run simple_app.py
   ```

## 📋 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
GROQ_API_KEY=your_groq_api_key
```

### Streamlit Secrets

Create `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "your_supabase_url"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
GROQ_API_KEY = "your_groq_api_key"
```

## 🗄️ Database Setup

The application uses Supabase as the database backend. Run the SQL schema from `simple_chatbot_schema.sql` in your Supabase SQL Editor to set up the required tables:

- `document_chunks`: Stores processed document chunks with embeddings
- Vector similarity search functions for RAG functionality

See `SIMPLE_CHATBOT_DATABASE_SETUP.md` for detailed setup instructions.

## 🎨 UI Features

### Dark Mode Styling
- Consistent dark theme across all components
- Enhanced contrast ratios for accessibility
- Smooth animations and hover effects
- CSS custom properties for easy theming

### Responsive Design
- **Mobile (≤480px)**: Single column layout, larger touch targets
- **Tablet (≤768px)**: Responsive columns, touch-friendly interface  
- **Desktop (>768px)**: Full sidebar, multi-column layouts
- **Large Desktop (≥1024px)**: Maximum content density

### Accessibility
- WCAG 2.1 AA compliance
- Focus indicators for keyboard navigation
- High contrast mode support
- Reduced motion preferences
- Screen reader compatibility

## 🤖 AI Models

### Fast Model (Default)
- **Model**: Groq Gemma2-9B-IT
- **Speed**: Very fast responses
- **Use Case**: General questions, quick interactions

### Premium Model
- **Model**: Groq GPT-OSS-20B
- **Quality**: Higher quality responses
- **Use Case**: Complex questions, detailed analysis

## 📚 Document Processing

### Supported Formats
- PDF (.pdf)
- Word Documents (.docx)
- Text Files (.txt)
- Markdown (.md)

### Features
- Automatic text extraction
- Intelligent chunking with overlap
- Vector embeddings for similarity search
- Real-time processing status
- Comprehensive error handling

## 🛠️ Error Handling

The application includes comprehensive error handling for:

- **API Errors**: Authentication, rate limits, network issues
- **Document Processing**: File validation, format issues, corruption
- **Database Errors**: Connection issues, schema problems
- **System Errors**: Initialization failures, critical errors

Each error provides:
- Clear, user-friendly messages
- Actionable recovery options
- Fallback strategies
- Detailed troubleshooting guidance

## 📱 Usage

1. **Start Chatting**: Type your question in the chat input
2. **Upload Documents**: Use the sidebar to upload files for RAG
3. **Switch Models**: Toggle between Fast and Premium models
4. **View Status**: Monitor connection and document processing status
5. **Export Chat**: Download your conversation history

## 🔧 Development

### Project Structure
```
├── simple_app.py              # Main Streamlit application
├── models.py                  # AI model management
├── rag.py                     # RAG system implementation
├── database.py                # Database operations
├── simple_chatbot_schema.sql  # Database schema
├── requirements.txt           # Python dependencies
└── .streamlit/
    └── secrets.toml.example   # Configuration template
```

### Key Components

- **`simple_app.py`**: Main application with UI and error handling
- **`models.py`**: Model management and API integration
- **`rag.py`**: Document processing and vector search
- **`database.py`**: Supabase database operations

## 🚀 Deployment

### Streamlit Cloud

1. Fork this repository
2. Connect to Streamlit Cloud
3. Add secrets in the Streamlit Cloud dashboard
4. Deploy automatically

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Run the app
streamlit run simple_app.py
```

## 📖 Documentation

- **[Usage Guide](SIMPLE_CHATBOT_USAGE.md)**: Detailed usage instructions
- **[Database Setup](SIMPLE_CHATBOT_DATABASE_SETUP.md)**: Database configuration guide
- **[Task Summary](task8_ui_error_handling_summary.md)**: Implementation details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

If you encounter any issues:

1. Check the error messages for guidance
2. Review the documentation files
3. Ensure all environment variables are set correctly
4. Verify your Supabase database schema is up to date

## 🎯 Features Roadmap

- [ ] User authentication
- [ ] Conversation history
- [ ] File management interface
- [ ] Advanced model configuration
- [ ] Multi-language support
- [ ] Voice input/output

---

**Built with ❤️ using Streamlit, Supabase, and Groq**
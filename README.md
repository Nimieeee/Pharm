# PharmGPT - AI-Powered Pharmacology Assistant

A modern AI pharmacology assistant featuring deep research capabilities, document analysis, lab report generation, and specialized pharmaceutical expertise.

## 🌐 Live Application

- **Frontend**: [pharmgpt.app](https://pharmgpt.app) (Vercel)
- **Backend**: Private VPS (deployed separately)

## ✨ Features

### Core Capabilities
- **💬 AI Chat**: Intelligent pharmacology assistant with multiple modes (Fast, Detailed, Deep Research)
- **📚 Document RAG**: Upload PDFs, images, and documents for context-aware responses
- **🔬 Lab Report Generation**: Generate structured laboratory reports from data
- **🔍 Deep Research**: Comprehensive multi-source research with citations
- **🖼️ Image Analysis**: Pixtral-powered vision analysis for uploaded images
- **📊 Data Workbench**: Analyze and visualize data with AI assistance

### Technical Features
- **User Authentication**: JWT-based secure authentication
- **Multi-Conversation**: Manage multiple chat sessions with separate knowledge bases
- **Vector Search**: HNSW-indexed semantic search with Mistral embeddings
- **Real-time Streaming**: Server-Sent Events for streaming responses
- **Mobile Responsive**: Full mobile and tablet support

## 🚀 Frontend Development

This repository contains the **Next.js frontend** only.

### Prerequisites
- Node.js 18+
- npm or yarn

### Local Development

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`

### Environment Variables

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

### Deployment

The frontend is deployed to **Vercel**:
1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to `master`

## 📱 Application Modes

| Mode | Description | Model |
|------|-------------|-------|
| **Fast** | Quick responses for simple queries | Mistral Small |
| **Detailed** | Comprehensive, in-depth answers | Mistral Large |
| **Deep Research** | Multi-source research with citations | Mistral Large + Web Search |
| **Lab Report** | Structured laboratory reports | Mistral Large |

## 🔧 Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # Reusable UI components
│   │   ├── chat/        # Chat interface components
│   │   ├── ui/          # Common UI components
│   │   └── workbench/   # Data workbench components
│   ├── contexts/        # React contexts (Auth, Chat)
│   ├── hooks/           # Custom React hooks
│   └── lib/             # Utilities and API client
├── public/              # Static assets
├── package.json
└── next.config.js
```

## 🎨 UI Features

- **Dark Mode**: Elegant dark theme optimized for readability
- **Glassmorphism**: Modern glass-effect design elements
- **Smooth Animations**: Framer Motion powered transitions
- **Responsive Design**: Mobile-first approach
- **Accessibility**: ARIA labels and keyboard navigation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary. All rights reserved.

---

**Built with ❤️ for the pharmacology and medical community**

*Powered by Next.js, Vercel, and Mistral AI*

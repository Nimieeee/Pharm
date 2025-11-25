# PharmGPT Next.js - OpenAI & ChatGPT-Inspired Design

A modern Next.js implementation of PharmGPT with OpenAI-inspired homepage and ChatGPT-inspired chat interface.

## Architecture Overview

### Core Features

**Homepage (OpenAI-inspired)**:
- **Dark Theme**: High-contrast design with custom color palette
- **Responsive Navigation**: Collapsible sidebar + top navbar
- **Hero Section**: Interactive chat input with sample prompts
- **Content Grid**: Card-based layout for research, news, and stories
- **Floating Chat Input**: Sticky bottom input for quick access

**Chat Interface (ChatGPT-inspired)**:
- **Collapsible Sidebar**: Chat history and navigation
- **Clean Message Layout**: User/Assistant differentiation with avatars
- **Auto-expanding Input**: Grows with content, max 200px
- **File Attachments**: Support for document uploads
- **Voice Input**: Microphone button for voice queries
- **Model Selector**: Switch between different AI models
- **Real-time Responses**: Streaming support with loading states

### Tech Stack
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **Language**: TypeScript

### Component Structure

```
src/
├── app/
│   ├── layout.tsx          # Root layout with Navbar, Sidebar, Footer
│   ├── page.tsx            # Home page with Hero + Content Grids
│   ├── chat/
│   │   ├── page.tsx        # Chat page orchestrator
│   │   └── layout.tsx      # Chat-specific layout (no navbar/footer)
│   └── globals.css         # Global styles
├── components/
│   ├── Navbar.tsx          # Top navigation with search
│   ├── Sidebar.tsx         # Collapsible side navigation
│   ├── HeroSection.tsx     # Main hero with chat input
│   ├── ContentGrid.tsx     # Reusable content card grid
│   ├── FloatingChatInput.tsx # Sticky bottom chat input
│   ├── Footer.tsx          # Multi-column footer
│   └── chat/               # ChatGPT-inspired components
│       ├── ChatSidebar.tsx # Chat history sidebar
│       ├── ChatHeader.tsx  # Model selector header
│       ├── ChatMessages.tsx # Message display
│       └── ChatInput.tsx   # Auto-expanding input
```

### Routing Strategy
- **Static Routes**: `/`, `/research`, `/safety`, `/api`, `/about`
- **Dynamic Routes**: `/chat?q=query` for chat with initial query
- **API Routes**: Can be added in `app/api/` for server-side logic

### State Management
- **Client Components**: Using React hooks (useState, useEffect)
- **URL State**: Search params for chat queries
- **Future**: Can integrate Zustand or Redux for global state

### Styling Methodology
- **Utility-First**: Tailwind CSS for rapid development
- **Custom Theme**: Extended Tailwind config with brand colors
- **Animations**: CSS keyframes + Tailwind animate utilities
- **Responsive**: Mobile-first approach with breakpoints

### Interactive Behaviors
- **Search Toggle**: Expandable search bar in navbar
- **Sidebar Toggle**: Collapsible navigation with overlay
- **Chat Input**: Auto-focus, disabled states, loading indicators
- **Hover Effects**: Card scaling, color transitions, border highlights
- **Smooth Scrolling**: Auto-scroll to latest messages

## Getting Started

### Installation

```bash
cd nextjs-pharmgpt
npm install
```

### Environment Setup

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
npm run build
npm start
```

## Integration with Existing Backend

The chat interface connects to your Python backend:

```typescript
// In src/app/chat/page.tsx
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/ai/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: text,
    conversation_history: messages,
  }),
})
```

Ensure your backend has CORS enabled for the Next.js origin.

## Customization

### Colors
Edit `tailwind.config.ts`:
```typescript
colors: {
  accent: '#10a37f',  // Your brand color
  // ...
}
```

### Content
Update sample data in `src/app/page.tsx`:
- `featuredContent` - Featured research cards
- `latestNews` - News items

### Navigation
Modify menu items in `src/components/Sidebar.tsx` and `Navbar.tsx`

## Deployment

### Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

## Performance Optimizations
- Server Components by default (App Router)
- Image optimization with Next.js Image
- Code splitting and lazy loading
- Static generation where possible
- API route caching

## Accessibility
- Semantic HTML elements
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus states on all interactive elements
- Color contrast ratios meet WCAG AA

## Documentation

- **[CHATGPT_ARCHITECTURE.md](./CHATGPT_ARCHITECTURE.md)** - Detailed chat interface architecture
- **[README.md](./README.md)** - This file

## Future Enhancements

### Chat Interface
- [ ] Real-time streaming responses
- [ ] Document upload in chat
- [ ] Message regeneration
- [ ] Copy message content
- [ ] Export conversations
- [ ] Chat history persistence
- [ ] Conversation branching

### General
- [ ] User authentication
- [ ] Dark/light theme toggle
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Team workspaces
- [ ] Usage analytics

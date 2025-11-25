# ChatGPT-Inspired Chat Interface Architecture

## Overview
This document details the architecture of the ChatGPT-inspired chat interface built for PharmGPT.

## Architecture Analysis

### 1. Navigation Flow
- **Collapsible Sidebar**: Left sidebar that can be toggled open/closed
- **Persistent State**: Sidebar state maintained across sessions
- **Quick Actions**: Top of sidebar contains primary actions (New Chat, Search, Library)
- **Organized History**: Chat history grouped by time periods
- **Profile Section**: User profile and upgrade options at bottom

### 2. Component Structure

```
chat/
├── page.tsx                 # Main chat page orchestrator
├── layout.tsx              # Chat-specific layout (no navbar/footer)
└── components/
    ├── ChatSidebar.tsx     # Left navigation panel
    ├── ChatHeader.tsx      # Top bar with model selector
    ├── ChatMessages.tsx    # Message display area
    └── ChatInput.tsx       # Bottom input with attachments
```

### 3. Component Breakdown

#### ChatSidebar
**Purpose**: Navigation and chat history management

**Features**:
- Toggle open/closed
- New chat creation
- Search functionality
- Library access
- Projects section
- Chat history with hover actions
- User profile with upgrade CTA

**State Management**:
- `isOpen`: Boolean for sidebar visibility
- Chat history fetched from API/local storage

#### ChatHeader
**Purpose**: Top navigation and chat controls

**Features**:
- Model selector dropdown
- Group chat option
- Temporary chat toggle
- Minimal, clean design

**Interactions**:
- Model switching
- Chat mode changes

#### ChatMessages
**Purpose**: Display conversation history

**Features**:
- Auto-scroll to latest message
- User/Assistant message differentiation
- Avatar icons for each role
- Loading state with animation
- Empty state with welcome message

**Layout**:
- Max-width container (3xl)
- Centered content
- Alternating message alignment
- Smooth scrolling

#### ChatInput
**Purpose**: Message composition and submission

**Features**:
- Auto-expanding textarea
- File attachment button
- Voice input option
- Send button (disabled when empty)
- Keyboard shortcuts (Enter to send, Shift+Enter for newline)
- Character limit handling

**State**:
- Input value
- Loading state
- File attachments (future)

### 4. Routing Strategy

**Current Routes**:
- `/chat` - New chat session
- `/chat/[id]` - Existing chat (future)
- `/library` - Document library (future)

**URL State**:
- Query params for initial messages: `/chat?q=query`
- Chat ID in URL for persistence

### 5. State Management

**Local State** (React hooks):
- `messages`: Array of message objects
- `input`: Current input value
- `isLoading`: API call status
- `sidebarOpen`: Sidebar visibility

**Message Interface**:
```typescript
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}
```

**Future Enhancements**:
- Context API for global chat state
- Zustand for sidebar/UI preferences
- React Query for API caching

### 6. Styling Methodology

**Color Palette**:
- Background: `#212121` (darker gray)
- Card: `#2f2f2f` (medium gray)
- Border: `#3a3a3a` (subtle borders)
- Accent: `#10a37f` (teal green)
- Text: `#ffffff` (white)

**Design Principles**:
- Minimal borders
- Subtle hover states
- Smooth transitions (300ms)
- Rounded corners (lg, xl, 2xl, 3xl)
- Icon-first design
- Generous padding

**Responsive Design**:
- Sidebar collapses on mobile
- Messages stack vertically
- Input remains fixed at bottom
- Touch-friendly tap targets

### 7. Interactive Behaviors

#### Sidebar
- **Toggle**: Smooth slide animation (300ms)
- **Hover**: Background color change on items
- **Active**: Highlight current chat
- **Scroll**: Independent scroll for chat history

#### Messages
- **Auto-scroll**: Smooth scroll to new messages
- **Copy**: Click to copy message (future)
- **Regenerate**: Regenerate assistant response (future)

#### Input
- **Auto-expand**: Textarea grows with content (max 200px)
- **Enter**: Send message
- **Shift+Enter**: New line
- **Disabled**: When loading or empty
- **Focus**: Border color change

#### Header
- **Model Selector**: Dropdown menu
- **Icons**: Hover states with tooltips

### 8. Technical Patterns

#### Component Communication
```typescript
// Parent to Child (Props)
<ChatInput 
  value={input}
  onChange={setInput}
  onSend={handleSendMessage}
  isLoading={isLoading}
/>

// Child to Parent (Callbacks)
const handleSendMessage = (text: string) => {
  // Handle in parent
}
```

#### API Integration
```typescript
const response = await fetch('/api/v1/ai/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: text,
    conversation_history: messages,
  }),
})
```

#### Error Handling
- Try-catch blocks for API calls
- Error messages displayed as assistant responses
- Loading states prevent duplicate submissions

### 9. Performance Optimizations

**Implemented**:
- Auto-scroll only on new messages
- Textarea height calculation on change only
- Disabled buttons prevent duplicate API calls

**Future**:
- Virtual scrolling for long conversations
- Message pagination
- Lazy loading of chat history
- Debounced search
- Optimistic UI updates

### 10. Accessibility

**Current**:
- Semantic HTML elements
- ARIA labels on buttons
- Keyboard navigation support
- Focus states on interactive elements
- Alt text on icons

**Future**:
- Screen reader announcements for new messages
- Keyboard shortcuts documentation
- High contrast mode
- Font size controls

## Key Differences from OpenAI ChatGPT

1. **Branding**: PharmGPT colors and terminology
2. **Sidebar Content**: Pharmaceutical-focused projects and history
3. **Model Selector**: Single model vs. multiple options
4. **Features**: Simplified for MVP (no voice mode, canvas, etc.)
5. **API Integration**: Custom backend vs. OpenAI API

## Integration with Existing Backend

The chat interface connects to your Python FastAPI backend:

**Endpoint**: `POST /api/v1/ai/chat`

**Request**:
```json
{
  "message": "What are the side effects of aspirin?",
  "conversation_history": [
    {
      "role": "user",
      "content": "Previous message",
      "timestamp": "2025-11-25T10:00:00Z"
    }
  ]
}
```

**Response**:
```json
{
  "response": "Aspirin side effects include...",
  "sources": [...],
  "confidence": 0.95
}
```

## Future Enhancements

### Phase 1 (MVP+)
- [ ] Chat history persistence
- [ ] Document upload in chat
- [ ] Message regeneration
- [ ] Copy message content
- [ ] Export conversation

### Phase 2 (Advanced)
- [ ] Streaming responses
- [ ] Voice input/output
- [ ] Multi-modal support (images)
- [ ] Conversation branching
- [ ] Shared chats

### Phase 3 (Enterprise)
- [ ] Team workspaces
- [ ] Admin controls
- [ ] Usage analytics
- [ ] Custom models
- [ ] API access

## Development Commands

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## File Structure

```
nextjs-pharmgpt/
├── src/
│   ├── app/
│   │   ├── chat/
│   │   │   ├── page.tsx
│   │   │   └── layout.tsx
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   └── components/
│       ├── chat/
│       │   ├── ChatSidebar.tsx
│       │   ├── ChatHeader.tsx
│       │   ├── ChatMessages.tsx
│       │   └── ChatInput.tsx
│       ├── Navbar.tsx
│       ├── Sidebar.tsx
│       ├── Footer.tsx
│       ├── HeroSection.tsx
│       ├── ContentGrid.tsx
│       └── FloatingChatInput.tsx
├── public/
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

## Testing Checklist

- [ ] Sidebar toggle works smoothly
- [ ] Messages display correctly
- [ ] Input expands with content
- [ ] Send button enables/disables properly
- [ ] Loading state shows during API calls
- [ ] Error messages display correctly
- [ ] Keyboard shortcuts work (Enter, Shift+Enter)
- [ ] Responsive on mobile devices
- [ ] Sidebar collapses on mobile
- [ ] Chat history scrolls independently
- [ ] Auto-scroll to new messages works
- [ ] Empty state displays correctly

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Full support

## License

MIT

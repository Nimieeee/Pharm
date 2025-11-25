# Chat Interface Quick Start Guide

## Overview
The PharmGPT chat interface is inspired by ChatGPT's clean, minimal design with a focus on pharmaceutical conversations.

## Getting Started

### 1. Installation
```bash
cd nextjs-pharmgpt
npm install
```

### 2. Environment Setup
Create `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run Development Server
```bash
npm run dev
```

Navigate to: `http://localhost:3000/chat`

## Interface Components

### Sidebar (Left Panel)
- **Toggle**: Click the panel icon to show/hide
- **New Chat**: Start a fresh conversation
- **Search**: Find previous chats
- **Library**: Access saved documents
- **Chat History**: View and resume past conversations
- **Profile**: User settings and upgrade options

### Header (Top Bar)
- **Model Selector**: Choose AI model (PharmGPT)
- **Group Chat**: Start collaborative sessions (future)
- **Temporary Chat**: Enable ephemeral mode (future)

### Messages (Center)
- **User Messages**: Right-aligned with user avatar
- **Assistant Messages**: Left-aligned with bot avatar
- **Loading State**: Animated "Thinking..." indicator
- **Empty State**: Welcome message when no messages

### Input (Bottom)
- **Textarea**: Auto-expands as you type (max 200px)
- **Attachment**: Click paperclip to upload files
- **Voice**: Click microphone for voice input
- **Send**: Click arrow or press Enter to send

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift + Enter` | New line in message |
| `⌘/Ctrl + K` | Search chats |
| `⇧ ⌘ O` | New chat |

## Usage Examples

### Basic Chat
1. Type your question in the input box
2. Press Enter or click the send button
3. Wait for the AI response
4. Continue the conversation

### With Initial Query
Navigate to: `/chat?q=What are the side effects of aspirin?`

The chat will automatically start with your query.

### File Upload (Future)
1. Click the paperclip icon
2. Select your document
3. The AI will analyze and respond

## API Integration

The chat interface sends requests to your backend:

**Endpoint**: `POST /api/v1/ai/chat`

**Request Body**:
```json
{
  "message": "Your question here",
  "conversation_history": [
    {
      "id": "1",
      "role": "user",
      "content": "Previous message",
      "timestamp": "2025-11-25T10:00:00Z"
    }
  ]
}
```

**Expected Response**:
```json
{
  "response": "AI response here",
  "sources": ["source1", "source2"],
  "confidence": 0.95
}
```

## Customization

### Change Colors
Edit `tailwind.config.ts`:
```typescript
colors: {
  background: '#212121',  // Main background
  card: '#2f2f2f',        // Sidebar/cards
  accent: '#10a37f',      // Brand color
}
```

### Modify Chat History
Edit `src/components/chat/ChatSidebar.tsx`:
```typescript
const chatHistory = [
  { id: '1', title: 'Your chat title', date: 'Today' },
  // Add more...
]
```

### Adjust Message Layout
Edit `src/components/chat/ChatMessages.tsx`:
- Change max-width: `max-w-3xl` → `max-w-4xl`
- Adjust spacing: `space-y-6` → `space-y-8`
- Modify avatars: Change icon sizes

### Customize Input
Edit `src/components/chat/ChatInput.tsx`:
- Max height: `max-h-[200px]` → `max-h-[300px]`
- Placeholder text: `"Ask anything"` → `"Your text"`
- Button styles: Modify colors and sizes

## Troubleshooting

### Sidebar Won't Toggle
- Check `sidebarOpen` state in `page.tsx`
- Verify `onToggle` callback is passed correctly
- Inspect CSS transitions in `ChatSidebar.tsx`

### Messages Not Scrolling
- Ensure `messagesEndRef` is attached to div
- Check `useEffect` dependency array includes `messages`
- Verify `overflow-y-auto` class on container

### Input Not Expanding
- Check `adjustHeight` function in `ChatInput.tsx`
- Verify `onChange` handler calls `adjustHeight()`
- Inspect textarea `ref` is properly set

### API Calls Failing
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`
- Check backend is running on correct port
- Inspect network tab for CORS errors
- Ensure request format matches backend expectations

### Loading State Stuck
- Check `finally` block sets `isLoading` to false
- Verify error handling doesn't skip state update
- Add timeout for API calls

## Best Practices

### Performance
- Keep message history under 100 messages
- Implement pagination for long conversations
- Use React.memo for message components
- Debounce search input

### UX
- Show loading indicators immediately
- Provide error messages that are actionable
- Auto-save drafts in input
- Confirm before clearing chat

### Accessibility
- Use semantic HTML
- Add ARIA labels to buttons
- Support keyboard navigation
- Provide screen reader announcements

### Security
- Sanitize user input
- Validate file uploads
- Implement rate limiting
- Use HTTPS in production

## Deployment

### Vercel (Recommended)
```bash
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
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables
Set in your deployment platform:
- `NEXT_PUBLIC_API_URL`: Your backend URL

## Support

For issues or questions:
1. Check [CHATGPT_ARCHITECTURE.md](./CHATGPT_ARCHITECTURE.md)
2. Review [README.md](./README.md)
3. Inspect browser console for errors
4. Check backend logs

## Next Steps

1. **Test the interface**: Send various types of queries
2. **Customize branding**: Update colors and text
3. **Add features**: Implement file upload, voice input
4. **Optimize performance**: Add caching, pagination
5. **Deploy**: Push to production environment

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [React Hooks](https://react.dev/reference/react)
- [TypeScript](https://www.typescriptlang.org/docs)

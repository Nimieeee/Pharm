# Streaming Chat Implementation

## Overview

PharmGPT now features real-time streaming chat powered by custom streaming hooks and Streamdown for beautiful markdown rendering.

## Architecture

### Frontend Components

1. **`useStreamingChat` Hook** (`frontend/src/hooks/useStreamingChat.ts`)
   - Custom React hook for managing streaming chat
   - Handles SSE (Server-Sent Events) streaming from backend
   - Manages message state, loading states, and file uploads
   - Supports abort/cancel functionality

2. **`StreamingMessage` Component** (`frontend/src/components/StreamingMessage.tsx`)
   - Renders individual chat messages
   - Uses Streamdown for markdown rendering
   - Shows streaming cursor animation
   - Swiss Spa design aesthetic

3. **Streamdown CSS** (`frontend/src/index.css`)
   - Beautiful markdown styling
   - Code syntax highlighting
   - Tables, blockquotes, lists
   - Responsive design

### Backend Endpoints

- **`POST /api/v1/ai/chat/stream`** - Streaming chat endpoint
  - Returns Server-Sent Events (SSE)
  - Streams response chunks in real-time
  - Saves complete message to database when done

## Usage Example

```typescript
import { useStreamingChat } from '@/hooks/useStreamingChat'
import { StreamingMessage } from '@/components/StreamingMessage'

function ChatPage() {
  const {
    messages,
    input,
    handleInputChange,
    isLoading,
    sendMessage,
    uploadFile,
    stop
  } = useStreamingChat({
    conversationId: 'your-conversation-id',
    mode: 'fast', // or 'detailed'
    onNewMessage: (message) => {
      console.log('New message:', message)
    }
  })

  return (
    <div>
      {/* Render messages */}
      {messages.map((message, idx) => (
        <StreamingMessage
          key={message.id}
          message={message}
          isStreaming={isLoading && idx === messages.length - 1}
        />
      ))}

      {/* Input */}
      <textarea
        value={input}
        onChange={handleInputChange}
        disabled={isLoading}
      />

      {/* Send button */}
      <button
        onClick={() => sendMessage(input)}
        disabled={!input.trim() || isLoading}
      >
        {isLoading ? 'Sending...' : 'Send'}
      </button>

      {/* Stop button */}
      {isLoading && (
        <button onClick={stop}>
          Stop
        </button>
      )}
    </div>
  )
}
```

## Features

### Real-Time Streaming
- Messages appear character-by-character as they're generated
- Smooth, responsive user experience
- No waiting for complete response

### File Upload Integration
```typescript
const { uploadFile } = useStreamingChat({ ... })

// Upload a file
const fileId = await uploadFile(file)

// Send message with file context
await sendMessage('Analyze this document', [fileId])
```

### Abort/Cancel
```typescript
const { stop, isLoading } = useStreamingChat({ ... })

// Cancel ongoing request
if (isLoading) {
  stop()
}
```

### Mode Switching
```typescript
// Fast mode - quick responses
useStreamingChat({ mode: 'fast', ... })

// Detailed mode - comprehensive responses
useStreamingChat({ mode: 'detailed', ... })
```

## Markdown Support

Streamdown renders beautiful markdown including:

- **Headers** (H1-H6)
- **Bold** and *italic* text
- `Inline code`
- Code blocks with syntax highlighting
- Lists (ordered and unordered)
- Tables
- Blockquotes
- Links
- Images

Example:
```markdown
# Pharmacology Overview

## Key Concepts

1. **Pharmacokinetics** - What the body does to the drug
2. **Pharmacodynamics** - What the drug does to the body

### Code Example

\`\`\`python
def calculate_dose(weight, mg_per_kg):
    return weight * mg_per_kg
\`\`\`

> Important: Always verify dosage calculations
```

## Swiss Spa Design

The streaming interface maintains the luxury Swiss Spa aesthetic:

- Soft, rounded corners (`rounded-spa`)
- Smooth transitions (`transition-spa`)
- Elegant color palette
- Touch-friendly interactions (44px minimum)
- Responsive design

## Performance

- **Efficient streaming**: Chunks processed as they arrive
- **Memory management**: Proper cleanup with AbortController
- **Error handling**: Graceful fallbacks and user feedback
- **Loading states**: Clear visual indicators

## Security

- **Authentication**: Bearer token in all requests
- **Input validation**: Security guard on backend
- **Output auditing**: Response validation
- **Rate limiting**: Prevents abuse

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Full support

## Dependencies

```json
{
  "ai": "^5.0.101",
  "streamdown": "^1.6.6",
  "react": "^18.2.0",
  "react-hot-toast": "^2.4.1"
}
```

## Future Enhancements

- [ ] Message editing
- [ ] Regenerate response
- [ ] Copy to clipboard
- [ ] Export conversation
- [ ] Voice input
- [ ] Multi-modal support (images in responses)
- [ ] Collaborative chat
- [ ] Message reactions

## Troubleshooting

### Streaming not working
- Check backend `/chat/stream` endpoint is accessible
- Verify authentication token is valid
- Check browser console for errors

### Messages not rendering
- Ensure Streamdown CSS is loaded
- Check message format matches `StreamingMessage` type
- Verify `content` field is not empty

### File upload fails
- Check file size (max 10MB)
- Verify file format is supported
- Check conversation ID is valid

## Support

For issues or questions:
- Check backend logs for errors
- Review browser console
- Verify API endpoints are responding
- Test with simple messages first

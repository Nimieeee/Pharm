'use client'

import { useState } from 'react'
import { Send } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function FloatingChatInput() {
  const [prompt, setPrompt] = useState('')
  const router = useRouter()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim()) {
      router.push(`/chat?q=${encodeURIComponent(prompt)}`)
    }
  }

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-3xl px-6 z-40">
      <form onSubmit={handleSubmit}>
        <div className="relative bg-card rounded-2xl border border-border shadow-2xl hover:border-accent/50 transition-colors backdrop-blur-lg">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Message PharmGPT"
            className="w-full px-6 py-4 bg-transparent focus:outline-none pr-14"
          />
          <button
            type="submit"
            disabled={!prompt.trim()}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-accent hover:bg-accent-hover disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  )
}

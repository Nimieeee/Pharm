'use client'

import { useState } from 'react'
import { Send, Sparkles } from 'lucide-react'
import { useRouter } from 'next/navigation'

const samplePrompts = [
  'Drug interactions with Metformin',
  'Latest clinical trials for cancer treatment',
  'Pharmacokinetics of antibiotics',
  'FDA approval process timeline',
  'Adverse effects of statins',
  'Pharmaceutical compound analysis',
]

export default function HeroSection() {
  const [prompt, setPrompt] = useState('')
  const router = useRouter()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim()) {
      router.push(`/chat?q=${encodeURIComponent(prompt)}`)
    }
  }

  const handlePromptClick = (text: string) => {
    setPrompt(text)
  }

  return (
    <section className="relative min-h-[80vh] flex items-center justify-center px-6 pt-24 pb-16">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-accent/5 to-transparent pointer-events-none" />
      
      <div className="relative max-w-4xl w-full space-y-12">
        {/* Title */}
        <div className="text-center space-y-4 animate-fade-in">
          <h1 className="text-5xl md:text-6xl font-bold">
            What can I help with?
          </h1>
          <p className="text-gray-400 text-lg">
            Ask anything about pharmaceuticals, drug interactions, or clinical research
          </p>
        </div>

        {/* Main Input */}
        <form onSubmit={handleSubmit} className="relative animate-slide-up">
          <div className="relative bg-card rounded-2xl border border-border hover:border-accent/50 transition-colors">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Message PharmGPT"
              className="w-full px-6 py-4 bg-transparent resize-none focus:outline-none min-h-[120px]"
              rows={3}
            />
            <div className="flex items-center justify-between px-6 pb-4">
              <div className="flex items-center space-x-2 text-sm text-gray-400">
                <Sparkles size={16} />
                <span>AI-powered pharmaceutical intelligence</span>
              </div>
              <button
                type="submit"
                disabled={!prompt.trim()}
                className="p-3 bg-accent hover:bg-accent-hover disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </form>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-3 justify-center animate-fade-in">
          <button className="px-4 py-2 bg-card hover:bg-card-hover rounded-full text-sm transition-colors border border-border">
            Search Database
          </button>
          <button className="px-4 py-2 bg-card hover:bg-card-hover rounded-full text-sm transition-colors border border-border">
            Upload Document
          </button>
          <button className="px-4 py-2 bg-card hover:bg-card-hover rounded-full text-sm transition-colors border border-border">
            Research
          </button>
          <button className="px-4 py-2 bg-card hover:bg-card-hover rounded-full text-sm transition-colors border border-border">
            More
          </button>
        </div>

        {/* Sample Prompts */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 animate-fade-in">
          {samplePrompts.map((text, index) => (
            <button
              key={index}
              onClick={() => handlePromptClick(text)}
              className="px-4 py-3 bg-card hover:bg-card-hover rounded-lg text-sm text-left transition-colors border border-border hover:border-accent/50"
            >
              {text}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}

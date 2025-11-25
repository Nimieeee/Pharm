'use client'

import { useState } from 'react'
import HeroSection from '@/components/HeroSection'
import ContentGrid from '@/components/ContentGrid'
import FloatingChatInput from '@/components/FloatingChatInput'

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const featuredContent = [
    {
      id: 1,
      title: 'Advanced Drug Interaction Analysis',
      category: 'Research',
      date: 'Nov 24, 2025',
      readTime: '5 min read',
      image: '/images/drug-interaction.jpg',
      link: '/research/drug-interactions'
    },
    {
      id: 2,
      title: 'AI-Powered Clinical Trial Insights',
      category: 'Product',
      date: 'Nov 20, 2025',
      readTime: '7 min read',
      image: '/images/clinical-trials.jpg',
      link: '/product/clinical-trials'
    },
    {
      id: 3,
      title: 'Pharmaceutical Compound Discovery',
      category: 'Research',
      date: 'Nov 19, 2025',
      readTime: '6 min read',
      image: '/images/compound-discovery.jpg',
      link: '/research/compound-discovery'
    },
  ]

  const latestNews = [
    {
      id: 1,
      title: 'New FDA Approval Guidelines Integration',
      category: 'Safety',
      date: 'Nov 20, 2025',
      image: '/images/fda.jpg',
      link: '/news/fda-guidelines'
    },
    {
      id: 2,
      title: 'Expanding Pharmaceutical Database Coverage',
      category: 'Company',
      date: 'Nov 19, 2025',
      image: '/images/database.jpg',
      link: '/news/database-expansion'
    },
    {
      id: 3,
      title: 'Enhanced Drug Safety Monitoring',
      category: 'Safety',
      date: 'Nov 18, 2025',
      image: '/images/safety.jpg',
      link: '/news/safety-monitoring'
    },
  ]

  return (
    <>
      <HeroSection />
      
      <div className="max-w-7xl mx-auto px-6 py-16 space-y-20">
        <ContentGrid 
          title="Featured Research" 
          items={featuredContent}
          viewAllLink="/research"
        />
        
        <ContentGrid 
          title="Latest News" 
          items={latestNews}
          viewAllLink="/news"
        />
      </div>

      <FloatingChatInput />
    </>
  )
}

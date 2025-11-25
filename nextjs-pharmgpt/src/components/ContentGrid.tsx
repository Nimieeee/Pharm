'use client'

import Link from 'next/link'
import { ArrowRight, Clock } from 'lucide-react'

interface ContentItem {
  id: number
  title: string
  category: string
  date: string
  readTime?: string
  image?: string
  link: string
}

interface ContentGridProps {
  title: string
  items: ContentItem[]
  viewAllLink: string
}

export default function ContentGrid({ title, items, viewAllLink }: ContentGridProps) {
  return (
    <section className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">{title}</h2>
        <Link
          href={viewAllLink}
          className="flex items-center space-x-2 text-accent hover:text-accent-hover transition-colors"
        >
          <span>View all</span>
          <ArrowRight size={20} />
        </Link>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {items.map((item) => (
          <Link
            key={item.id}
            href={item.link}
            className="group block bg-card hover:bg-card-hover rounded-xl overflow-hidden transition-all hover:scale-[1.02] border border-border hover:border-accent/50"
          >
            {/* Image Placeholder */}
            <div className="aspect-video bg-gradient-to-br from-accent/20 to-accent/5 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
              <div className="absolute bottom-4 left-4 right-4">
                <span className="inline-block px-3 py-1 bg-accent/90 rounded-full text-xs font-medium">
                  {item.category}
                </span>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-3">
              <h3 className="text-xl font-semibold group-hover:text-accent transition-colors line-clamp-2">
                {item.title}
              </h3>
              
              <div className="flex items-center space-x-4 text-sm text-gray-400">
                <time>{item.date}</time>
                {item.readTime && (
                  <>
                    <span>•</span>
                    <div className="flex items-center space-x-1">
                      <Clock size={14} />
                      <span>{item.readTime}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}

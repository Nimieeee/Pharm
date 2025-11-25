'use client'

import Link from 'next/link'
import { Github, Twitter, Linkedin, Mail } from 'lucide-react'

export default function Footer() {
  const footerSections = [
    {
      title: 'Research',
      links: [
        { label: 'Research Index', href: '/research' },
        { label: 'Clinical Trials', href: '/research/clinical-trials' },
        { label: 'Drug Database', href: '/research/database' },
        { label: 'Publications', href: '/research/publications' },
      ],
    },
    {
      title: 'Safety',
      links: [
        { label: 'Safety Overview', href: '/safety' },
        { label: 'Drug Interactions', href: '/safety/interactions' },
        { label: 'Adverse Effects', href: '/safety/adverse-effects' },
        { label: 'Reporting', href: '/safety/reporting' },
      ],
    },
    {
      title: 'API Platform',
      links: [
        { label: 'API Overview', href: '/api' },
        { label: 'Documentation', href: '/api/docs' },
        { label: 'Pricing', href: '/api/pricing' },
        { label: 'API Login', href: '/api/login' },
      ],
    },
    {
      title: 'Company',
      links: [
        { label: 'About Us', href: '/about' },
        { label: 'Careers', href: '/careers' },
        { label: 'Contact', href: '/contact' },
        { label: 'Blog', href: '/blog' },
      ],
    },
    {
      title: 'Legal',
      links: [
        { label: 'Terms of Use', href: '/terms' },
        { label: 'Privacy Policy', href: '/privacy' },
        { label: 'Cookie Policy', href: '/cookies' },
        { label: 'Compliance', href: '/compliance' },
      ],
    },
  ]

  return (
    <footer className="border-t border-border bg-background mt-20">
      <div className="max-w-7xl mx-auto px-6 py-16">
        {/* Main Footer Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-8 mb-12">
          {footerSections.map((section) => (
            <div key={section.title}>
              <h3 className="font-semibold mb-4">{section.title}</h3>
              <ul className="space-y-3">
                {section.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-gray-400 hover:text-accent transition-colors text-sm"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Social Links & Copyright */}
        <div className="flex flex-col md:flex-row items-center justify-between pt-8 border-t border-border space-y-4 md:space-y-0">
          <div className="flex items-center space-x-6">
            <Link
              href="https://twitter.com"
              target="_blank"
              className="text-gray-400 hover:text-accent transition-colors"
              aria-label="Twitter"
            >
              <Twitter size={20} />
            </Link>
            <Link
              href="https://github.com"
              target="_blank"
              className="text-gray-400 hover:text-accent transition-colors"
              aria-label="GitHub"
            >
              <Github size={20} />
            </Link>
            <Link
              href="https://linkedin.com"
              target="_blank"
              className="text-gray-400 hover:text-accent transition-colors"
              aria-label="LinkedIn"
            >
              <Linkedin size={20} />
            </Link>
            <Link
              href="mailto:contact@pharmgpt.com"
              className="text-gray-400 hover:text-accent transition-colors"
              aria-label="Email"
            >
              <Mail size={20} />
            </Link>
          </div>

          <div className="text-sm text-gray-400">
            PharmGPT © 2015–2025
          </div>
        </div>
      </div>
    </footer>
  )
}

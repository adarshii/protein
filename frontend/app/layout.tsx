import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from '@/components/ui/toaster'

export const metadata: Metadata = {
  title: {
    default: 'BioChemAI Platform',
    template: '%s | BioChemAI',
  },
  description:
    'Advanced bioinformatics and chemoinformatics platform powered by AI — sequence analysis, molecular descriptors, omics data, and clinical evidence.',
  keywords: ['bioinformatics', 'chemoinformatics', 'AI', 'genomics', 'proteomics', 'drug discovery'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
        <Toaster />
      </body>
    </html>
  )
}

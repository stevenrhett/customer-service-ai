import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Customer Service AI',
  description: 'Multi-agent AI customer service system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

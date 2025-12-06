import type { Metadata, Viewport } from "next"
import "../styles/globals.css"

export const metadata: Metadata = {
  title: "Customer Service AI",
  description: "Advanced multi-agent customer service system",
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#3b82f6",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  )
}

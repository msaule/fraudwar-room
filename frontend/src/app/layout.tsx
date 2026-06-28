import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'FraudWar Room',
  description: 'Adaptive fraud simulation and review dashboard',
  icons: {
    icon: '/favicon.svg'
  }
}

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

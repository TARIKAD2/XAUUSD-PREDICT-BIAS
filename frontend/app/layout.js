import '../styles/globals.css'

export const metadata = {
  title: 'AI Market Intelligence',
  description: 'Financial market intelligence and machine-learning research platform',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
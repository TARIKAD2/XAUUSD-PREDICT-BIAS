import Providers from '../components/Providers';
import '../styles/globals.css';

export const metadata = {
  title: 'AI Market Intelligence | Quantitative Terminal',
  description: 'Real-time financial market intelligence and machine-learning quantitative research platform',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
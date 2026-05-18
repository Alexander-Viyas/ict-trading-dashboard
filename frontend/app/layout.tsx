import './globals.css';

export const metadata = {
  title: 'ICT Trading Dashboard',
  description: 'Hybrid MT5 + CSV Backtesting with AI Insights',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-ict-dark text-slate-200 min-h-screen">{children}</body>
    </html>
  );
}

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'ict-dark': '#0f172a',
        'ict-panel': '#1e293b',
        'ict-accent': '#38bdf8',
        'ict-bull': '#22c55e',
        'ict-bear': '#ef4444',
      },
    },
  },
  plugins: [],
};

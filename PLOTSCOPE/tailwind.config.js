/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        theme: {
          primary: '#EA580C',      // Orange 600 (Professional, deep orange)
          primaryHover: '#C2410C', // Orange 700
          secondary: '#D97706',    // Amber 600 (Golden/Yellow accent)
          text: '#FAFAFA',         // Off-white for dark mode
          subtle: '#A3A3A3',       // Neutral 400
          bg: '#0A0A0A',           // Very dark grey/black
          paper: '#171717',        // Slightly lighter dark for cards
          border: '#262626',       // Dark borders
        }
      },
      fontFamily: {
        'serif': ['Georgia', 'Cambria', '"Times New Roman"', 'Times', 'serif'],
        'editorial': ['"Playfair Display"', 'Georgia', 'serif'],
        'mono': ['"JetBrains Mono"', 'Consolas', 'monospace'],
        'sans': ['"Manrope"', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

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
          primary: '#0F766E',      // TU VERDE EXACTO (Teal 700)
          primaryHover: '#0D9488', // Un tono más brillante para el hover (Teal 600)
          text: '#111827',         // Negro tinta
          subtle: '#4B5563',       // Gris suave
          bg: '#FAFAFA',           // Fondo papel
          paper: '#FFFFFF',        // Blanco puro
          border: '#E5E7EB',       // Bordes grises
        }
      },
      fontFamily: {
        // La fuente que te gusta para el logo LYA
        'serif': ['Georgia', 'Cambria', '"Times New Roman"', 'Times', 'serif'],
        // La fuente elegante para títulos grandes
        'editorial': ['"Playfair Display"', 'Georgia', 'serif'],
        // La fuente para datos
        'mono': ['"JetBrains Mono"', 'Consolas', 'monospace'],
        // La fuente para textos generales
        'sans': ['system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
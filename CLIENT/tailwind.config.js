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
          // Verde teal principal (exacto de la imagen)
          primary: '#0F766E',
          // Textos
          text: '#1A1A1A',
          subtle: '#374151',
          // Fondos
          bg: '#F7F7F7',
          header: '#FFFFFF',
          // Bordes
          border: '#D1D5DB',
        }
      },
      fontFamily: {
        // Fuente serif para títulos (estilo editorial/reporte)
        'report-serif': ['Georgia', 'Cambria', '"Times New Roman"', 'serif'],
        // Fuente mono para datos (estilo máquina de escribir)
        'report-mono': ['Consolas', 'Monaco', '"Courier New"', 'monospace'],
      },
    },
  },
  plugins: [],
}

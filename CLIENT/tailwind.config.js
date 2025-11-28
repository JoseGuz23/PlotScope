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
          bg: '#F7F7F7',      // Papel/Crema
          header: '#FFFFFF',  // Blanco Puro
          primary: '#2F855A', // Verde Bosque
          text: '#1A1A1A',    // Negro Profundo
          subtle: '#374151',  // Gris Encabezados
          border: '#D1D5DB'   // Gris Líneas
        }
      },
      fontFamily: {
        'report-mono': ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        'report-serif': ['ui-serif', 'Georgia', 'serif'],
      }
    },
  },
  plugins: [],
}
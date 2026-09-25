/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0B1220',
        panel: '#101A2E',
        'panel-2': '#0D1626',
        grid: '#1E2C47',
        'grid-soft': '#17223A',
        textMain: '#E8EDF5',
        muted: '#7C8BA8',
        blueAccent: '#4C7EFF',
        'blue-dim': '#2B4A99',
        redAccent: '#E8543E',
        amberAccent: '#E0A526',
        greenAccent: '#3FB88A',
      },
      fontFamily: {
        mono: ['IBM Plex Mono', 'monospace'],
        sans: ['IBM Plex Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

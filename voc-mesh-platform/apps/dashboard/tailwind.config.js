/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        space: {
          DEFAULT: '#0A0F1E',
          50: '#1A2332',
          100: '#141C2B',
        },
        voc: {
          DEFAULT: '#00FF9C',
          dark: '#00CC7D',
          light: '#33FFB0',
        },
        alert: {
          DEFAULT: '#FF3B30',
          dark: '#CC2F26',
        },
        panel: '#1A2332',
        text: {
          DEFAULT: '#E8EDF2',
          muted: '#8B95A5',
          dim: '#5A6577',
        },
      },
      fontFamily: {
        display: ['Space Mono', 'monospace'],
        body: ['IBM Plex Sans', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};

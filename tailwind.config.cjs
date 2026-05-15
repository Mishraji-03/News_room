/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        'shimmer-fast': 'shimmer-move 1.5s infinite linear',
        'shimmer': 'shimmer-move 2s infinite ease-in-out',
      },
      keyframes: {
        'shimmer-move': {
          '0%': { transform: 'translateX(-150%)' },
          '100%': { transform: 'translateX(300%)' },
        },
      },
    },
  },
  plugins: [],
}

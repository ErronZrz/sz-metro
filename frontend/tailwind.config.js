/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        metro: {
          primary: '#0066CC',
          secondary: '#00A651',
          accent: '#FF6B35',
        }
      }
    },
  },
  plugins: [],
}

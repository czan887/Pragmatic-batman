/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        twitter: {
          blue: '#1DA1F2',
          dark: '#14171A',
          gray: '#657786',
          light: '#AAB8C2',
          lighter: '#E1E8ED',
          lightest: '#F5F8FA',
        },
      },
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        'haze-blue-1': '#0F6BAE',
        'haze-blue-2': '#248BD6',
        'haze-blue-3': '#83B8FF',
        'haze-blue-4': '#C6CDFF'
      }
    }
  },
  plugins: []
};

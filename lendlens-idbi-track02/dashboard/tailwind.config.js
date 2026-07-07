/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        idbi: {
          green: "#0b6b3a",     // IDBI-style deep green (primary)
          greenDark: "#08532d",
          greenLight: "#e8f3ec",
          gold: "#b8860b",
        },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "Segoe UI", "Roboto", "Helvetica", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};

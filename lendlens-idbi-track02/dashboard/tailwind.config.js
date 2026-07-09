/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        idbi: {
          green: "#0b6b3a",
          greenDark: "#08532d",
          greenLight: "#e8f3ec",
          gold: "#b8860b",
        },
        // Fundly-inspired accent system (used in dark theme)
        ll: {
          blue: "#3e8bff",
          orange: "#ff7a45",
          green: "#3fe08a",
          pink: "#ec4899",
          purple: "#a855f7",
          amber: "#ffb547",
          red: "#ff5f6d",
          txt: "#eceef3",
          txt2: "#8b909e",
          txt3: "#5f6472",
        },
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "ui-sans-serif", "system-ui", "Segoe UI", "Roboto", "sans-serif"],
      },
      keyframes: {
        "fade-up": {
          from: { opacity: 0, transform: "translateY(6px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
      },
      animation: { "fade-up": "fade-up 0.25s ease-out both" },
    },
  },
  plugins: [],
};

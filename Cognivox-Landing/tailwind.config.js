const { lightTheme, draculaTheme } = require("./src/themes/theme");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./index.html"],
  theme: {
    extend: {
      colors: {
        ...draculaTheme.colors,
        ...lightTheme.colors,
      },
      animation: {
        "meteor-effect": "meteor 5s linear infinite",
        "shooting-star": "shooting-star 10s linear infinite",
      },
      keyframes: {
        meteor: {
          "0%": { transform: "rotate(215deg) translateX(0)", opacity: "1" },
          "70%": { opacity: "1" },
          "100%": {
            transform: "rotate(215deg) translateX(-800px)",
            opacity: "0",
          },
        },
        "shooting-star": {
          "0%": { transform: "translateX(-100px) translateY(0)", opacity: "0" },
          "10%": { opacity: "1" },
          "90%": { opacity: "1" },
          "100%": { transform: "translateX(100vw) translateY(-100px)", opacity: "0" },
        },
      },
    },
  },
  plugins: [],
}; 
const { lightTheme, draculaTheme } = require("./src/themes/theme");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ...draculaTheme.colors,
        ...lightTheme.colors,
      },
      animation: {
        "meteor-effect": "meteor 5s linear infinite",
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
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: 'inherit',
            a: {
              color: '#3182ce',
              '&:hover': {
                color: '#2c5282',
              },
            },
            strong: {
              color: 'inherit',
            },
            code: {
              color: 'inherit',
              backgroundColor: 'rgb(var(--tw-prose-pre-bg))',
              paddingLeft: '0.25rem',
              paddingRight: '0.25rem',
              paddingTop: '0.125rem',
              paddingBottom: '0.125rem',
              borderRadius: '0.25rem',
            },
            'code::before': {
              content: 'none',
            },
            'code::after': {
              content: 'none',
            },
            pre: {
              backgroundColor: 'rgb(var(--tw-prose-pre-bg))',
              color: 'inherit',
              borderRadius: '0.375rem',
              padding: '0.75rem 1rem',
            },
            blockquote: {
              color: 'inherit',
              borderLeftWidth: '0.25rem',
              borderLeftColor: 'rgb(var(--tw-prose-quote-borders))',
              fontStyle: 'italic',
            },
            hr: {
              borderColor: 'rgb(var(--tw-prose-hr))',
            },
            h1: {
              color: 'inherit',
            },
            h2: {
              color: 'inherit',
            },
            h3: {
              color: 'inherit',
            },
            h4: {
              color: 'inherit',
            },
            'ul > li::before': {
              backgroundColor: 'rgb(var(--tw-prose-bullets))',
            },
            'ol > li::before': {
              color: 'rgb(var(--tw-prose-counters))',
            },
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};

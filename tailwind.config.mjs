/** @type {import('tailwindcss').Config} */
// The tokens are at the top of src/styles/global.css; these repeat them for any utility class.
export default {
  content: ['./src/**/*.{astro,html,js,jsx,ts,tsx,md,mdx}'],
  theme: {
    extend: {
      colors: {
        // Pucksley: the film's card house on the kitchen bench, and the puck's own screen.
        card: { DEFAULT: '#F6F3ED', deep: '#ECE6DB' },
        bench: '#D8CBB5',
        ink: { DEFAULT: '#141416', soft: '#56534E' },
        night: { DEFAULT: '#0B0B0D', blue: '#18212E' },
        yellow: '#FFD60A',
        clay: '#DA7A55',
        screen: '#CFE3F6',
      },
      fontFamily: {
        sans: ['"Nunito Variable"', 'Nunito', 'system-ui', '"Segoe UI"', 'sans-serif'],
      },
      maxWidth: {
        page: '1160px',
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './**/templates/**/*.html',
    './static/**/*.js',
    '!./venv/**',
    '!./node_modules/**',
  ],
  theme: {
    extend: {
      colors: {
        navy: '#0B2545',
        navy2: '#0F3460',
        gold: '#D4AF37',
        green: '#146B3A',
        paper: '#FBFAF7',
      },
      fontFamily: {
        serif: ['Georgia', 'Times New Roman', 'serif'],
      },
    },
  },
  plugins: [],
};

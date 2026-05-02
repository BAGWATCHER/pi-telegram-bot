/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Scriptorium design tokens
      colors: {
        parchment: {
          50: '#fdf8f0',
          100: '#f9f0e2',
          200: '#f2e0c3',
          300: '#e8cfa0',
          400: '#dcb87a',
          500: '#d1a55c',
          600: '#c49248',
          700: '#a87a3a',
          800: '#8b6332',
          900: '#73522c',
          950: '#3d2b16',
        },
        ink: {
          50: '#f5f0ea',
          100: '#e0d6c8',
          200: '#c4b5a0',
          300: '#a89478',
          400: '#8c7858',
          500: '#725f40',
          600: '#5a4830',
          700: '#433520',
          800: '#2d2212',
          900: '#1a1208',
          950: '#0d0904',
        },
        gold: {
          50: '#fdfaed',
          100: '#f9f0cc',
          200: '#f3df95',
          300: '#ebc954',
          400: '#e0b020',
          500: '#c49412',
          600: '#9e730f',
          700: '#7d5911',
          800: '#664716',
          900: '#553c18',
          950: '#2f2009',
        },
      },
      fontFamily: {
        serif: ['Cormorant Garamond', 'Georgia', 'serif'],
        display: ['Cinzel', 'Georgia', 'serif'],
        body: ['Lora', 'Georgia', 'serif'],
      },
      backgroundImage: {
        'parchment-noise': "url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJmIj48ZmVUdXJidWxlbmNlIHR5cGU9ImZyYWN0YWxOb2lzZSIgYmFzZUZyZXF1ZW5jeT0iLjc1IiBudW1PY3RhdmVzPSIzIiAvPjwvZmlsdGVyPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbHRlcj0idXJsKCNmKSIgb3BhY2l0eT0iMC4wNCIgLz48L3N2Zz4=')",
      },
    },
  },
  plugins: [],
}


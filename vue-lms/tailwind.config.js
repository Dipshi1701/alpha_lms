/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── ASI Brand Palette ────────────────────────────────────────────────
        // Use these everywhere: bg-asi-purple, text-asi-red, border-asi-lavender …
        asi: {
          purple:   '#462C6B',   // primary – sidebar, headers, badges
          'purple-light': '#F0EDF6', // tinted surface
          lavender: '#7D6B9D',   // secondary accent
          red:      '#CA1F47',   // CTA buttons, danger, highlights
          'red-light': '#FAEAEE',
          orange:   '#F26524',   // third accent, icons
          'orange-light': '#FEF0E8',
          blue:     '#4890C0',   // links, secondary buttons
          'blue-light': '#EAF3FA',
          gray:     '#67686B',   // muted body text
          black:    '#231F20',   // headings / dark text
          surface:  '#F7F5FA',   // page background
          border:   '#E8E2F0',   // card borders
        },
      },
      fontFamily: {
        // Arial is the approved web-safe fallback per ASI brand guidelines
        sans: ['Arial', 'Helvetica', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

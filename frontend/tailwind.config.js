/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
    theme: {
        extend: {
            fontFamily: {
                display: ['"Cormorant Garamond"', '"Times New Roman"', "serif"],
                sans: ["Inter", "system-ui", "sans-serif"],
                mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
            },
            colors: {
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
                popover: { DEFAULT: "hsl(var(--popover))", foreground: "hsl(var(--popover-foreground))" },
                primary: { DEFAULT: "hsl(var(--primary-h))", foreground: "hsl(var(--primary-foreground))" },
                secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
                muted: { DEFAULT: "hsl(var(--muted-h))", foreground: "hsl(var(--muted-foreground))" },
                accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
                destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                // Claude palette
                canvas: "#faf9f5",
                cream: { DEFAULT: "#faf9f5", card: "#efe9de", strong: "#e8e0d2", soft: "#f5f0e8" },
                coral: { DEFAULT: "#14345c", active: "#0e2545" },
                ink: "#141413",
                bodytext: "#3d3d3a",
                mutedink: "#6c6a64",
                hairline: "#e6dfd8",
                navy: { DEFAULT: "#181715", soft: "#1f1e1b", elevated: "#252320" },
                teal: "#0f5f8f",
                amber: "#c8a24a",
                // legacy names kept so unchanged components still render
                volt: "#14345c",
                signal: "#b23a3a",
                electric: "#c8a24a",
                success: "#5db872",
                surface0: "#faf9f5",
                surface1: "#efe9de",
                surface2: "#e8e0d2",
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
            },
            keyframes: {
                "accordion-down": { from: { height: "0" }, to: { height: "var(--radix-accordion-content-height)" } },
                "accordion-up": { from: { height: "var(--radix-accordion-content-height)" }, to: { height: "0" } },
            },
            animation: {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
            },
        },
    },
    plugins: [require("tailwindcss-animate")],
};

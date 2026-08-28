# TruthLens Design System

## Identity
TruthLens is a forensic intelligence dashboard for detecting deepfakes and misinformation. Its visual identity should feel like a high-security operations center — precise, trustworthy, and authoritative.

## Design Tokens

### Color Palette
- **Background Primary**: Deep Navy `#0f172a` — main app background
- **Background Surface**: Slate `#1e293b` — cards, panels, sidebar
- **Background Elevated**: `#253349` — hover states, active elements
- **Border Default**: `#334155` — subtle container borders
- **Border Active**: `#475569` — focused/hover borders
- **Primary Accent**: Electric Cyan `#06b6d4` — actions, links, active states
- **Primary Hover**: `#0891b2` — darker cyan for hover
- **Primary Glow**: `rgba(6, 182, 212, 0.15)` — subtle background glow
- **Danger**: Crimson `#ef4444` — high-risk indicators
- **Warning**: Amber `#f59e0b` — review-needed states
- **Success**: Emerald `#22c55e` — low-risk/clean results
- **Text Primary**: Cool White `#f1f5f9` — headings, primary text
- **Text Secondary**: Muted Slate `#94a3b8` — descriptions, captions
- **Text Tertiary**: `#64748b` — disabled, placeholder text

### Typography
- **Font Family**: Inter (system fallback: -apple-system, BlinkMacSystemFont, sans-serif)
- **Body**: 15px / 1.6 line-height
- **Headings**: Uppercase, letter-spacing 0.05em, font-weight 700
- **Monospace**: Source Code Pro for code/IDs
- **Tabular Numbers**: `font-variant-numeric: tabular-nums` for scores/numbers

### Spacing Scale
- xs: 4px | sm: 8px | md: 12px | lg: 16px | xl: 24px | 2xl: 32px

### Border Radius
- sm: 6px | md: 8px | lg: 12px | xl: 16px | pill: 50px

### Shadows
- Card: `0 1px 3px rgba(0, 0, 0, 0.3)`
- Elevated: `0 4px 12px rgba(0, 0, 0, 0.4)`
- Glow Cyan: `0 0 20px rgba(6, 182, 212, 0.2)`
- Glow Danger: `0 0 20px rgba(239, 68, 68, 0.3)`

## Component Patterns

### Cards (ops-card)
- Background: Surface
- Border: 1px solid Border Default
- Border-radius: 12px
- Padding: 20px
- Hover: border-color transitions to Border Active

### Buttons
- Primary: Cyan background, white text, pill shape
- Secondary: Transparent with cyan border
- Ghost: No background, text only
- All buttons: visible hover state, focus-visible ring

### Verdict Badges
- Pill-shaped (border-radius: 50px)
- Background: color at 15% opacity
- Border: 2px solid color
- Text: color, uppercase, bold

### Progress Bars
- Height: 6px, border-radius: 3px
- Background: track at 10% opacity
- Fill: smooth width transition

### Tabs
- Background: Surface
- Border: 1px solid Border Default
- Active: Cyan border + cyan text + cyan background glow

## Accessibility (WCAG 2.2 AA)
- All interactive elements: visible focus ring (2px solid cyan, offset 2px)
- Color contrast: minimum 4.5:1 for body text
- Don't rely on color alone — add icons + text labels
- Respect `prefers-reduced-motion`
- Semantic HTML elements
- Keyboard navigable
- Screen reader friendly

## Atmosphere
- **Vibe**: Tech / Cyber — futuristic, neon accents, glassmorphism effects
- **Mood**: Precise, trustworthy, authoritative
- **Motion**: Subtle, purposeful — fade-in, slide-up, pulse-glow for alerts

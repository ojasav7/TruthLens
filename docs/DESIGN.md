# Design System: TruthLens

**Project:** TruthLens — Forensic Intelligence Dashboard  
**Version:** 4.0.2  
**Platform:** Web, Desktop-first (React + Tailwind CSS)

---

## 1. Visual Theme & Atmosphere

TruthLens is a **forensic operations center** — precise, authoritative, and uncompromising. The aesthetic is **dark-tech minimalism**: deep ink backgrounds that feel like a secure terminal, with a single electric green accent that cuts through like a laser. There is no decorative flourish; every element exists to serve the investigator's eye.

**Mood:** Clinical precision meets high-security operations. The interface should feel like peering into a classified analysis terminal — cool, confident, and ruthlessly functional.

**Density:** Moderate. Generous whitespace between sections, but dense information panels when displaying analysis results. The dashboard uses a sidebar + main layout that maximizes screen real estate.

**Philosophy:** "Signal over noise." Every pixel earns its place. If an element doesn't help the user detect threats or understand results, it doesn't exist.

---

## 2. Color Palette & Roles

### Primary Colors

| Name | Hex Code | Role |
|------|----------|------|
| **Void Black** | `#000000` / `oklch(0.05 0 0)` | Primary background — pure, absolute black |
| **Carbon** | `oklch(0.10 0 0)` | Card backgrounds — subtle elevation from void |
| **Graphite** | `oklch(0.12 0 0)` | Secondary surfaces, muted sections |
| **Slate Border** | `oklch(0.18 0 0)` | Borders, dividers, subtle separations |
| **Ash** | `oklch(0.55 0 0)` | Muted text, secondary labels, timestamps |
| **Ghost White** | `oklch(0.95 0 0)` | Primary text, headings, high-emphasis content |

### Accent Colors

| Name | Hex Code | Role |
|------|----------|------|
| **Electric Mint** | `oklch(0.75 0.28 158)` / `#22c55e` | Primary actions, active states, system indicators, success |
| **Crimson Alert** | `oklch(0.577 0.245 27.325)` / `#ef4444` | Destructive actions, high-risk threats, errors |
| **Amber Warning** | `oklch(0.85 0.18 85)` / `#f59e0b` | Warning states, suspicious content, review-needed |
| **Emerald Safe** | `oklch(0.72 0.22 155)` / `#22c55e` | Low-risk, clean results, verified content |

### Semantic Color Mapping

| State | Color | Usage |
|-------|-------|-------|
| **Online/Active** | Electric Mint | Backend status dot, system active badge |
| **Offline/Error** | Crimson Alert | Backend down, analysis failures |
| **High Risk** | Crimson Alert | Threat score > 70%, deepfake detected |
| **Suspicious** | Amber Warning | Threat score 30-70%, needs review |
| **Clean** | Emerald Safe | Threat score < 30%, authentic content |
| **Primary Action** | Electric Mint | CTA buttons, active tabs, focus rings |

---

## 3. Typography Rules

### Font Families

| Role | Font | Fallback |
|------|------|----------|
| **Body/UI** | Inter | system-ui, -apple-system, BlinkMacSystemFont, sans-serif |
| **Code/Data** | JetBrains Mono | Fira Code, SF Mono, Menlo, monospace |

### Type Scale

| Element | Size | Weight | Tracking | Case |
|---------|------|--------|----------|------|
| **Hero Heading** | 5xl–7xl (3rem–4.5rem) | 800 (extrabold) | `-0.05em` (tighter) | Uppercase |
| **Section Heading** | 4xl (2.25rem) | 800 (extrabold) | `-0.05em` (tighter) | Uppercase |
| **Card Title** | xl (1.25rem) | 700 (bold) | normal | Uppercase |
| **Body Text** | base–lg (1rem–1.125rem) | 400 (normal) | normal | Sentence case |
| **Caption/Label** | 10px–xs | 500 (medium) | `0.1em` (widest) | Uppercase |
| **Code/Data** | 10px–xs | 400 (normal) | normal | Monospace |

### Typography Principles

- **Headings are monolithic:** Extra-bold, tightly tracked, uppercase — they feel carved from stone
- **Labels are clinical:** Mono font, widest tracking, smallest size — like instrument readouts
- **Body text is quiet:** Regular weight, muted color — it supports but never competes with headings
- **Tabular data uses tabular-nums:** For threat scores, percentages, and metrics

---

## 4. Component Stylings

### Navigation Bar

- **Position:** Sticky top, z-50
- **Background:** `oklch(0.05 0 0)` at 80% opacity with `backdrop-blur-md`
- **Border:** 1px bottom border using `oklch(0.18 0 0)`
- **Height:** 64px (h-16)
- **Logo:** Green square (24px) + monospace "TRUTHLENS" uppercase

### Buttons

| Variant | Background | Text | Border | Hover |
|---------|-----------|------|--------|-------|
| **Primary (CTA)** | Electric Mint | Void Black | none | `brightness-1.1` |
| **Secondary** | Transparent | Ghost White | `oklch(0.18 0 0)` | `oklch(0.18 0 0)` bg |
| **Ghost** | Transparent | Muted | none | Mint text |

- **Shape:** Sharp corners (no border-radius) — squared-off, clinical
- **Padding:** `px-8 py-4` (CTA), `px-4 py-1.5` (nav)
- **Typography:** Bold, uppercase, widest tracking, xs–sm size
- **Focus:** 2px solid mint ring with 2px offset

### Cards/Containers

- **Background:** `oklch(0.10 0 0)` — barely elevated from void
- **Border:** 1px solid `oklch(0.18 0 0)`
- **Border-radius:** None — sharp, squared edges
- **Shadow:** None — flat, no depth illusion
- **Hover:** `border-primary/30` or `bg-primary/5` — subtle mint tint
- **Padding:** 32px (p-8) for content cards

### Inputs/Forms

- **Background:** `oklch(0.12 0 0)` — slightly lighter than cards
- **Border:** 1px solid `oklch(0.18 0 0)`
- **Border-radius:** None
- **Text:** Ghost White, regular weight
- **Placeholder:** `oklch(0.55 0 0)` — muted ash
- **Focus:** 2px solid mint ring

### Status Indicators

- **Online dot:** 8px circle, Electric Mint, `animate-pulse`
- **Offline dot:** 8px circle, Crimson Alert
- **Badge:** Inline-flex, `bg-primary/10`, `border-primary/20`, `rounded-sm`

### Modality Tabs

- **Active:** `bg-primary` (full mint background, black text)
- **Inactive:** Transparent with icon + label
- **Shape:** Sharp corners, no border-radius
- **Icons:** Lucide React icons (T, Image, Film, Mic)

---

## 5. Layout Principles

### Grid System

- **Max width:** 1280px (`max-w-7xl`)
- **Horizontal padding:** 24px (`px-6`)
- **Dashboard layout:** `grid lg:grid-cols-[320px_1fr]` — fixed sidebar + fluid main
- **Landing hero:** `grid lg:grid-cols-2` — text + visual side by side
- **Modality grid:** `grid md:grid-cols-2 lg:grid-cols-4` — 4 equal columns with 1px gaps
- **Intelligence grid:** `grid md:grid-cols-3` — 3 equal columns with 1px gaps

### Spacing Strategy

- **Section vertical padding:** 96px (`py-24`) — generous breathing room between sections
- **Card internal padding:** 32px (`p-8`) — spacious content areas
- **Element gaps:** 8px–32px (`gap-2` to `gap-8`) — consistent rhythm
- **Grid gaps:** 1px (`gap-px`) with `bg-border` parent — creates separator lines between cards

### Border & Divider Pattern

- **Section separators:** `border-t border-border` — 1px top border
- **Card grids:** `bg-border gap-px` parent — 1px lines between all cards
- **No shadows anywhere** — the design is intentionally flat

### Responsive Breakpoints

- **Mobile:** Single column, stacked layout
- **Tablet (md):** 2-column grids activate
- **Desktop (lg):** Full 4-column grids, sidebar layout, side-by-side hero

### Scroll Behavior

- **Smooth scroll** for anchor links (respects `prefers-reduced-motion`)
- **Sticky nav** with backdrop blur at z-50
- **Scroll-reveal animations** — sections fade in + slide up on viewport entry
- **Staggered card reveals** — grid cards animate in sequence (80–120ms delay)

---

## 6. Animation & Motion

### Easing Curves

- **Primary:** `cubic-bezier(0.16, 1, 0.3, 1)` — fast start, gentle settle (used everywhere)
- **Duration:** 500–700ms for reveals, 3s for scan line, 5s for loader circle

### Key Animations

| Name | Purpose | Duration |
|------|---------|----------|
| **fadeIn** | Hero entrance | 0.6s |
| **slideUp** | Floating badge entrance | 0.5s, 0.8s delay |
| **scan** | Scanning line over hero image | 3s infinite |
| **pulse-glow** | Button hover glow | 2s infinite |
| **scroll-hidden → scroll-visible** | Section reveal on scroll | 0.7s |
| **scroll-hidden-stagger** | Card cascade reveal | 0.5s, staggered delays |

### Reduced Motion

- All animations disabled when `prefers-reduced-motion: reduce` is active
- `animation-duration: 0.01ms` for instant feedback
- Scroll behavior set to `auto` instead of `smooth`

---

## 7. Accessibility (WCAG 2.2 AA)

- **Focus rings:** 2px solid mint with 2px offset on all interactive elements
- **Skip link:** "Skip to main content" — visually hidden until focused
- **Screen reader text:** `.sr-only` class for off-screen labels
- **ARIA labels:** All buttons, status indicators, and interactive elements have descriptive labels
- **Semantic HTML:** `<nav>`, `<main>`, `<section>`, `<article>`, `role="status"`, `role="progressbar"`
- **Color contrast:** Ghost White on Void Black = 19.5:1 ratio (exceeds AAA)
- **Keyboard navigation:** All interactive elements reachable via Tab, Enter activates buttons
- **Alt text:** All images have descriptive alt attributes

---

## 8. Design Tokens (Tailwind CSS)

```css
/* Core palette */
--color-background: oklch(0.05 0 0);      /* Void Black */
--color-foreground: oklch(0.95 0 0);      /* Ghost White */
--color-primary: oklch(0.75 0.28 158);    /* Electric Mint */
--color-destructive: oklch(0.577 0.245 27.325); /* Crimson Alert */
--color-border: oklch(0.18 0 0);          /* Slate Border */
--color-muted-foreground: oklch(0.55 0 0); /* Ash */

/* Semantic aliases */
--color-cyan: oklch(0.75 0.28 158);       /* = primary */
--color-crimson: oklch(0.577 0.245 27.325); /* = destructive */
--color-amber: oklch(0.85 0.18 85);       /* Warning */
--color-emerald: oklch(0.72 0.22 155);    /* Success */
```

---

## 9. Usage Guidelines for Stitch Prompting

When generating new screens for TruthLens, use these visual descriptions:

- **Background:** "Pure void black (#000000) background with no gradients or textures"
- **Cards:** "Flat, sharp-cornered cards with subtle 1px slate borders, no shadows"
- **Accent:** "Electric mint (#22c55e) for all primary actions, active states, and system indicators"
- **Typography:** "Extra-bold uppercase headings with tight tracking, mono-font labels with widest tracking"
- **Layout:** "Generous vertical spacing (96px between sections), tight horizontal padding (24px)"
- **Motion:** "Smooth cubic-bezier(0.16,1,0.3,1) transitions, 500-700ms duration"
- **Mood:** "Clinical, forensic, authoritative — like a classified analysis terminal"

---

*This design system is the source of truth for all TruthLens UI generation. Every new screen, component, or feature must adhere to these tokens and principles.*

# SkillGraph UI Reference & Design Specification

> **Document Version:** 1.0.0  
> **Source Inspected:** Live production web application at `https://career-ready-trail.lovable.app/`  
> **Inspection Method:** Deep inspection of production bundles (`styles-CLjVBCcF.css`, `routes-Dz9By3Ij.js`, `dashboard-DxvMGq8p.js`, `resume-B_qOdenq.js`, `skills-BYoMr0Q2.js`, `github-GIZNmZPF.js`, `jobs-C6pmEC09.js`, `roadmap-BndpPDJf.js`, `analytics-BD0HODut.js`, `projects-DDXkk-ui.js`, `primitives-DZ18TU59.js`, `mock-data-F_G3FcXc.js`, and `connection-feedback-CooBQFnS.js`).

---

## 1. Design Philosophy: "Paper & Ink Edition"

The SkillGraph interface adheres to an **editorial, technical, and typographic aesthetic** referred to in the codebase as the **"Paper & Ink edition"**.

* **Tone & Identity:** High-rigor, calm, authoritative, academic-engineering feel. It deliberately eschews flashy gradients and generic neon SaaS templates in favor of warm tactile paper surfaces, deep black ink typography, editorial serif headlines, and focused amber-orange highlights.
* **Core Metaphor:** A technical dossier or architectural monograph — crisp borders, generous whitespace, tactile contrast, and clear data hierarchy.
* **Editorial Motto:** *"Careers deserve engineering rigor. No vibes. Just signal."*

---

## 2. Color Palette & Token System

The design system is built entirely on native CSS custom properties utilizing modern **OKLCH** color notation for uniform perceptual lightness and chroma.

### 2.1 CSS Custom Properties (Theme Tokens)

#### Light Theme (`:root` - Default)

| CSS Variable | OKLCH Value | Approximate Hex / Appearance | Semantic Purpose |
| :--- | :--- | :--- | :--- |
| `--paper` | `oklch(97.2% 0.008 85)` | `#FBF9F5` / Warm Cream | Primary page background |
| `--paper-2` | `oklch(94.5% 0.01 85)` | `#F3EFEA` / Parchment | Secondary surfaces, muted card fills, tab backgrounds |
| `--ink` | `oklch(14.5% 0 0)` | `#161616` / Deep Ink | Primary text, heavy headings, active pills, solid buttons |
| `--ink-2` | `oklch(24.5% 0 0)` | `#2A2A2A` / Charcoal | Secondary dark accents, borders on dark mode |
| `--highlight` | `oklch(78% 0.16 60)` | `#E58A2B` / Amber Gold | Active status pulse, accent buttons, key gap indicators |
| `--background` | `var(--paper)` | `#FBF9F5` | Overall body background |
| `--foreground` | `var(--ink)` | `#161616` | Main body typography and primary iconography |
| `--card` | `oklch(100% 0 0)` | `#FFFFFF` / Pure White | Elevating cards, input fields, containers |
| `--card-foreground` | `var(--ink)` | `#161616` | Card text and elements |
| `--popover` | `oklch(100% 0 0)` | `#FFFFFF` | Dropdowns, tooltips, popovers |
| `--popover-foreground` | `var(--ink)` | `#161616` | Popover text |
| `--primary` | `var(--ink)` | `#161616` | Primary action button fills |
| `--primary-foreground`| `var(--paper)` | `#FBF9F5` | Primary action button text |
| `--secondary` | `var(--paper-2)` | `#F3EFEA` | Secondary buttons, progress tracks, pill backgrounds |
| `--secondary-foreground`| `var(--ink)` | `#161616` | Secondary element text |
| `--muted` | `var(--paper-2)` | `#F3EFEA` | Subtle dividers and inactive tab tracks |
| `--muted-foreground` | `oklch(45% 0.01 85)` | `#6B665E` / Muted Taupe | Metadata, subtitles, axis labels, timestamps |
| `--accent` | `var(--highlight)` | `#E58A2B` | Radar target fill, badge highlights, missing skill bars |
| `--accent-foreground` | `var(--ink)` | `#161616` | Text rendered on top of accent elements |
| `--destructive` | `oklch(55% 0.22 27)` | `#DC2626` / Crimson | Error notifications, destructive actions |
| `--destructive-foreground` | `var(--paper)` | `#FBF9F5` | Text on destructive elements |
| `--border` | `oklch(88% 0.012 85)` | `#DDD7CE` / Warm Sand | Card outlines, dividers, subtle borders |
| `--input` | `oklch(88% 0.012 85)` | `#DDD7CE` | Input field borders |
| `--ring` | `var(--ink)` | `#161616` | Keyboard focus ring |
| `--radius` | `1rem` (16px) | Base border radius | Base rounding token |

#### Dark Theme (`.dark`)

| CSS Variable | OKLCH Value | Semantic Purpose |
| :--- | :--- | :--- |
| `--background` | `oklch(14.5% 0 0)` | Deep slate-black canvas |
| `--foreground` | `var(--paper)` | High-contrast warm off-white text |
| `--card` | `oklch(20% 0 0)` | Dark surface elevation |
| `--card-foreground` | `var(--paper)` | Text on dark cards |
| `--popover` | `oklch(20% 0 0)` | Dark popover background |
| `--popover-foreground` | `var(--paper)` | Text on dark popovers |
| `--primary` | `var(--paper)` | Inverted primary buttons (white on dark) |
| `--primary-foreground` | `var(--ink)` | Dark text inside inverted primary buttons |
| `--secondary` | `oklch(24% 0 0)` | Secondary pill and bar track backgrounds |
| `--secondary-foreground`| `var(--paper)` | Text on secondary elements |
| `--muted` | `oklch(24% 0 0)` | Muted panels |
| `--muted-foreground` | `oklch(68% 0.01 85)` | Subtle text in dark mode |
| `--border` | `oklch(100% 0 0 / 0.10)` | 10% white alpha borders |
| `--input` | `oklch(100% 0 0 / 0.12)` | 12% white alpha input borders |
| `--ring` | `var(--paper)` | Light focus ring |

### 2.2 Chart & Data Visualization Color Palette

Charts systematically consume CSS variable references so they seamlessly adapt to light and dark modes:
* **Candidate Series ("You"):** `var(--ink)` with `fillOpacity: 0.18` (area and radar fills) or solid `strokeWidth: 2`.
* **Target Role Series ("Target"):** `var(--accent)` (`oklch(78% 0.16 60)`) with `fillOpacity: 0.10`.
* **Language Mix Donut Chart Sequence:**
  1. `var(--foreground)` (dominant language, ~41%)
  2. `var(--muted-foreground)` (secondary language, ~28%)
  3. `var(--accent)` (tertiary language, ~12%)
  4. `var(--secondary)` (quaternary language, ~9%)
  5. `var(--border)` (other/tail languages, ~10%)
* **Grid Lines & Axes:** `var(--border)` (`stroke`), `var(--muted-foreground)` (tick labels, font size 11–12px).
* **Tooltip Card:** `background: var(--card); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.06);`.

---

## 3. Typography System

The application loads three specific Google Web Fonts:

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap"/>
```

### 3.1 Font Families

1. **Display & Headings (`--font-display`):**
   * Font stack: `"Fraunces", "Instrument Serif", ui-serif, Georgia, serif`
   * Characteristics: Elegant optical-size serif, high contrast, warm literary curves.
   * Tracking: `letter-spacing: -0.02em;`
   * Used for: Page titles (`H1`), large numerals (e.g. `text-7xl` readiness scores, `text-8xl` match scores), section titles (`H2`, `H3`), logo mark (`SkillGraph`).
2. **Body & Interface (`--font-sans`):**
   * Font stack: `"Inter", ui-sans-serif, system-ui, -apple-system, sans-serif`
   * Characteristics: Clean neo-grotesque sans-serif, high legibility at micro sizes.
   * Weights: Regular (`400`), Medium (`500`), Semibold (`600`).
   * Used for: Body copy, navigation links, button labels, descriptions, subtitles.
3. **Monospace & Data (`--font-mono`):**
   * Font stack: `"JetBrains Mono", ui-monospace, SFMono-Regular, monospace`
   * Characteristics: Fixed-pitch, technical clarity.
   * Used for: Percentages (`82%`), skill tags, pipeline step numbers (`01`, `02`), dates (`Jul 12`), code snippets, character counters.

### 3.2 Typography Scale & Style Classes

* **Hero Title (Landing):** `font-display text-5xl md:text-7xl lg:text-8xl leading-[0.95] max-w-5xl`
* **Page Header Title (`H1`):** `font-display text-4xl md:text-5xl leading-[1.05]`
* **Section Heading (`H2`):** `font-display text-4xl leading-tight` / Dark CTA banner `text-5xl md:text-6xl leading-[1]`
* **Card Heading (`H3`):** `font-display text-2xl`
* **Sub-card Heading (`H4`):** `font-display text-xl` or `text-2xl`
* **Metric Numbers:** `font-display text-4xl` (KPI cards), `font-display text-7xl` (readiness page), `font-display text-8xl` (job match score)
* **Eyebrows & Badges:** `text-xs uppercase tracking-widest text-muted-foreground font-sans`
* **Body Text:** `text-sm` (14px) and `text-base` / `text-lg` (18px) `text-muted-foreground leading-relaxed`
* **Ink Underline Effect (`.ink-underline`):**
  ```css
  .ink-underline {
    background-image: linear-gradient(currentColor, currentColor);
    background-position: 0 100%;
    background-repeat: no-repeat;
    background-size: 0 1px;
    transition: background-size 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .ink-underline:hover {
    background-size: 100% 1px;
  }
  ```

---

## 4. Spacing, Borders & Elevation

* **Page Container:** `max-w-7xl mx-auto px-6` (1280px max-width, 24px horizontal padding).
* **Vertical Spacing:**
  * Top hero padding: `pt-14 pb-8` (internal pages) or `pt-20 pb-24 md:pt-28 md:pb-32` (landing page).
  * Section gap: `pb-8`, `pb-10`, `pb-16`, `pb-24`.
  * Grid gap: `gap-4` (compact card grids), `gap-6` (split views), `gap-16` (editorial sections).
* **Border Radii:**
  * Pill / Full: `rounded-full` (9999px) — navigation tabs, buttons, stat badges, status pills.
  * Inputs & Small Cards: `rounded-2xl` (16px) — textareas, file drop zones, individual skill cards.
  * Standard Cards: `rounded-3xl` (24px) — main analytical cards, feature containers.
  * Hero Banners: `rounded-[2.5rem]` (40px) — dark bottom callout banner.
* **Borders:**
  * Solid: `1px solid var(--border)`
  * Dashed: `1px dashed var(--border)` (used for missing skills, unpopulated slots, file upload zone)
* **Shadows:** Flat and subtle; primary separation is achieved through background contrast (`var(--card)` on top of `var(--paper)`) and crisp borders rather than heavy drop shadows.

---

## 5. Global Shell & Navigation

### 5.1 Sticky Header Bar

* **Position:** `sticky top-0 z-50`
* **Styling:** `border-b border-border/70 bg-background/80 backdrop-blur-xl` (translucent parchment with glass blur).
* **Container:** `mx-auto flex max-w-7xl items-center justify-between px-6 py-4`
* **Logo Mark:**
  * Left side anchor pointing to `/`.
  * Circular badge: `grid h-8 w-8 place-items-center rounded-full bg-foreground text-background font-display text-sm` with letter `"S"`.
  * Title text: `font-display text-lg tracking-tight` with `"SkillGraph"` + `<span class="text-muted-foreground">.ai</span>`.
* **Desktop Navigation Links (`hidden md:flex items-center gap-1`):**
  * Route List:
    1. **Dashboard** (`/dashboard`)
    2. **Resume** (`/resume`)
    3. **Skills** (`/skills`)
    4. **GitHub** (`/github`)
    5. **Jobs** (`/jobs`)
    6. **Roadmap** (`/roadmap`)
    7. **Analytics** (`/analytics`)
  * Link Styling: `relative rounded-full px-4 py-1.5 text-sm transition`
  * Active Link State: Inverted solid black pill (`bg-foreground text-background font-medium`).
  * Inactive Link State: `text-foreground/70 hover:text-foreground hover:bg-secondary/60`.
* **Desktop Right Actions:**
  * `Sign in` link to `/auth` (`rounded-full px-4 py-2 text-sm text-foreground/80 hover:text-foreground transition`).
  * `Get started` link to `/auth` (`rounded-full bg-foreground px-5 py-2 text-sm text-background hover:bg-foreground/90 transition`).
* **Mobile Hamburger Toggle (`md:hidden`):**
  * `button class="rounded-full border border-border p-2"`
  * Icons: Hamburger (3 bars, 18px) when closed; Close (`X`, 18px) when opened.
  * Mobile Dropdown Drawer: Slides down over header border, lists all 7 links vertically with `px-4 py-2 text-sm rounded-full hover:bg-secondary`, followed by full-width `Get started` button.

### 5.2 Standard Page Header Primitive (`PageHeader`)

Every authenticated view shares the standard page header component:
```html
<div class="mx-auto max-w-7xl px-6 pt-14 pb-8">
  <div class="flex flex-wrap items-end justify-between gap-6">
    <div>
      <!-- Eyebrow Pill -->
      <p class="mb-3 inline-block rounded-full border border-border bg-card px-3 py-1 text-xs uppercase tracking-widest text-muted-foreground">
        {eyebrow}
      </p>
      <!-- Page Title -->
      <h1 class="font-display text-4xl md:text-5xl leading-[1.05]">
        {title}
      </h1>
      <!-- Subtitle Description -->
      <p class="mt-3 max-w-2xl text-muted-foreground">
        {sub}
      </p>
    </div>
    <!-- Optional Header Action / Status Badge -->
    <div class="flex items-center gap-2">
      {actions}
    </div>
  </div>
  <!-- Divider -->
  <div class="mt-8 h-px w-full bg-border"></div>
</div>
```

### 5.3 Live vs. Demo Source Badge

Present on every analytical view (`resume`, `skills`, `github`, `jobs`, `roadmap`):
* Pill container: `inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground`
* Dot indicator:
  * **Live Mode:** `h-1.5 w-1.5 rounded-full bg-emerald-600 dark:bg-emerald-400` + text `Live`
  * **Demo Mode:** `h-1.5 w-1.5 rounded-full bg-muted-foreground/60` + text `Demo`
  * **Awaiting Data:** `h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse` + text `Live · awaiting data`

---

## 6. Page-by-Page Detailed Inventory

### 6.1 Landing Page (`/`)

* **Hero Section:**
  * Version badge: `rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground` with pulsing amber dot: `v1.0 • Career readiness, mapped.`
  * Heading: `"Know the exact `*`distance`*` between you and the role you want."` (*distance* italicized in muted taupe).
  * Description: `"SkillGraph AI reads your resume, listens to your GitHub, and compares you to real job descriptions. Then it hands you a 6-week roadmap. No vibes. Just signal."`
  * CTA Group:
    * Primary Button: `Start free` + right arrow (`->`) linking to `/auth`.
    * Outline Button: `See a live demo` linking to `/dashboard`.
    * Subtext: `No card. 30-second signup.` (`text-xs text-muted-foreground`).
  * Infinite Marquee Ticker:
    * Bounded by `border-y border-border py-4 overflow-hidden`.
    * Scrolling text: `FastAPI • PostgreSQL • spaCy • Sentence Transformers • scikit-learn • Redis • Docker • HTML5 • Vanilla JS • ` repeated continuously with `@keyframes marquee`.
* **Principle Section:**
  * 3-column grid (`grid md:grid-cols-3 gap-16`):
    * Column 1: Eyebrow `Principle`, Heading `Careers deserve engineering rigor.`
    * Columns 2–3: Editorial explanation contrasting vibes-based checklists with versioned, evidence-backed metric readiness.
* **Feature Grid (6 Cards):**
  * Container: `rounded-3xl border border-border bg-border grid sm:grid-cols-2 lg:grid-cols-3 gap-px overflow-hidden` (1px interior borders created by background peek).
  * Cards:
    1. **Resume parsing:** spaCy + Sentence Transformers extract every skill, tool, and outcome. (Icon: FileText)
    2. **Gap analysis:** Compare yourself to any target role. See exactly what's missing. (Icon: Target)
    3. **GitHub analysis:** Language mix, commit cadence, and project quality — all scored. (Icon: GitHub)
    4. **Roadmaps:** Personalized 6-week plans generated from your gaps and goals. (Icon: Route)
    5. **Progress tracking:** Watch your readiness score climb as you ship. (Icon: TrendingUp)
    6. **Private by default:** JWT auth, encrypted storage, your data never leaves your account. (Icon: ShieldCheck)
  * Hover interaction: Card background transitions to `bg-secondary`, circular icon badge rotates slightly (`group-hover:rotate-6`).
* **Dark Bottom Callout Section:**
  * Container: `rounded-[2.5rem] bg-foreground text-background p-14 md:p-20 relative overflow-hidden`.
  * Background Sparkle Watermark: Opacity 20%, size 200px, positioned top right.
  * Headline: `Stop guessing what to learn next.` (`font-display text-5xl md:text-6xl`).
  * Body: `Get your readiness score in under a minute.`
  * Buttons: `Create your graph` (accent gold pill) and `Explore demo` (outline white border pill).
* **Footer:**
  * Top border `border-t border-border py-8`.
  * Left: `© {year} SkillGraph AI • Paper & Ink edition`
  * Right: Links with `.ink-underline` (`Product` -> `/dashboard`, `Docs`, `GitHub`).

---

### 6.2 Authentication View (`/auth`)

* **Layout:** Two-column split layout (`grid min-h-[calc(100vh-72px)] max-w-6xl grid-cols-1 md:grid-cols-2`).
* **Left Column (Branding & Testimonial - `hidden md:flex flex-col justify-between border-r border-border p-12`):**
  * Top: Eyebrow `Access`, Heading `The graph writes itself.`
  * Bottom: Blockquote in italic muted font: `"Went from 'I have no idea what I'm missing' to a 6-week plan in under a minute."` — *Priya, CS senior*.
* **Right Column (Interactive Form - `flex items-center justify-center p-8 md:p-12`):**
  * Segmented Pill Toggle:
    * Inset container: `rounded-full border border-border p-1 text-sm flex mb-8`.
    * Options: `Sign in` vs `Create account`.
    * Active option has animated dark pill background (`bg-foreground text-background`).
  * Form Elements:
    * Status Banner: Live/Demo source indicator and inline error/spinner alert.
    * `Name` input (visible only when `Create account` is selected): Label `NAME`, Placeholder `Jane Doe`.
    * `Email` input: Label `EMAIL`, Type `email`, Placeholder `you@work.com`, required.
    * `Password` input: Label `PASSWORD`, Type `password`, Placeholder `••••••••`, required.
    * Input Styling: `w-full rounded-full border border-border bg-card px-5 py-3 text-sm outline-none transition focus:border-foreground focus:ring-2 focus:ring-foreground/10`.
    * Submit Button: Full-width pill (`w-full justify-center`), text `Sign in` or `Create account` (or `Working…` while loading).
    * Demo Disclaimer: `Demo mode — no backend configured. Any credentials work.` (`text-center text-xs text-muted-foreground`).

---

### 6.3 Dashboard (`/dashboard`)

* **Header:** Eyebrow `Overview`, Title `Your readiness graph.`, Subtitle `A single view of where you stand, what's missing, and what to ship next.`, Action: `Update resume ->` button linking to `/resume`.
* **KPI Stats Grid (`grid md:grid-cols-4 gap-4 pb-10`):**
  1. `Readiness`: Value `78%`, Delta `+7 this month`
  2. `Skills tracked`: Value `10`
  3. `GitHub commits (12mo)`: Value `1,284`
  4. `Roles compared`: Value `4`
* **Charts Section (`grid lg:grid-cols-5 gap-4 pb-10`):**
  * **Card 1 (Left 3 cols) — Readiness Trajectory:**
    * Heading: `Readiness trajectory`, Subtext: `Rolling monthly score across all target roles.`
    * Chart: Height 288px (`h-72`). Smooth monotone area chart with gradient fill (`var(--ink)` 35% opacity to 0% opacity). X-axis: 7 months (`Jan` to `Jul`), Y-axis: score (0 to 100).
  * **Card 2 (Right 2 cols) — Skill Radar:**
    * Heading: `Skill radar`, Subtext: `You vs. target role median.`
    * Chart: Height 288px (`h-72`). 6-axis spider/radar chart. Axes: `Frontend`, `Backend`, `ML`, `DevOps`, `System Design`, `Testing`.
    * Polygon 1: "You" (stroke `var(--ink)`, fill `var(--ink)` at 18% opacity).
    * Polygon 2: "Target" (stroke `var(--accent)`, fill `var(--accent)` at 10% opacity).
* **Target Roles Grid (`grid md:grid-cols-3 gap-4 pb-16`):**
  * Displays top 3 roles: `ML Engineer` (71%), `Full-Stack Engineer` (83%), `AI Product Engineer` (76%).
  * Card elements: Eyebrow `Target`, Title `role`, Progress bar (`h-2 rounded-full bg-secondary`, fill `bg-foreground`), missing badges: `missing: {skill}` (`rounded-full border border-border bg-secondary px-2.5 py-1 text-xs`).
* **Quick Navigation Cards (`grid md:grid-cols-3 gap-4 pb-24`):**
  * 3 interactive link cards:
    1. `Parse resume` -> `/resume` ("Extract every skill.")
    2. `Analyze GitHub` -> `/github` ("Signal from your code.")
    3. `Match a job` -> `/jobs` ("Score any JD in seconds.")
  * Hover effect: Card background turns to `var(--secondary)`, icon rotates 6 degrees, right arrow fades in.

---

### 6.4 Resume Parsing View (`/resume`)

* **Header:** Eyebrow `Ingest`, Title `Feed the graph.`, Subtitle `Drop a PDF or DOCX. We extract skills, tools, and outcomes with spaCy + Sentence Transformers.`
* **Main Grid (`grid lg:grid-cols-5 gap-4 pb-16`):**
  * **Upload Card (Left 3 cols):**
    * Source badge at top right.
    * Drag & Drop Zone: `flex min-h-[280px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 text-center transition`.
    * Drag-over active state: `border-foreground bg-secondary`.
    * Upload Icon: Circular badge `h-14 w-14 bg-foreground text-background` with cloud upload icon.
    * Heading: `Drop your resume` (or selected file name).
    * Subtitle: `PDF, DOCX or TXT • up to 5MB`.
    * Hidden file input accepting `.pdf, .docx, .txt`.
    * Action Row: `Clear` (ghost button if file chosen) + `Parse resume` / `Parsing…` / `Re-parse` (primary button).
  * **Pipeline Card (Right 2 cols):**
    * Title: `Pipeline`
    * Ordered steps with monospace indices:
      * `01` **Text extraction:** `pdfplumber / python-docx`
      * `02` **NER + normalization:** `spaCy pipeline, custom entity ruler`
      * `03` **Embeddings:** `Sentence Transformers all-MiniLM-L6-v2`
      * `04` **Skill scoring:** `cosine similarity vs. skill ontology`
* **Extracted Skills Results Section (`pb-24`):**
  * Header: Icon FileText + `Extracted skills` + Source badge.
  * Grid: `grid md:grid-cols-2 lg:grid-cols-3 gap-3`.
  * Skill Card: `rounded-2xl border border-border bg-card p-4`
    * Skill name (`font-medium`) + Category pill (`rounded-full bg-secondary px-2 py-0.5 text-xs`).
    * Progress bar: `mt-3 h-1.5 w-full bg-secondary rounded-full`, fill `bg-foreground`.
    * Percentage readout: `font-mono text-xs text-muted-foreground text-right`.

---

### 6.5 Skills Gap Analysis (`/skills`)

* **Header:** Eyebrow `Analysis`, Title `Skill gap, laid bare.`, Subtitle `Pick a target role. See what's present, what's missing, and how far away you are.`
* **Role Selector Bar (`pb-8`):**
  * Pill buttons for all configured roles (`ML Engineer`, `Full-Stack Engineer`, `AI Product Engineer`, `Backend Engineer`).
  * Selected state: `border-foreground bg-foreground text-background`.
  * Unselected state: `border-border bg-card hover:border-foreground`.
* **Readiness & Present Skills Grid (`grid lg:grid-cols-5 gap-4 pb-10`):**
  * **Readiness Score Card (Left 2 cols):**
    * Eyebrow `Readiness`
    * Huge readout: `font-display text-7xl` (e.g. `71`) + `<span class="text-4xl text-muted-foreground">%</span>`.
    * Progress bar: `h-2 rounded-full bg-secondary`, fill `bg-foreground`.
    * Target role label.
    * Action buttons: `Generate roadmap` (primary) + `Export report` (outline).
  * **Present Skills Card (Right 3 cols):**
    * Heading: `Present skills`.
    * Chart: Horizontal bar chart (`height: 288px`). Bars oriented horizontally with skill name on Y-axis (width 100px), score level bar fill `var(--ink)` with rounded right end `radius: [0, 999, 999, 0]`.
* **Missing Skills Grid (`pb-24`):**
  * Heading: `What's missing for {role}`.
  * Grid: `grid md:grid-cols-2 lg:grid-cols-4 gap-3`.
  * Missing Skill Card: `rounded-2xl border border-dashed border-border p-5`.
    * Skill title: `font-display text-xl` (e.g. `MLOps`, `PyTorch`, `Kubernetes`, `Airflow`).
    * Subtitle: `High-signal missing skill` (`text-xs text-muted-foreground`).
    * Accent indicator: `h-1 rounded-full bg-secondary`, fill `h-full bg-accent`.

---

### 6.6 GitHub Analysis (`/github`)

* **Header:** Eyebrow `Signal`, Title `Your GitHub, quantified.`, Subtitle `Repos, commit cadence, language mix, and quality signals — all scored.`
* **Username Input Card (`pb-10`):**
  * Header row: Source badge + detected username.
  * Form row: Pill container with GitHub icon, fixed prefix `github.com/`, text input for username, submit button `Analyze` / `Analyzing…`.
* **Metrics Grid (`grid md:grid-cols-4 gap-4 pb-10`):**
  * 4 KPI cards: `Public repos`, `Total stars`, `Commits (12mo)`, `Followers`.
* **Cadence & Language Grid (`grid lg:grid-cols-5 gap-4 pb-10`):**
  * **Commit Cadence Card (Left 3 cols):**
    * Heading: `Commit cadence (26 wk)` with commit horizontal icon.
    * Chart: Height 288px. Vertical bar chart with 26 weekly bars (`W1` through `W26`), fill `var(--ink)`, top rounded corners (`radius: [999, 999, 0, 0]`).
  * **Language Mix Card (Right 2 cols):**
    * Heading: `Language mix`.
    * Chart: Height 288px. Donut pie chart (`innerRadius: 55, outerRadius: 95, paddingAngle: 2`).
    * Color Pills Legend: Dot color indicator + language name + percentage (e.g. `Python 41%`, `TypeScript 28%`).
* **Quality Signals Section (`pb-24`):**
  * Heading: `Quality signals`.
  * Subtitle: `Derived from repo topics, README quality, test presence, and PR review activity.`
  * 3 Metric Cards (`grid md:grid-cols-3 gap-4`):
    * `Documentation`: 82 / 100
    * `Test coverage`: 61 / 100
    * `Collaboration`: 74 / 100
    * Each with a progress bar indicator.

---

### 6.7 Job Description Matching (`/jobs`)

* **Header:** Eyebrow `Match`, Title `Score any job description.`, Subtitle `Paste the JD. We embed both sides and score alignment area by area.`
* **Input & Overall Score Grid (`grid lg:grid-cols-5 gap-4 pb-10`):**
  * **Input Card (Left 3 cols):**
    * Source badge.
    * Label: `JOB DESCRIPTION` (`text-xs uppercase tracking-widest text-muted-foreground`).
    * Textarea: `h-72 w-full resize-none rounded-2xl border border-border bg-card p-4 text-sm outline-none focus:border-foreground`.
    * Bottom bar: Character counter (`X chars`) + `Analyze` button with sparkle icon (`Scoring…` when active).
  * **Score Card (Right 2 cols):**
    * Centered layout.
    * Eyebrow: `Overall match`.
    * Huge numeral: `font-display text-8xl` with `—` or `82%`.
    * Target Role label: `Senior Backend Engineer @ Acme` (or placeholder).
* **Match Breakdown Results (`pb-24`):**
  * **Area Breakdown Card:**
    * Heading: `Area breakdown`.
    * 5 Horizontal category bars:
      1. `Core language` (92%)
      2. `Frameworks` (84%)
      3. `Data stores` (78%)
      4. `Infra / DevOps` (61%)
      5. `System design` (55%)
    * Each area displays name, mono percentage, and animated fill bar.
  * **Matched vs. Missing Skills (2 columns - `grid md:grid-cols-2 gap-4`):**
    * **Matched Card:** Checkmark icon + `Matched` header. Solid dark pills (`rounded-full bg-foreground text-background px-3 py-1 text-xs`): `Python`, `FastAPI`, `PostgreSQL`, `Redis`, `REST`.
    * **Missing Card:** X/dash icon + `Missing` header. Dashed border pills (`rounded-full border border-dashed border-border px-3 py-1 text-xs`): `Kafka`, `gRPC`, `Terraform`.

---

### 6.8 6-Week Learning Roadmap (`/roadmap`)

* **Header:** Eyebrow `Plan`, Title `Six weeks to ready.`, Subtitle `Your learning plan and completed milestones.`, Action: Source badge.
* **Goal Input Form (`pb-6`):**
  * Target role input field (default: `ML Engineer`) + `Generate roadmap` / `Regenerate` button with sparkle icon.
* **Progress Overview Card (`pb-8`):**
  * Heading: `Progress` (`text-xs uppercase tracking-widest text-muted-foreground`).
  * Big percentage: `font-display text-4xl` (e.g. `22%`).
  * Subtext: `k of O tasks complete` (e.g. `4 of 18 tasks complete`).
  * Progress Bar: `h-2 rounded-full bg-secondary`, fill `bg-foreground`.
* **Vertical Timeline (`pb-24`):**
  * Relative container with vertical rail line: `absolute left-6 top-2 bottom-2 w-px bg-border md:left-8`.
  * Week Blocks (`space-y-6`):
    * Circular Week Badge: Anchored on the rail: `absolute left-0 top-2 grid h-12 w-12 place-items-center rounded-full border border-border bg-card font-display text-lg md:h-16 md:w-16 md:text-xl`: `W1`, `W2`, `W3`, `W4`, `W5`, `W6`.
    * Content Card: Indented (`pl-14 md:pl-20`).
      * Header: Week focus name (`Foundations`, `Data layer`, `ML services`, `APIs + Auth`, `MLOps`, `Polish`) + Task count badge (`3 tasks`).
      * Task Checklist:
        * Interactive checkbox: `input type="checkbox"` (`accent-primary`).
        * Text label: Strikethrough and muted when done (`line-through text-muted-foreground`).
        * Real-time saving indicator: Spinner with `Saving progress…`.

---

### 6.9 Analytics View (`/analytics`)

* **Header:** Eyebrow `Analytics`, Title `Signals over time.`, Subtitle `Every score in one place. Everything trends — because progress is a metric, not a mood.`
* **KPI Metrics Grid (`grid md:grid-cols-4 gap-4 pb-8`):**
  1. `Avg readiness`: `78%`, Delta: `+36 since Jan`
  2. `Skills learned`: `14`, Delta: `+3 this month`
  3. `Projects shipped`: `6`
  4. `Roadmap streak`: `24d`, Delta: `Personal best`
* **Charts Section (`grid lg:grid-cols-5 gap-4 pb-8`):**
  * **Readiness Over Time (3 cols):** Line chart (height 320px) with solid line `stroke: var(--ink)`, width 2.5px, and filled circular data points (`r: 4, fill: var(--ink)`).
  * **Top Skills (2 cols):** Bar chart (height 320px) with vertical bars showing top skills and level scores.
* **Activity Log Table (`pb-24`):**
  * Heading: `Activity log`.
  * Chronological list separated by `divide-y divide-border`:
    * Date (`font-mono text-xs text-muted-foreground w-16`)
    * Action description (`flex-1 font-medium`)
    * Result delta (`text-xs text-muted-foreground`)
    * Examples: `Jul 12` | `Parsed resume v3.pdf` | `+2 skills detected`; `Jul 01` | `Readiness recalculated` | `71% -> 78%`.

---

### 6.10 Recommended Projects View (`/projects`)

* **Header:** Eyebrow `Build`, Title `Ship what matters.`, Subtitle `Every project is picked to close a specific gap in your target readiness.`
* **Projects Grid (`grid md:grid-cols-2 gap-4 pb-24`):**
  * 4 Project Cards:
    1. **Realtime resume-to-role matcher** (Intermediate, 18h, `FastAPI`, `spaCy`, `Sentence Transformers`)
    2. **MLOps pipeline: train -> serve -> monitor** (Advanced, 32h, `Docker`, `MLflow`, `Kubernetes`)
    3. **GitHub contribution analyzer CLI** (Beginner, 8h, `Python`, `GitHub API`, `Click`)
    4. **Vector-search knowledge base** (Intermediate, 14h, `pgvector`, `Sentence Transformers`, `FastAPI`)
  * Card elements:
    * Difficulty Badge:
      * `Beginner`: `bg-secondary text-foreground`
      * `Intermediate`: `bg-foreground text-background`
      * `Advanced`: `bg-accent text-accent-foreground`
    * Impact description: Explains exactly which career gap this project closes.
    * Monospace Skill Tags: `rounded-full border border-border bg-secondary px-2.5 py-1 text-xs font-mono`.
    * Footer Row: Estimated duration `~Xh` with clock icon + `Start` outline button with zap icon.

---

## 7. Responsive Breakpoints & States

| Breakpoint | Width | Layout Adjustments |
| :--- | :--- | :--- |
| **Mobile (`< 640px`)** | Fluid | Single column layouts; 4 KPI stats collapse to single column or 2x2; mobile hamburger menu active; charts resize via SVG `viewBox`. |
| **Tablet (`md: >= 768px`)** | 768px | Header shows desktop nav; KPI cards expand to 4 columns; split auth view shows left testimonial column; projects grid becomes 2 columns. |
| **Desktop (`lg: >= 1024px`)** | 1024px | 5-column dashboard chart grid activates (3 cols trajectory / 2 cols radar); skills gap analysis splits 2 cols readiness / 3 cols bar chart; job matcher splits 3 cols textarea / 2 cols score. |
| **Wide (`xl: >= 1280px`)** | 1280px | Content capped at `max-w-7xl` (1280px) centered with `px-6`. |

---

## 8. Micro-Interactions & Transitions

* **Pill Navigation Shift:** Active tab pill has spring-like smooth repositioning or clean opacity transition.
* **Marquee Ticker:** Linear continuous scroll from right to left (`animation: marquee 25s linear infinite`).
* **Progress Bar Fill:** Animated width fill on card mount / scroll-into-view (`transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1)`).
* **Hover Scale & Rotate:** Circular icons rotate 6 degrees on card hover (`group-hover:rotate-6 transition-transform`).
* **Buttons Active State:** Micro-scale tap feedback (`active:scale-[0.97]`).
* **Checklist Strikethrough:** Smooth text-decoration and opacity change when completing roadmap tasks.


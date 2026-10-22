---
name: SIMS
description: Student register for a Ukrainian dean's office, built as a visible-edge card file
colors:
  enamel-rail: "oklch(0.32 0.038 165)"
  rail-active: "oklch(0.42 0.05 165)"
  rail-foreground: "oklch(0.96 0.012 165)"
  rail-muted: "oklch(0.8 0.03 165)"
  primary: "oklch(0.42 0.065 165)"
  primary-foreground: "oklch(0.985 0.005 165)"
  ring: "oklch(0.52 0.09 165)"
  ground: "oklch(0.966 0.009 165)"
  strip: "oklch(0.925 0.018 165)"
  card: "oklch(1 0 0)"
  ink: "oklch(0.23 0.022 165)"
  muted-ink: "oklch(0.46 0.022 165)"
  secondary: "oklch(0.93 0.014 165)"
  muted: "oklch(0.94 0.012 165)"
  accent: "oklch(0.92 0.022 165)"
  border: "oklch(0.875 0.014 165)"
  input: "oklch(0.84 0.016 165)"
  destructive: "oklch(0.53 0.19 27)"
  course-1: "oklch(0.83 0.085 250)"
  course-2: "oklch(0.85 0.11 150)"
  course-3: "oklch(0.88 0.12 95)"
  course-4: "oklch(0.83 0.1 45)"
  course-5: "oklch(0.83 0.08 305)"
  course-6: "oklch(0.85 0.075 200)"
  course-ink: "oklch(0.25 0.03 165)"
  signal-academic: "oklch(0.55 0.2 27)"
  signal-tuition: "oklch(0.74 0.16 72)"
  signal-leave: "oklch(0.55 0.16 305)"
  signal-expelled: "oklch(0.5 0.02 250)"
  signal-graduated: "oklch(0.52 0.09 235)"
  signal-fresh: "oklch(0.7 0.17 140)"
typography:
  display:
    fontFamily: "Geist Variable, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Geist Variable, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Geist Variable, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.375
  section:
    fontFamily: "Geist Variable, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.5
  body:
    fontFamily: "Geist Variable, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "\"cv11\", \"ss01\", \"tnum\""
  label:
    fontFamily: "Geist Variable, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.33
  cipher:
    fontFamily: "Geist Mono Variable, ui-monospace, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    letterSpacing: "-0.025em"
rounded:
  sm: "0.225rem"
  md: "0.3rem"
  lg: "0.375rem"
  xl: "0.525rem"
spacing:
  hairline: "3px"
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  gutter: "24px"
  control: "32px"
  row: "40px"
  rail: "232px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.lg}"
    padding: "0 10px"
    height: "32px"
    typography: "{typography.body}"
  button-outline:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "0 10px"
    height: "32px"
  button-outline-hover:
    backgroundColor: "{colors.muted}"
  button-ghost-hover:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.ink}"
  input:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "4px 10px"
    height: "32px"
  nav-item:
    textColor: "{colors.rail-muted}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
  nav-item-active:
    backgroundColor: "{colors.rail-active}"
    textColor: "{colors.rail-foreground}"
  chip-course:
    backgroundColor: "{colors.card}"
    textColor: "{colors.muted-ink}"
    rounded: "{rounded.md}"
    height: "32px"
    width: "32px"
  chip-course-active:
    backgroundColor: "{colors.course-2}"
    textColor: "{colors.course-ink}"
  course-tab:
    backgroundColor: "{colors.course-1}"
    textColor: "{colors.course-ink}"
    rounded: "{rounded.sm}"
    padding: "1px 6px"
    typography: "{typography.label}"
  course-tab-raised:
    backgroundColor: "{colors.course-4}"
    textColor: "{colors.course-ink}"
    padding: "4px 12px 6px"
    typography: "{typography.label}"
  signal-clip:
    backgroundColor: "{colors.signal-academic}"
    width: "8px"
    height: "16px"
  register-row:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    height: "40px"
  register-row-selected:
    backgroundColor: "{colors.accent}"
  filter-strip:
    backgroundColor: "{colors.strip}"
    padding: "12px 24px"
  pulled-card:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.md}"
    width: "24rem"
  demo-mark:
    backgroundColor: "{colors.signal-tuition}"
    textColor: "{colors.course-ink}"
    rounded: "{rounded.sm}"
    padding: "1px 6px"
---

# Design System: SIMS

## Overview

**Creative North Star: "The Visible-Edge Card File"**

The register is a Kardex cabinet seen from the front. Every row is the exposed margin of one student's card; state is not written in a status column for the eye to parse, it is clipped onto that margin as small flat metal signals, so red academic debt and amber tuition debt are spotted down a column of 252 names without reading. Pulling a card is the system's one gesture: a white card with a coloured index tab slides out beside a register that stays live.

The scene is a daytime office under fluorescent light. A deep cabinet-enamel green rail owns the left edge as a field of colour, a pale cool-green working ground carries the page, a second neutral layer (the filter strip) holds the sorting controls, and white cards carry records. Colour commits whole regions or codes facts; it is never sprinkled. Density is high and deliberate: 14px body, 32px controls, 40px rows, tabular figures throughout, because staff work in it all day beside Word and Excel.

The system rejects the grey dashboard of KPI cards over a stock table. There is no hero, no metric tiles, no decorative imagery; the only illustration is the authored favicon, a card with a red clip.

**Key Characteristics:**
- One hue family (green-grey, hue 165) for every neutral and the primary; course and signal hues are the only other colours.
- Signals are flat single-fill clips (8x16), clipped to a register row's top edge, inline elsewhere.
- Six index-tab hues code courses 1 to 6, identically in the filter, the table and the pulled card.
- Flat at rest; lift appears only on a card that has been pulled out of the file.
- Geist for all UI, Geist Mono only for ciphers and document numbers.

## Colors

A single cool green-grey family in four layers (rail, ground, strip, card), plus two closed code sets: six pastel course hues and six saturated signal hues.

### Primary
- **Cabinet Enamel** (`enamel-rail`): the left rail, full height, as a field rather than an accent. Its active nav item steps up to **Enamel Lit** (`rail-active`); rail text is **Rail Paper** (`rail-foreground`) with secondary text in **Rail Sage** (`rail-muted`). Dialog and sheet overlays tint with this colour at 15 to 20 percent, never blur.
- **Ledger Green** (`primary`): the single filled action per view ("Додати студента", "Відкрити картку"), the text caret, and the source of the focus ring (`ring`).

### Secondary
- **Index-Tab Pastels** (`course-1` to `course-6`): blue, green, yellow, orange, violet, cyan at high lightness; one per course. Text on them is always **Tab Ink** (`course-ink`). A missing course falls back to `muted`.

### Tertiary
- **Metal Signals**: **Signal Red** (`signal-academic`) academic debt; **Signal Amber** (`signal-tuition`) tuition debt; **Signal Violet** (`signal-leave`) academic leave; **Signal Slate** (`signal-expelled`) expelled; **Signal Steel Blue** (`signal-graduated`) graduated; **Signal Fresh Green** (`signal-fresh`) a record changed this session, drawn hollow (card fill, 1.5px green stroke) until opened.

### Neutral
- **Pale Cabinet Ground** (`ground`): page background and sticky table header.
- **Strip Sage** (`strip`): the filter strip, a second neutral layer between header and register, bordered top and bottom.
- **Card White** (`card`): register rows, cards, controls set on the strip.
- **Office Ink** (`ink`) for text; **Faded Ink** (`muted-ink`) for labels, meta and column headers.
- **Hairline** (`border`) dividers and row rules (rows at 70 percent); **Input Edge** (`input`) control borders.
- **Hover Wash** (`accent`): row hover at 60 percent, focus at 70 percent, the selected (pulled) row at full.
- **Error Red** (`destructive`): form errors and failed loads only.

### Named Rules
**The Closed Code Rule.** Course hues mean a course and signal hues mean a state. Neither set is used for decoration, charts, category tags or emphasis anywhere else.

**The Field Not Accent Rule.** The rail and the filter strip are coloured regions; the primary green fills at most one action per view.

## Typography

**Display Font:** Geist Variable (with system-ui), self-hosted with Cyrillic subsets
**Label/Mono Font:** Geist Mono Variable (with ui-monospace)

**Character:** A neutral grotesk set small and dense, with `cv11` and `ss01` on and tabular figures in every table; the mono face appears only where a code is read character by character.

### Hierarchy
- **Display** (600, 1.5rem, 1.25, -0.025em): the person or group name on a full card.
- **Headline** (600, 1.375rem, 1.25, -0.025em): page titles ("Студенти"), with a 14px muted record count below.
- **Title** (600, 1.125rem, 1.375): the name on a pulled card.
- **Section** (600, 1rem): section titles inside card tabs.
- **Body** (400, 0.875rem, 1.45): everything else, tables included. Muted hints cap at 46 to 60ch.
- **Label** (500, 0.75rem): field labels, filter legends, column headers, course tabs. Sentence case.
- **Cipher** (400, 0.8125rem mono, -0.025em): group ciphers (`6.G19.26-з`), record-book and document numbers.

### Named Rules
**The Cipher Rule.** Mono is for codes only. Names, money, dates and labels stay in Geist with tabular figures.

**The Printed Form Rule.** Money reads as on Ukrainian forms: `10 000,00 ₴` with plain-space grouping; a zero or absent debt renders as "—", never "0,00 ₴".

## Layout

A two-column shell: a sticky 232px rail at full viewport height and a fluid main column. Main content runs on a 24px gutter: page header (24px top, 16px bottom, title left, search and primary action right, wrapping), then the full-bleed filter strip (12px vertical), then the register edge to edge, then the pager. The filter strip is an auto-fill grid of 10.5rem minimum tracks with 12px column and 10px row gaps; specialty, course chips and the debt toggles span two tracks. Rows are 40px, header cells 36px, controls 32px. `html` reserves a stable scrollbar gutter so the layout never shifts when a list grows.

Below 768px the rail becomes a static top band: wordmark, demo mark, and the nav as a four-column grid of icon-over-label items; the year block hides. The filter strip collapses behind a full-width «Фільтри (n)» button that discloses a single-column stack. The register scrolls horizontally rather than dropping columns. The search box goes full width below 640px.

## Elevation & Depth

Flat by default. Depth is carried by tonal layers (rail, ground, strip, card) and hairlines. Shadow appears only on a card that has left the file: the pulled side card, the lifted header card on full student and group pages, and the raised index tab standing above them. All lift shadows are tinted with the rail hue, not grey. Overlays tint the page; nothing is blurred.

### Shadow Vocabulary
- **Pulled card** (`box-shadow: 0 14px 36px -10px oklch(0.2 0.03 165 / 0.38), 0 2px 6px oklch(0.2 0.03 165 / 0.12)`): the side card pulled from a register row.
- **Card on desk** (`box-shadow: 0 8px 24px -12px oklch(0.2 0.03 165 / 0.3), 0 1px 3px oklch(0.2 0.03 165 / 0.1)`): the header card of a full student or group page.
- **Raised tab** (`box-shadow: 0 -1px 2px oklch(0 0 0 / 0.08)`): the index tab above a lifted card.
- **Tab edge** (`box-shadow: inset 0 -3px 0 <course hue>`): an inactive course chip keeps its hue on its lower edge.
- **Pressed tab** (`box-shadow: inset 0 -2px 0 oklch(0 0 0 / 0.12)`): an active, filled course chip.

### Named Rules
**The Pulled Card Rule.** Only a card that has been taken out of the file casts a shadow. Rows, the strip, tables and panels in place stay flat.

## Shapes

Small, office-grade corners from one radius (6px): controls and buttons at 6px, cards, chips and nav items at 4.8px, inline course tabs and the demo mark at 3.6px, dialogs at 8.4px. A lifted card squares off its top-left corner where its index tab joins it, and the raised tab rounds only its top corners, so tab and card read as one silhouette. The signal clip is a flat 8x16 bar with 1px-rounded lower corners; on a register row it sits at the row's top edge (offset 1px up, 24px in) as if folded over the card. The debt toggle carries the same bar shape at 8x14.

## Components

### Buttons
Restrained and compact; one filled action per view.
- **Shape:** 6px corners, 32px tall, 10px horizontal padding, 16px Lucide icon leading.
- **Primary:** Ledger Green fill, near-white text; hover drops to 80 percent.
- **Outline:** ground fill, hairline border; hover to `muted`. Used for secondary card actions (Редагувати, Змінити статус, Перевести, Картка PDF).
- **Ghost:** no fill until hover; used for reset and close.
- **Focus:** 2px ring-coloured outline with 2px offset globally; shadcn primitives add a 3px ring halo at 50 percent.

### Chips
Course chips are index tabs, not pills.
- **Style:** 32px square (the "Усі" chip padded wider), 4.8px corners, card fill at 60 percent with Input Edge border and Faded Ink numerals.
- **State:** inactive chips keep a 3px inner lower edge in their course hue; the active chip fills with the hue, drops the border, sets Tab Ink, and takes the pressed inner edge. Selecting the active chip again clears the filter.
- **Debt toggles** (Академборг, Фінборг): outline chips carrying their signal bar at 55 percent opacity; pressed sets the bar solid, the card fill and a darker border.

### Cards / Containers
- **Corner Style:** 4.8px, top-left squared under a raised tab.
- **Background:** Card White on the ground.
- **Shadow Strategy:** see The Pulled Card Rule.
- **Border:** internal sections divided by hairlines; tables in place use a hairline border instead of shadow.
- **Internal Padding:** 20px horizontal, 14px vertical sections on the pulled card; 24px by 20px on the full-page header card.

### Inputs / Fields
- **Style:** 32px, 6px corners, Input Edge border, card fill when on the strip or a form. Labels are the Label style above the control with a 4px gap.
- **Focus:** ring border plus ring halo.
- **Error:** destructive border and halo; a 12px destructive message replaces the hint.

### Navigation
- **Rail nav:** 14px items, 8px by 12px, 4.8px corners, Rail Sage text with a 16px icon; hover washes with Enamel Lit at 60 percent; active fills Enamel Lit with Rail Paper medium text. The current academic year sits at the rail foot above a translucent hairline.
- **Mobile:** four-column icon-over-label grid, 12px labels.
- **Card tabs:** shadcn segmented tabs on `muted`, the active segment on the ground with a small shadow.

### Signal Margin (signature)
The first register column (56px) holds a row's signals in a 3px-gapped run, fresh mark first. Clipped to the row top in the register, inline beside labels on the pulled card, full card and group lists. The run carries one accessible label listing every signal; the pulled card repeats each clip beside its written meaning.

### Pulled Card (signature)
Clicking a row, or Space, pulls its card: a fixed 24rem aside 80px from the top and 20px from the right, entering with a 200ms ease-out fade and 1.5rem slide from the right, its raised course tab leading. It is non-modal, with no backdrop: the register stays live and the row stays highlighted. ↑/↓ on the rows flips to the neighbouring card, Enter on the open row opens the full card, Esc puts it back. Contents: name and cipher, signals with their meanings, a status/funding/record-book list, "Відкрити картку" and "Картка PDF".

### Demo Mark
Synthetic grades, debts, contracts and curators must never pass for real ones. When `GET /api/meta` reports demo data, an amber tag with a flask icon («Демо-дані», 11px semibold) appears at the rail foot (solid amber), in the mobile rail band, and beside each synthetic fact (amber at 25 percent). Absent otherwise.

## Do's and Don'ts

### Do:
- **Do** derive every new neutral from hue 165 and place it in the rail, ground, strip, card layering.
- **Do** show a record's state as signal clips in its margin, each clip also named in text or an accessible label.
- **Do** use the course hue as an index tab wherever a course is shown, in Tab Ink.
- **Do** set ciphers and document numbers in Geist Mono at 0.8125rem, and everything numeric in tabular figures.
- **Do** render an absent or zero debt as "—" and money as `10 000,00 ₴`.
- **Do** keep controls at 32px and register rows at 40px.
- **Do** label every surface that shows synthetic data with the Demo Mark.

### Don't:
- **Don't** build KPI-card dashboards over a stock table; the register is the home screen.
- **Don't** use course or signal hues for decoration, charts, category tags or emphasis.
- **Don't** give in-place surfaces (rows, strip, tables, panels) a shadow; lift belongs to a pulled card.
- **Don't** blur the page behind overlays; tint it with the rail colour.
- **Don't** set names, labels or money in the mono face.
- **Don't** put small uppercase eyebrow labels above headings; labels are sentence case.

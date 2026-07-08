---
name: rewst-slides
description: >-
  Build on-brand Rewst presentations — slide decks, pitch decks, corporate
  presentations — that match the Rewst style guide exactly and export to PDF and
  PowerPoint. Use this skill whenever someone wants to create, build, draft, or
  put together a presentation, deck, slides, or pitch for Rewst, or asks to turn
  notes / a doc / a topic into a Rewst presentation, or wants an existing deck
  redone in Rewst branding. Triggers even when they don't say the word "deck" —
  e.g. "make slides for the QBR," "I need something for the customer webinar,"
  "put together a roadmap presentation." Owns brand fidelity: the Rewst palette
  (Bot Teal #00BBB4 as the anchor), Poppins/Montserrat type, logo usage, voice,
  and the rule that primary Bot Teal appears on every slide.
---

# Rewst Deck

Build a presentation that looks like Rewst made it — and prove it did, slide by
slide. The deck is authored as a self-contained HTML file (the source of truth),
then exported to PDF and PPTX. Brand consistency comes first; the exports follow
from it.

## How the pieces fit

- `assets/deck-template.html` — the starting deck: 16 archetypes + light
  variants, brand CSS wired in, placeholder copy in `[brackets]`.
- `assets/deck.css`, `assets/deck-stage.js`, `assets/design-system/`,
  `assets/logo/`, `assets/illustrations/` — the brand kit the HTML depends on.
- `references/brand.md` — palette, type, logo, voice, the Bot Teal rule.
- `references/slides.md` — what each archetype is for and where teal lives.
- `scripts/deck.py` — `check` (verify Bot Teal, right margin, box padding, and
  footers per slide) and `export` (one command writes the full set: `.pdf`,
  `-editable.pptx`, and `-html.zip`).

## Workflow

### 1. Read the two references first
Open `references/brand.md` and `references/slides.md` before writing anything.
They define the palette, voice, archetypes, and the one hard rule. Don't author
from memory of "teal-ish corporate decks" — the specifics matter.

### 2. Set up a working copy
Create a deck folder in the output area and copy the kit so the deck's relative
asset paths resolve:

```bash
mkdir -p /mnt/user-data/outputs/<deckname>
cd /mnt/user-data/outputs/<deckname>
for item in deck.css deck-stage.js design-system logo illustrations fonts; do
  cp -r <skill>/assets/"$item" .
done
cp <skill>/assets/deck-template.html ./<deckname>.html
```

Everything (`deck.css`, `design-system/`, `logo/`, `illustrations/`) sits beside
the HTML — keep it that way so the deck stays portable.

### 3. Author the deck
Work inside `<deckname>.html`:
- **Choose archetypes** from `references/slides.md` that fit the content. Fill
  the `[bracketed]` placeholders. Delete sections you don't need; this is a kit,
  not a fixed 16-slide deck. **Always open with the `s-title` slide** and keep
  its bleed-Stewart treatment — that tone-on-tone silhouette is the brand's
  signature opener. Use the default Bot Teal field, or `class="s-title on-deep"`
  for the Bot Teal Deep field (see slides.md for the logo/pageno swap).
- **Write in Rewst's voice** (brand.md): active, specific, outcome-led, no
  jargon. Sentence-case titles as full sentences. Three points beat four.
- **Stay in palette, solid fills, no gradients.** Anchor each layout in Bot
  Teal. Use Trigger Amber only for genuine CTAs and the section dividers.
- **Respect the right margin.** Keep content within the ~110px right gutter; the
  only thing allowed to bleed past it is the single-color Stewart on title and
  section/header slides. Don't move the footers.
- **Logo per background:** `rewst-logo-ondark.png` on dark, `rewst-logo.png` on
  light. Never alter it.
- **Keep the chrome honest:** update each `.pageno` (e.g. `04 / 16` → `04 / 08`)
  and keep the `#speaker-notes` JSON array the same length and order as the
  slides you keep — the exporter maps note `N` to slide `N`.
- Leave `deck-stage.js` wired up and leave the footer Bot Teal dot rule in
  `deck.css` in place.

### 4. The Bot Teal rule — primary `#00BBB4` on every slide
This is the brand rule the team added and the thing this skill exists to
guarantee. It holds automatically: most archetypes carry teal in their accents,
and a small Bot Teal indicator dot is baked into the footer of every slide
(including any you add). So in normal authoring you don't have to do anything
special — just don't strip the dot, and don't recolor accents off-teal.

If you build a genuinely custom slide, give it a real `#00BBB4` element (an
eyebrow, indicator, or teal surface) so the color anchors the layout rather than
relying on the dot alone.

### 5. Check before exporting
```bash
python <skill>/scripts/deck.py check /mnt/user-data/outputs/<deckname>/<deckname>.html
```
This renders every slide in a real browser and verifies these rules:
1. **Bot Teal** — at least one element in exact `#00BBB4` is present.
2. **Right margin** — no content paints past the 110px right gutter (the bleed
   Stewart and the footers are exempt). This catches cards, tables, or columns
   that creep to the edge before they ship.
3. **Box padding** — every content box/card keeps at least `--box-pad-min`
   (32px) of internal padding, so text never touches a card edge (small chips,
   badges, avatars, and table cells are exempt).
4. **Footers** — every slide shows the Rewst logo bottom-left and the slide
   number bottom-right (never swapped, moved, or hidden).
5. **Retired teal** — the deck's own source (its HTML and `deck.css`) must not
   contain the retired `#1EAFAF` / `#1CAFAF`. (Illustration SVGs are external and
   aren't scanned — their internal legacy teal is left as-is by design.)

A `FAIL` is a real defect — fix it and re-run until everything passes. Don't
export a deck that fails.

### 6. Export — one command produces the whole set
```bash
python <skill>/scripts/deck.py export /mnt/user-data/outputs/<deckname>/<deckname>.html \
    --out /mnt/user-data/outputs/<deckname>/<deckname>
```
A single `export` (no flags needed) always writes **three** deliverables:

1. `<deckname>.pdf` — one page per slide, full fidelity. The share/print format.
2. `<deckname>-editable.pptx` — **editable** PowerPoint: the design (teal fields,
   Stewart bleed, illustrations, cards, dividers, dots, generated marks) is a
   full-bleed background image, and **every piece of copy is a native, editable
   text box** in the correct Rewst font, size, color, and position.
3. `<deckname>-html.zip` — the **editable source**: the HTML plus its asset kit,
   zipped. Unzip and open the HTML in a browser to view/edit/re-render.

This is the standard deliverable set — generate all three every time. (`--no-editable`
exists to skip the editable PPTX, but don't use it unless the user explicitly
asks; editability is part of the standard output.)

Tradeoffs to mention when handing over the **editable** PPTX:
- The editor needs **Poppins and Montserrat installed** locally, or PowerPoint
  substitutes fonts.
- Editing text doesn't reflow the baked background; very long replacements can
  overrun their area.
- Each text box keeps the **design's own line breaks** (the export bakes the
  balanced wrap points in as hard breaks), so headlines wrap the same as the PDF —
  no widows and no re-flow crowding the line below. Re-typing a headline replaces
  those breaks with PowerPoint's own wrapping.
- List bullets/numbers are drawn in the background; the text sits in a native box
  positioned just after the marker (with the hanging indent preserved). Alignment
  is correct in the generated file — if a viewer re-flows it on import, regenerate
  from the current skill.
- Decorative marks live in the background, so they're not editable — the bullet
  and ✓/✕ list markers, indicator dots, and Stewart art. **All actual text is
  editable**, including the agenda's auto-numbers (their CSS counter is resolved
  into a real text box on export).

### 7. Present the results
Share all three: the **PDF**, the **editable `-editable.pptx`**, and the
**`-html.zip`** (editable source). Briefly note which is which — the PDF is
pixel-perfect for presenting or printing as-is; the editable PPTX is for
tweaking copy in PowerPoint; the HTML zip is the master you can re-render.
Don't make the team ask for the editable formats — they're part of every delivery.

## Fidelity notes

- **Fonts:** Poppins headings export perfectly. For pixel-perfect Montserrat
  body text in PDF/PPTX, drop the Montserrat `.ttf` files into `assets/fonts/`
  once (see `assets/fonts/README.md`); otherwise body falls back to a system
  sans in the exports only — the live HTML is always correct.
- **The HTML is the master.** If anything looks off in an export, fix it in the
  HTML and re-export; never hand-edit the PPTX/PDF.
- **No external dependencies at render time.** The renderer blocks network
  fetches, so keep all assets local (the kit already is). Don't add CDN scripts
  or remote images.

## Guardrails

- Primary Bot Teal is `#00BBB4`. Never the retired `#1EAFAF`.
- Every deck opens with the `s-title` bleed-Stewart slide (Bot Teal or Bot Teal
  Deep field). Don't substitute a plain title or drop the Stewart silhouette.
- The off-the-edge Stewart is used ONLY on title and section-divider slides,
  ALWAYS off the right edge, in the same placement every time, and ALWAYS
  tone-on-tone (teal silhouette on a teal field, amber on an amber field). Never
  on other slides, never off the left, never teal-on-amber or amber-on-teal.
- Keep content within the right-hand margin (~110px gutter). Only the bleed
  Stewart may cross it; footers (brand mark, page number, teal dot) stay fixed.
- Every slide shows the Rewst logo bottom-left and the slide number bottom-right
  — including the title and dividers. Never swap, move, or hide them.
- Every content box/card keeps at least `--box-pad-min` (32px) of inner padding
  so text never touches its edge. Small chips, badges, avatars, and table cells
  are exempt.
- No gradients between brand hues; solid fills only.
- Alert Coral (canonical `#F15B5B`) is a small accent only — process badges,
  cons/before glyphs, a single `.tag-coral` pill, an `.accent-coral` highlight,
  or one box in a multi-box set that already uses Trigger Amber. Never a header
  or a large fill (headers stay Teal or Amber).
- No colors outside the four brand families + neutrals.
- Poppins headings, Montserrat body — nothing else.
- Balance wrapped lines and avoid widows (a lone word on its own line or on the
  last line) in headings, titles, and body. The stylesheet handles this
  automatically; for a stubborn case bind the last two words with `&nbsp;`.
- The logo is used as-shipped, with clear space, never altered.

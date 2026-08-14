# Slide Archetypes

`assets/deck-template.html` ships every archetype below, in order, with
placeholder copy in `[brackets]`. Authoring a deck means choosing the
archetypes that fit the content, filling them in, and dropping the rest —
not inventing new layouts. Each `<section>` is one slide; its `class`
selects the archetype.

The deck canvas is **1920×1080 (16:9)**. Slides are the direct `<section>`
children of `<deck-stage>`. Keyboard nav, speaker notes, print-to-PDF, and
auto-scaling are handled by `deck-stage.js` — leave it wired up.

## The 16 core archetypes

| # | Class | Use it for | Where Bot Teal lives |
|---|-------|-----------|----------------------|
| 01 | `s-title` | **Opening slide — required on every deck** | Tone-on-tone teal field + bleed Stewart |
| 02 | `s-agenda` | What we'll cover, with timings | Numbers + lead headline |
| 03 | `s-section` | Chapter / section divider (amber) | — amber slide (number/eyebrow in mid brown, distinct from the deeper title) |
| 04 | `s-stat` | One hero number + what it means | — the hero number is amber |
| 05 | `s-bullets` | Three parallel points | Eyebrow + point headlines |
| 06 | `s-compare` | Before / after, two columns | Eyebrow + headline |
| 07 | `s-image` | Big visual statement + bare feature illustration (no frame — pick art that clears the slide ground) | — |
| 08 | `s-section` | Second section divider | — amber slide |
| 09 | `s-process` | A process in four steps | Eyebrow + step labels |
| 10 | `s-timeline` | Roadmap across quarters/periods | Eyebrow + completed-step dots |
| 11 | `s-table` | At-a-glance comparison grid | Eyebrow |
| 12 | `s-team` | Up to four people | Eyebrow + a card surface; avatars cycle the full brand spectrum (teal → orange → coral → indigo) at primary shade |
| 13 | `s-section` | Third section divider | — amber slide |
| 14 | `s-pricing` | Plan tiers | Featured (middle) tier fill |
| 15 | `s-quote` | Customer quote | — accents are amber |
| 16 | `s-close` | Q&A + contact card | Stewart bleed |

A dash means the archetype carries no primary teal, which is fine — teal anchors
the deck, not each slide.

## The title slide is mandatory

Every deck opens with the `s-title` slide, and it always uses the signature
tone-on-tone Stewart treatment: a single-color Stewart outline bleeding off the
right edge of a teal field. Two on-brand options:

- **Default — Bot Teal field** (`class="s-title"`): a `#00BBB4` background with a
  Bot Teal Deep (`#082C2C`) Stewart outline. Title text is deep teal. The dark
  logo is applied automatically.
- **Deep field** (`class="s-title on-deep"`): a Bot Teal Deep (`#082C2C`)
  background with a primary Bot Teal (`#00BBB4`) Stewart outline. Eyebrow in Bot
  Teal, title in white. The white logo and numerals are applied automatically —
  the authored `.pageno` modifier is ignored.

Don't replace the title with a plain slide, and don't remove the `bleed-stewart`
element — that silhouette is the brand signature for the opener. The page number
is intentionally hidden on the title slide (the bleed art occupies that corner).

## The vibrant theme

The template ships as the dark deck. Adding `class="theme-vibrant"` to
`<deck-stage>` re-bands the whole deck into the vibrant theme.

Grounds are **saturated primaries** — the four family cores — over a Bot Teal
Dark working surface. Light and pale stops never carry a slide; they supply type
and small fills only. Each archetype is assigned deterministically, and no two
adjacent slides in the template's running order share a ground:

| Ground | Type on it | Archetypes |
|--------|-----------|------------|
| `#00BBB4` Bot Teal | `#082C2C` teal-deep | title, bullets, timeline, pricing |
| `#F9A100` Trigger Amber | `#3F2900` amber-deep | section dividers, compare |
| `#7D5100` Trigger Amber Dark | `#FDD999` / white | agenda, table |
| `#504384` Ops Indigo | `#BAB3CF` / white | process, quote |
| `#005655` Bot Teal Dark | `#A5DFDF` / `#D8EDED` | stat, image, team, close *(surface)* |

Override a single slide with
`class="inset-teal | inset-amber | inset-amber-dark | inset-indigo"`.

### A filled box carries its own type

Two token pairs, same idea: **a fill never lets the slide's type tokens leak
inside it.**

| Fill token | Type tokens that go with it | Used by |
|-----------|------------------------------|---------|
| `--t-panel` | `--t-on-panel` | stat card, quote box, CTA card, compare "after", featured tier, table pills |
| `--t-bg-card` | `--t-on-card-label` / `-strong` / `-body` / `-mark` / `-divider` | `s-process` steps, `s-team` cards, `s-pricing` tiers, compare "before" |

The card set defaults to the ground tokens, so leaving it alone changes nothing.
**If a theme fills a card differently from its ground, it must set the card set
too** — otherwise the card gets type coloured for the ground behind it, which on
a white card means pale type on a pale fill.

Two related traps, both of which have produced invisible elements:

- **`--t-on-panel` and `--t-on-accent` default to `var(--t-bg-deep)`** — the
  slide's own ground. That's right on a dark ground and wrong on a bright one.
  Any slide with a bright ground should name them rather than inherit.
- **`--t-mark` holds primary Bot Teal "whatever the family does"** — which is
  self-defeating on a ground that is itself primary Bot Teal. The teal ground
  steps it down a rung.

Glyphs (checks, crosses, chevrons) are **masks painted by a token**, not coloured
SVGs, so they re-band with the theme. If you add one, use the `--glyph-*` tokens
and the **longhand** mask properties — the `mask:` shorthand renders nothing in
headless Chromium, which is what every PDF and PPTX export goes through.

**Keep paired boxes within one rung of each other.** Where a slide paints two
filled boxes side by side — `s-compare`'s before/after columns, `s-pricing`'s
featured tier against the others — the two fills should be adjacent stops in the
same family, not opposite ends of it. Let the *ground* separate the boxes from
the slide; don't make the boxes fight each other. In vibrant that means
`s-compare` runs `#7D5100` beside `#3F2900`, and `s-pricing` runs `#005655`
beside `#082C2C` — both pairs one rung apart, both light-on-dark.

The logo lockup follows the ground: the two bright primary grounds take the dark
wordmark, everything darker takes the white one. It's driven by the `--logo`
token in `deck.css`, so it stays correct through an `inset-` override — don't set
a logo variant in markup.

Grounds come from Bot Teal and Trigger Amber, with Ops Indigo used sparingly.
The first two run **dark type on a bright ground**; Amber Dark, Indigo and the
working surface run **light type on a dark ground**.

**Ops Indigo can only run light-on-dark.** The styleguide gives it no dark stop,
so its primary is very dark and nothing in-family clears AA against it
(indigo-deep manages 1.77:1). Don't try to put dark type on indigo.

**Alert Coral is never a ground, in either theme.** It stays a small accent: the
process step badge, the third team avatar, `.tag-coral`, `.accent-coral`, and the
"before" column glyphs. There is deliberately no `inset-coral`; if you need a
fourth ground, use `inset-amber-dark`.

## Illustrations

The approved isometric set lives in `assets/illustrations/`. Three sizes, both
themes:

| Class | Size | Use |
|-------|------|-----|
| `.ic-item` | 96px | one per repeating item — bullet, tier, timeline quarter |
| `.illus-col` | up to 460px | a feature piece filling an empty column |
| `.illus-topright` | 210px | header-band slot, for dense archetypes where a bottom piece would sit behind a table (`s-table` only in the shipped template) |
| `.illus-panel-corner` | 300px | hung on an inset panel's top-right corner, straddling it |

`.illus-topright` is absolutely positioned inside the 110px gutter and clear of
the footer, so it won't trip `check`. It's art — keep real content out of it.

**Illustrations survive the editable PPTX export as native pictures**, not as
part of the baked background — select, move, resize, or right-click → Change
Picture to swap one. Each carries its source SVG, so PowerPoint draws it as
vector. The lift is scoped by source path (any `<img>` out of `illustrations/`),
which is why a piece doesn't need one of the classes above to come through; the
logo lockups live under `logo/` and stay baked deliberately. Cards, dividers,
pills, and the masked glyphs stay baked too — see SKILL.md.

**Illustrations bleed at the top and right only — never the bottom or left.**
The footer band (bottom 130px) belongs to the logo and page number, and the left
110px gutter stays clear. `deck.py check` enforces both edges on every
illustration, including the ones exempt from the right-margin rule. If a piece
wants to hang off a corner, that corner is top-right.

`s-image` features its illustration bare — there is no frame around it — so the
piece sits directly on the slide ground and the pairing table applies to the
ground itself. Both themes put `s-image` on a teal-family ground: choose from
the indigo or amber rows, never the teal row.

### The panel-corner treatment

`.illus-panel-corner` hangs art off the **top-right corner of an inset box** —
the stat card, a quote panel, a CTA card — so it straddles the corner: the upper
part sits on the slide ground, the lower part on the panel fill. Drop it in as
the first child of the box; the box becomes its positioning context
automatically, so no extra CSS is needed per archetype.

Two rules specific to it:

- **It bleeds past the 110px right gutter, on purpose.** It and the bleed Stewart
  are the only things allowed to. `deck.py check` exempts it *by class name*, so
  renaming it without updating `_MARGIN_JS` in `scripts/deck.py` will start
  failing decks.
- **Top corner only, never the bottom.** A bottom-corner hang would collide with
  the footer band.

**Pair by contrast, because the art is never recoloured.** These are
fixed-palette multi-colour SVGs (that's the point of them), so each has a
dominant family and will lose definition on a ground of that same family.
**A `.illus-panel-corner` piece crosses two grounds and must clear both** — the
slide ground *and* the panel fill — or half of it goes flat:

| Dominant family | Illustrations | Avoid on |
|-----------------|---------------|----------|
| Teal | Chart-going-up, Chart-circle-broken, Workflow-playbook, Education-steps-to-learn | `#00BBB4`, `#005655`, `#A5DFDF` |
| Amber | Community-quote, Community-target, Workflow-chart, Workflow-progress, Object-gold-star | `#F9A100`, `#7D5100` |
| Indigo | Object-gear-cloud, Object-time, Community-handshake, Education-thinking, Education-information | `#504384` |

Five of them contain the retired teal `#1EAFAF` internally. That is known and
left alone by design — `check` doesn't scan the SVGs.

`#A5DFDF` is on the teal row because the vibrant `s-bullets` boxes are filled
with it and hold an illustration each — a teal piece goes flat in there.

Worked example: `s-stat`'s card is a primary-teal panel on a teal-deep ground in
the dark deck, and a white panel on the `#005655` surface in vibrant. Both
grounds are teal in the dark deck, so the whole teal row is out; the template
uses `Education-information` (indigo), which clears both in either theme.

### Tone-on-tone rule: dark on primary, one step

The title and section dividers — the two slides that carry the bleed Stewart —
use one convention in the vibrant theme. The ground is the family's saturated
**primary**; the Stewart silhouette and the type are that family's **dark** stop,
exactly one rung below the ground, never two:

| Slide | Ground | Stewart + type |
|-------|--------|----------------|
| `s-title` | primary Bot Teal `#00BBB4` | Bot Teal Dark `#005655` |
| `s-section` | Trigger Amber `#F9A100` | Trigger Amber Dark `#7D5100` |

Don't mix the directions. A primary-on-dark title next to a dark-on-primary
divider is the inconsistency this rule replaced.

Apply the theme at the deck level, not per slide — mixing dark and vibrant
slides by hand breaks the banding.

## The Supporting graphics slide (PPTX output, both themes)

The PowerPoint template ships one slide of its own — **"Supporting graphics"**,
a sheet of the brand's SVG spot art — and it **stays in the exported PPTX, at
the end of the presentation**, for the dark deck and the vibrant theme alike.
It's a resource for whoever picks the deck up, not a slide in the deck.

- A 16-archetype deck exports as **17 PPTX slides**. That's right. Don't remove
  the extra slide and don't renumber `.pageno` for it — the page numbers are
  baked into the slide backgrounds and describe the deck, not the file.
- **Last, never first.** The exporter moves it behind the generated slides. It
  sits in the template ahead of them, so without that move it would open the
  presentation.
- **PPTX only.** It never appears in the PDF — that export is rendered from the
  HTML and has no knowledge of the template.

The archetype table above still describes the deck. This slide sits outside it.

## Authoring notes

- **Pick, don't pad.** A 6-slide deck is fine. Delete the sections you don't
  use; renumber the `.pageno` (e.g. `04 / 16` → `04 / 08`) so it stays honest.
- **Headline sizing is uniform on the statement slides.** The `s-image`,
  `s-quote`, and `s-close` headlines all default to the `s-section` divider
  size (96px). If authored copy runs longer than the layout holds, an autofit
  pass in `deck-stage.js` steps that headline down (to a floor of ~60%) until
  the slide fits — it never enlarges text. Opt any other element in with
  `data-fit-down` (optional `data-fit-min="<px>"` overrides the floor).
- **Speaker notes** live in the JSON array `#speaker-notes` at the top of the
  file — index `N` maps to slide `N`. Keep its length in sync with the slides
  you keep; the exporter copies these into the PPTX notes pane.
- **Dividers carry the color variety.** Section dividers are amber on purpose;
  the rest of the deck stays in the teal world. Don't make every slide amber.
- **Illustrations** in `assets/.../illustrations/` are the approved isometric
  set — use them on image-led and process slides. Don't pull in outside clip art.
- **Custom slide?** If you build a layout that isn't one of these, keep it inside
  the palette and the 110px right gutter, then run `check` to confirm the
  geometry. There's no per-slide teal requirement to satisfy.

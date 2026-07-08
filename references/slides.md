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
| 03 | `s-section` | Chapter / section divider (amber) | Indicator dot (number is teal-dark) |
| 04 | `s-stat` | One hero number + what it means | Indicator dot (number is amber) |
| 05 | `s-bullets` | Three parallel points | Eyebrow + point headlines |
| 06 | `s-compare` | Before / after, two columns | Eyebrow + headline |
| 07 | `s-image` | Big visual statement + illustration | Full `#00BBB4` background |
| 08 | `s-section` | Second section divider | Indicator dot |
| 09 | `s-process` | A process in four steps | Eyebrow + step labels |
| 10 | `s-timeline` | Roadmap across quarters/periods | Eyebrow + completed-step dots |
| 11 | `s-table` | At-a-glance comparison grid | Eyebrow |
| 12 | `s-team` | Up to four people | Eyebrow + a card surface; avatars cycle the full brand spectrum (teal → orange → coral → indigo) at primary shade |
| 13 | `s-section` | Third section divider | Indicator dot |
| 14 | `s-pricing` | Plan tiers | Featured (middle) tier fill |
| 15 | `s-quote` | Customer quote | Indicator dot (accents are amber) |
| 16 | `s-close` | Q&A + contact card | Stewart bleed + indicator dot |

## The title slide is mandatory

Every deck opens with the `s-title` slide, and it always uses the signature
tone-on-tone Stewart treatment: a single-color Stewart outline bleeding off the
right edge of a teal field. Two on-brand options:

- **Default — Bot Teal field** (`class="s-title"`): a `#00BBB4` background with a
  Bot Teal Deep (`#082C2C`) Stewart outline. Title text is deep teal. Use the
  dark logo (`rewst-logo.png`).
- **Deep field** (`class="s-title on-deep"`): a Bot Teal Deep (`#082C2C`)
  background with a primary Bot Teal (`#00BBB4`) Stewart outline. Eyebrow in Bot
  Teal, title in white. Switch the brand mark to `rewst-logo-ondark.png` and the
  `.pageno` to `on-dark`.

Don't replace the title with a plain slide, and don't remove the `bleed-stewart`
element — that silhouette is the brand signature for the opener. The page number
is intentionally hidden on the title slide (the bleed art occupies that corner).

## Light variants

Any slide flips to a cream background by adding `theme-light` to its class
(`class="s-agenda theme-light"`). The template includes ready-made light
versions of Agenda, Big Stat, Bullets, and Team at the end — duplicate or move
them into the flow as needed. On light slides the eyebrow/number teal softens
for contrast, so these rely on the indicator dot for the Bot Teal rule.

## Authoring notes

- **Pick, don't pad.** A 6-slide deck is fine. Delete the sections you don't
  use; renumber the `.pageno` (e.g. `04 / 16` → `04 / 08`) so it stays honest.
- **Speaker notes** live in the JSON array `#speaker-notes` at the top of the
  file — index `N` maps to slide `N`. Keep its length in sync with the slides
  you keep; the exporter copies these into the PPTX notes pane.
- **Dividers carry the color variety.** Section dividers are amber on purpose;
  the rest of the deck stays in the teal world. Don't make every slide amber.
- **Illustrations** in `assets/.../illustrations/` are the approved isometric
  set — use them on image-led and process slides. Don't pull in outside clip art.
- **Custom slide?** If you build a layout that isn't one of these, give it a
  primary `#00BBB4` element (an eyebrow, an indicator, a teal surface) or simply
  keep the footer dot — then run `check` to confirm.

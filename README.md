# rewst-slides

Claude skill for branded presentations in PDF, HTML, and editable PPTX.

`rewst-slides` builds decks that look like Rewst made them — and enforces it,
slide by slide. A deck is authored as a self-contained HTML file (the source of
truth), then exported to three formats. Brand fidelity comes first: the Rewst
palette (Bot Teal `#00BBB4` as the anchor), Poppins/Montserrat type, and correct
logo usage.

## What's in here

| Path | Purpose |
|------|---------|
| `SKILL.md` | The skill itself — workflow, brand rules, export commands. |
| `references/brand.md` | Palette, type, logo, and voice. |
| `references/slides.md` | Every archetype, what it's for, and where teal lives. |
| `assets/deck-template.html` | Starting deck — 16 archetypes (dark, or `theme-vibrant`), placeholder copy. |
| `assets/deck.css`, `deck-stage.js`, `design-system/`, `logo/`, `illustrations/`, `fonts/`, `template/` | The brand kit the HTML depends on (`template/` holds the Rewst `.potx` embedded in the editable PPTX). |
| `scripts/deck.py` | `check` (verify brand compliance) and `export` (write the full set). |
| `CHANGELOG.md` | Version history. |

## Exports

`export` writes any subset of three deliverables (`--formats pdf,pptx,html`;
the skill asks which you want):

- `.pdf` — one page per slide, full fidelity; the share/print format.
- `-editable.pptx` — native PowerPoint with editable text, bullet
  characters, and shape autoshapes.
- `-html.zip` — the portable self-contained deck.

## Brand compliance

`deck.py check` renders every slide in a real browser and verifies: no content
bleeds past the right gutter, content boxes keep minimum padding, footers show
the logo and slide number, and no retired teal remains in source. A `FAIL` is a
real defect — decks that fail don't ship.

## Installing the skill

Grab the latest `.skill` file from
[Releases](https://github.com/Stepherglades/rewst-slides/releases/latest) and
save it into your Claude profile, or add the files in this repo to a skill
directory directly.

## Versioning

Released as `vMAJOR.MINOR` tags, with a patch number for pure fixes (`v1.3.1`).
See [`CHANGELOG.md`](CHANGELOG.md) for what changed in each version — its top
heading is the single source of truth for the version, and this line restates it
by hand, so update both together. The current release is **v1.9.2**.

---

Private repo — Rewst internal tooling.

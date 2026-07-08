# Changelog

All notable changes to the `rewst-slides` skill are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project
uses simple `vMAJOR.MINOR` release tags.

## [Unreleased]

### Planned
- **Editable list markers in the PPTX export.** Emit bullets, numbers, and
  ✓/✕ list glyphs as native PowerPoint markers (drawn by PowerPoint) instead of
  baking them into the slide background, so they reflow and stay aligned when the
  text is edited. Validated in a working copy of `scripts/deck.py`; slated for
  v1.1 once reviewed against the standard QA passes.

## [1.0] — 2026-07-08

Production baseline — the version provisioned org-wide in claude.ai. Frozen here
as the point to revert to.

### Highlights
- **16 slide archetypes + light variants** in `assets/deck-template.html`, wired
  to the brand kit (`deck.css`, `design-system/`, `logo/`, `illustrations/`).
- **Brand fidelity enforced by `scripts/deck.py check`** — five rules per slide:
  primary Bot Teal (`#00BBB4`) present, content inside the 110px right gutter,
  ≥32px box padding, footers correct (logo bottom-left, page number
  bottom-right), and no retired teal (`#1EAFAF` / `#1CAFAF`) in the source.
- **One `export` command writes three deliverables:** the full-fidelity PDF, the
  editable PPTX (design baked as a full-bleed background with every piece of copy
  as a native, editable text box), and the `-html.zip` source bundle. Speaker
  notes carry into the PPTX notes pane.
- The older faithful (image-per-slide, non-editable) PPTX has been retired from
  the standard output set.

### Known behavior in this version
- **List markers are drawn in the background**, so bullets, numbers, and ✓/✕
  glyphs are not editable; all actual text is. (This is the item the Unreleased
  editable-marker work will change.)
- Body text falls back to a system sans in the exports unless Montserrat `.ttf`
  files are placed in `assets/fonts/`. Poppins headings export correctly either
  way; the live HTML is always correct.
- Re-typing a headline in the editable PPTX replaces the baked balanced line
  breaks with PowerPoint's own wrapping — re-check headlines after editing.

[Unreleased]: https://github.com/<your-username>/rewst-slides/compare/v1.0...HEAD
[1.0]: https://github.com/<your-username>/rewst-slides/releases/tag/v1.0

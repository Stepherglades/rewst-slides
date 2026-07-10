# Changelog

All notable changes to the `rewst-slides` skill are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project
uses simple `vMAJOR.MINOR` release tags.

## [Unreleased]

### Added
- **Rewst PowerPoint template embedded in the editable PPTX.** The export is
  now built on `assets/template/rewst-slides.potx`, so the delivered file
  carries the branded slide master, six branded layouts (title, content_dark,
  section divider, big statement, quote, content_light), and the theme palette
  anchored on Bot Teal `#00BBB4`. Generated slides are visually unchanged
  (design background + explicit text styling as before); the layouts exist so
  hand-added slides in PowerPoint pick up on-brand color, type, and placement.
  Cloned layout placeholders are stripped from generated slides (no
  "Click to add" ghosts), and export falls back to the plain PPTX base if the
  template file is missing. The theme's `accent1` was corrected from `00BBB3`
  (a Mac color-picker rounding) to the canonical `00BBB4`.
- **`--formats` flag for selective export.** `deck.py export --formats
  pdf,pptx,html` writes any subset of the three deliverables (default: all).
  Unknown tokens and an empty selection fail fast with exit code 2.
  `--no-editable` is kept for compatibility and simply removes `pptx` from the
  selected set.

### Changed
- **Export workflow is now ask-first.** `SKILL.md` instructs Claude to ask the
  user which of the three deliverables they want (PDF, editable PPTX, HTML
  source zip) and export only those via `--formats`, instead of always
  generating all three. "All" remains one word away, and skipped formats can be
  re-exported later without re-rendering the deck.

## [1.3.1] — 2026-07-10

### Added
- Montserrat `.ttf` files (Regular, Medium, SemiBold, Bold, Black) in
  `assets/fonts/`. `scripts/deck.py` auto-detects and embeds them at render
  time, so PDF and PPTX exports now use the real body font instead of a
  system-sans fallback. The live HTML deck was already unaffected (it loads
  Montserrat from Google Fonts).

## [1.3] — 2026-07-09

### Changed
- **`s-image` and `s-quote` headlines raised to the `s-section` divider size
  (96px, `var(--type-title)`).** `s-image` was 80px; the `s-quote` lead
  headline was a 64px `.h-2` and now also matches the divider's 1.02
  line-height and -0.015em tracking. The statement-style slides now share one
  headline scale.
- **`s-close` headline reduced from 120px to the `s-section` divider size
  (96px, `var(--type-title)`).** The eyebrow → "Questions?" spacing is
  unchanged (the eyebrow's 28px `margin-bottom` is untouched), so the
  eyebrow/headline rhythm now matches the dividers exactly.
- **New headline autofit in `deck-stage.js`.** The `s-image`, `s-quote`, and
  `s-close` headlines shrink automatically (2px steps, floor at ~60% of the
  starting size) when authored copy overflows the slide's fixed content area;
  short copy renders at the full 96px. Runs at load and again after web fonts
  resolve, so PDF export, editable-PPTX text extraction (which reads computed
  styles), and the live deck all see the fitted size. Any element can opt in
  with `data-fit-down`; `data-fit-min="<px>"` overrides the floor.

- **`s-stat` light variant: stat number is now primary Bot Teal
  (`--brand-teal`, #00BBB4) and the metric-label eyebrow is Trigger Amber
  (`--t-accent`, #F9A100).** Previously the number stayed amber and the
  eyebrow rule (written as a descendant selector, `.theme-light .s-stat`)
  never matched, leaving the eyebrow pale amber. New rules use the compound
  `.s-stat.theme-light` pattern consistent with the agenda/bullets light
  variants. Dark theme unchanged.
- **`s-stat` eyebrow-to-stat spacing widened.** The big stat number now sits
  farther from the metric-label eyebrow: `.s-stat .stat-num` gains
  `margin-top: 28px` on top of the left column's 28px flex gap, giving a
  ~56px effective gap between eyebrow and number while the number-to-headline
  gap stays at 28px. Matches the reference layout's ~2:1 rhythm. One rule in
  `assets/deck.css`; applies to both dark and light themes and flows through
  PDF, editable PPTX, and HTML exports (positions are measured from the DOM).
- **`s-close` left column is now vertically centered.** The eyebrow /
  "Questions?" headline / body block sits at the middle of the slide instead
  of anchoring to the top, in both dark and light themes. The CTA card column
  is unchanged. Implemented as a flex column with `justify-content: center`
  on the first grid child in `assets/deck.css`.
- **`s-close` eyebrow gains `margin-bottom: 28px`** so there's clear
  separation between the eyebrow and the headline, matching the `s-section`
  spacing convention.
- **`s-agenda` and `s-bullets` light variants: lead headline (`.h-2`) now uses
  primary Bot Teal (`#00BBB4`).** Previously the light theme remapped them to
  darkened teals (#005655 / #0E3D3D). Dark-theme headlines are unchanged. A new
  fixed `--brand-teal` token in `deck.css` is exempt from the `theme-light`
  remap so these headlines stay primary on cream.
- **`s-section` number and eyebrow now use mid brown (`--c-brown`, #7D5100)**
  instead of dark teal (`--c-teal-dark`, #005655). The "01" number and
  "CHAPTER ONE" eyebrow read as a warm accent sitting between the amber
  background and the deeper `--c-brown-dark` title, keeping the divider's
  left block in the warm family. The footer indicator dot still carries
  Bot Teal, so the primary-teal-on-every-slide rule is unaffected.

## [1.2] — 2026-07-08

Export pipeline: the s-timeline column dots become native, editable ovals, and
they now sit directly under each column label. `scripts/deck.py` and
`assets/deck.css` change from v1.1.

### Changed
- **Timeline column dots are now native, editable PPTX ovals.** The colored dots
  under each `s-timeline` column header are lifted out of the slide-background
  image and drawn as real PowerPoint ovals at the design's exact position, size,
  and fill (teal for the `done` column, accent for the rest). They can now be
  recolored or moved in PowerPoint instead of being frozen into the background.
- **Dots sit directly under their column labels.** In `assets/deck.css`,
  `.s-timeline .qtr .dot` moves from `top: 80px; left: 18px` to
  `top: 48px; left: 0`, so each dot sits snug beneath its header's underline and
  left-aligns with the label text instead of floating ~50px below, indented. This
  holds across all three deliverables (HTML, PDF, editable PPTX).

### Fixed
- **Bulleted text boxes anchor at the marker, with the design's gap after it.**
  In the editable PPTX, a padded list item's text box was placed past its marker
  (18px right of its column heading on s-timeline) with the dash flush against
  the text. Boxes now start at the item's border box — flush with the heading —
  and the marker-to-text gap is written as a true hanging indent, so the dash
  sits at the box edge, a space follows before the text, and wrapped or edited
  lines keep their alignment. Applies to every list archetype (timeline dashes,
  compare/pricing ✓/✕ lists), not just s-timeline.

### Notes
- Only `scripts/deck.py` and `assets/deck.css` change in this release.
- The footer Bot Teal dot was already native (v1.0); this extends the same
  treatment to the timeline dots. Stewart art remains the only baked decorative
  mark.
- Re-run `scripts/deck.py check` and export the timeline archetype; confirm in
  PowerPoint that each dot is a selectable oval sitting under its label.

## [1.1] — 2026-07-08

Export pipeline: list markers become native and editable. This is the working
copy of `scripts/deck.py` validated during QA — the only file that changes from
v1.0.

### Changed
- **List markers are now native, editable PPTX elements.** Bullets, numbers, and
  the ✓/✕ list glyphs are emitted as real PowerPoint markers (drawn by
  PowerPoint) instead of being baked into the slide-background image. They now
  reflow and stay aligned when the text in a list item is edited — previously,
  editing an item left the marker stranded because it lived in the background.
- Only `scripts/deck.py` changes in this release. `SKILL.md`, `assets/`, and
  `references/` are identical to v1.0.

### Notes
- Update the "Known behavior" note carried over from v1.0: list markers are no
  longer background-only. All other v1.0 behavior (Montserrat font fallback in
  exports, headline re-wrap on edit) is unchanged.
- Re-run `scripts/deck.py check` and a multi-slide export pass before publishing,
  and confirm marker alignment holds after editing a list item in PowerPoint.

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
  glyphs are not editable; all actual text is. (Changed in v1.1.)
- Body text falls back to a system sans in the exports unless Montserrat `.ttf`
  files are placed in `assets/fonts/`. Poppins headings export correctly either
  way; the live HTML is always correct.
- Re-typing a headline in the editable PPTX replaces the baked balanced line
  breaks with PowerPoint's own wrapping — re-check headlines after editing.

[Unreleased]: https://github.com/<your-username>/rewst-slides/compare/v1.2...HEAD
[1.2]: https://github.com/<your-username>/rewst-slides/compare/v1.1...v1.2
[1.1]: https://github.com/<your-username>/rewst-slides/compare/v1.0...v1.1
[1.0]: https://github.com/<your-username>/rewst-slides/releases/tag/v1.0

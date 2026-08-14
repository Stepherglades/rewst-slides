# Changelog

All notable changes to the `rewst-slides` skill are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project
uses simple `vMAJOR.MINOR` release tags, with a patch number for pure fixes.

## [1.9.2] — 2026-08-12

> **Verified 12 Aug 2026.** `test_pptx_pictures.py` is 22/22 (was 17/17), and the
> five new checks were mutation-tested — removing the `_lock_background` call
> turns two of them red, so they are looking at the thing they claim to check.
> `run-check.command` passes on both decks. The owner then drag-tested a real
> export in **macOS PowerPoint**: the background refuses to move and still
> deletes, which is exactly the intended trade. The package was rebuilt and
> `diff -rq`'d against the skill folder, and the suite re-run against the
> unzipped package.
>
> **Windows PowerPoint was not tested and can't be** — there's no Windows access
> on this project. Low risk, and in the reassuring direction: `picLocks` support
> has historically been weakest on Mac, so the Mac pass is the harder result. A
> build that ignores the flags renders the deck identically anyway.
>
> A **patch**, by owner decision. The argument for a minor is that the emitted
> PPTX changes for every deck author; the argument for a patch, which won, is that
> nothing about authoring changes, the deck renders pixel-identically, and the
> whole delta is two attributes on one element. `1.3.1` and `1.9.1` are the
> precedents. Previous release preserved at
> `rewst-slides-dev/snapshots/rewst-slides_2026-08-12_v1.9.1-released.skill`.
>
> Renumbered from `1.10`, which was live for about an hour and read as a *revert
> to 1.1* to someone who knows this repo well. `1.10` is defensible under a
> vMAJOR.MINOR scheme and still wrong in practice: a version's job is to say which
> build is newer at a glance, and a two-digit minor lies about that and sorts
> before `1.9` besides. **Keep minors single-digit; use the patch line, or go to
> `2.0` for a real minor.** Recorded in `HANDOFF.md`.
>
> Note also what this defeated: while `1.10` was live, all three places agreed and
> every consistency check passed. Uniformity is not correctness.

### Added — the editable PPTX background is locked against move and resize

The full-bleed background is the one shape on a generated slide that is never a
legitimate edit target. The slide *is* that picture, and every text box and
illustration above it is placed in absolute EMU against its frame — nothing
above it moves with it. It is also the thing under every click that misses a
text box, so the drag is easy to do and the result doesn't look like an
accident; it looks like the exporter got the geometry wrong.

It now goes out named `Background - slide design (locked)`, carrying
`<a:picLocks noMove="1" noResize="1"/>` on its `cNvPicPr`. python-pptx already
emits that element with `noChangeAspect="1"`, so this adds two attributes to an
existing element rather than writing a new one.

**`noSelect` was considered and rejected.** It would also make the background
unclickable and therefore undeletable — a dead end with no in-app escape for
someone who legitimately wants it gone. `noMove` + `noResize` stop the actual
accident and leave every intentional action available. The name says "(locked)"
because PowerPoint shows no lock indicator in the selection pane for these two
flags, and a drag that silently refuses otherwise reads as a broken file.

**Illustrations are deliberately left unlocked.** Swapping one is a supported
edit — it's why they've been named for the selection pane since 1.7 — and a test
now pins that scope so it isn't quietly widened later.

> **Caveat.** PowerPoint's honouring of `picLocks` is uneven across versions. This
> is a guard rail, not a guarantee — an edition that ignores the flags renders
> exactly as it did before, so the downside of it not working is nil. Confirmed on
> macOS, which is the version that matters here and also the historically weakest
> for `picLocks`, so it's the harder result to get.

## [1.9.1] — 2026-08-12

> **Verified 12 Aug 2026.** `run-timeline-test.command` green across both themes,
> then both `-editable.pptx` files opened in real PowerPoint and reviewed by the
> owner — the dots sit on the rule, left-flush with their labels, and select as
> editable ovals. `run-check.command`, `run-export.command` and
> `test_pptx_pictures.py` (17/17) all pass on the full decks.
>
> A **patch**, not a minor: one CSS fix plus a dev-only harness, no behaviour
> change for deck authors (`1.3.1` is the precedent). Previous release preserved
> at `rewst-slides-dev/snapshots/rewst-slides_2026-08-07_v1.9-released.skill`.

### Fixed — `s-timeline` dots printed through their own labels

The rail band was designed as rule-then-dots-then-text, and the 1.7 comment in
`deck.css` spelled out the arithmetic for it: rule at y=30, dot centred on the
rule at `30 − 22/2 = 19`, text from y=76. **The arithmetic was right and the
reference frame was wrong.** `.rail::before` is positioned against `.rail`, so
its `top: 30px` lands where intended; the dot is positioned against `.qtr`, and
`.qtr` is a grid item whose box starts *after* the rail's 76px top padding. The
same `top: 19px` therefore resolved to y=95 — 65px below the rule and directly
on the label, which starts at y=76. The dot and its 6px halo punched a hole
through the first characters of every column label ("40 MYA · AFRICA").

This was never a PPTX bug. It rendered identically in HTML, PDF, and both
exports since the band was introduced; it only got reported once the 1.7
editable export made the dots selectable and someone tried to drag one.

The three numbers that have to agree are now tokens on `.rail`
(`--rail-rule-y`, `--rail-dot`, `--rail-band`) and the dot's offset is a
`calc()` off them — `calc(30px + 1px − 76px − 22px/2)` = −56px, centred on the
rule's centreline rather than its top edge. Two hand-computed offsets in this
archetype have now been wrong in two consecutive releases, so the geometry no
longer lives in literals.

`.rail::before` also ran `left: 30px; right: 30px`, an inset that put the rule's
left end 19px to the right of the first dot's centre — the dots hung off the
front of the line. It now runs `left: 0; right: 24px`: flush with the first
column's text and dot, stopping at the last column's text edge (`.qtr`'s own
right padding). The rule spans the content it describes.

No height change — `--rail-band` is still 76px and text still starts at y=76, so
open item 1 in the handoff ("`s-timeline` may read short") is unchanged, neither
better nor worse.

**One render divergence, documented rather than fixed.** The dot's
`box-shadow: 0 0 0 6px var(--t-bg-deep)` cuts a gap in the rule around each dot.
Now that the dot actually sits on the rule that halo does visible work in HTML
and PDF — but the editable PPTX lifts the dot as a bare native oval and leaves
the rule baked in the background, so there the line reads as passing behind the
dot instead. Both look deliberate; they aren't identical. Noted in `deck.css`.

### Added — a harness that would have caught it (dev only)

`rewst-slides-dev/zz-timeline-test/` holds two one-slide decks — the archetype
and nothing else, dark and vibrant — and `test_timeline_rail.py`, which measures
the rail band in a real browser and asserts the four things a person was checking
by eye: dot centred on the rule, dot left-flush with its label, no dot or halo
intersecting any label in any column, rule spanning first dot to last text edge.
It then opens the exported PPTX and asserts the native ovals landed on the
browser's coordinates — the only check here that can catch the exporter and the
stylesheet drifting apart. Assets are symlinked into the skill rather than
copied, so the harness can't test a stale stylesheet.

Nothing in it is hardcoded; it reads `--rail-rule-y`, `--rail-band`, `--rail-dot`
and `.qtr`'s padding out of the computed styles. Retuning the band doesn't mean
editing the test.

Mutation-tested against synthetic rects: fed the pre-fix numbers, three of the
five checks go red and print the exact overlap from the defect report; fed the
post-fix numbers, all five pass.

`run-export.command` now skips `zz-*` folders. It picks the vibrant test deck by
globbing `*/*.html` and taking the first hit, so a new folder sorting before
`vibrant-theme-test/` would have silently exported the wrong deck under the
vibrant name.

### Verified

| | Status |
|---|---|
| Rail geometry, browser-measured, both themes | **PASS** — `run-timeline-test.command`, 10/10 |
| Native ovals placed on the browser's coordinates | **PASS** — same run |
| Both single-slide PPTX files in real PowerPoint | **PASS** — owner reviewed, 12 Aug 2026 |
| Full decks — gutter, padding, footers, illustration margins, teal | **PASS** — `run-check.command` |
| Full decks export (PDF + editable PPTX) | **PASS** — `run-export.command` |
| Editable-PPTX picture XML | **PASS** — `test_pptx_pictures.py`, 17/17 |

`test_timeline_rail.py` was also mutation-tested: fed the pre-fix numbers, three
of its five checks go red and print the exact overlap from the defect report.

### Fixed — version-number drift across three files

`README.md` said v1.6, `rewst-slides-dev/HANDOFF.md` said v1.8, and this file's
top entry said 1.9. The package on disk was 1.9 and correct. Cause: 1.9 was a
docs-only follow-up that updated `SKILL.md`, this file, and the `.skill` package,
but neither `README.md` nor the handoff. All three now agree.

**The version lives in exactly one place — this file's top heading. `README.md`
and the handoff restate it by hand, which is why it drifted; update all three
together or collapse them to one.** Both restating files now say so in place.

Also added: `snapshots/rewst-slides_2026-08-07_v1.9-released.skill`. There was no
snapshot of 1.8 or 1.9 — the live `rewst-slides.skill` was the only copy of the
released state, and one rebuild would have destroyed it. **Snapshot before every
rebuild.**

### Fixed — the 1.9 package shipped a stale `.pyc`

`rewst-slides.skill` contained `scripts/__pycache__/deck.cpython-310.pyc`,
compiled from whatever `deck.py` happened to be current when someone last ran the
exporter. Harmless but wrong: a bytecode cache of an older script, shipped inside
the deliverable. The 1.9.1 package excludes it, and its file list is otherwise
entry-for-entry identical to 1.9's.

`scripts/__pycache__/` regenerates locally every time anything imports `deck.py`,
so **exclude `__pycache__`, `*.pyc` and dotfiles when rebuilding the package** —
zipping the folder blind puts it back.

## [1.9] — 2026-08-07

### Changed — the theme is asked for, not assumed

Both themes have shipped since 1.5, but the workflow only ever documented the
dark deck as the starting point, so vibrant was reached only when a user named
it. New **step 2: Ask which theme — dark or vibrant**, placed before the working
copy is set up, with a one-line characterisation of each, the signals that answer
the question without asking (understated/formal → dark, keynote/high-energy →
vibrant), and dark as the fallback if the user declines to choose. Steps 2–7
renumbered to 3–8; the "see step 6" cross-reference follows.

Step 4 now opens by setting the theme before any content goes in, and the
guardrails carry the deck-level, one-theme-per-deck rule that previously lived
only in `references/slides.md`.

Docs only — no change to `deck.css`, the exporter, or the template, so all 1.8
verification stands.

## [1.8] — 2026-08-06

> **Verified 6 Aug 2026.** `test_pptx_pictures.py` 17/17 (up from 13), with both
> new behaviours mutation-tested — remove either fix and a check goes red. Then
> a real `run-export.command` run, both files opened in PowerPoint: dark exports
> 17 slides and vibrant 16, the graphics sheet is last in both with all 87 shapes
> intact, the replacement note is in place, and speaker notes are present on
> every deck slide (16/16 and 15/15). PDFs came out 16 and 15 pages,
> byte-identical to 1.7 — the template work doesn't touch that path.

### Added — the template's Supporting graphics slide ships at the end

`assets/template/rewst-slides.potx` now carries one real slide of its own,
"Supporting graphics" — a library of brand SVG spot art. It is part of the
deliverable and stays in the exported PPTX for **both themes**, positioned after
the generated deck. A 16-slide deck exports as 17 slides.

- `_move_template_slides_to_end` reorders `<p:sldIdLst>` after generation. Only
  the id list changes; slide parts and relationships are untouched.
- Needed because python-pptx appends `add_slide()` output *behind* whatever the
  template already holds — left alone, the spot-art sheet opened the deck.
- No-op when the template ships no slides, which covers the stock `.potx` and
  the plain python-pptx fallback.
- **PDF is unaffected**, by design. It renders from the HTML and has no
  knowledge of the `.potx`, so it stays one page per deck slide.

### Fixed — speaker notes survived only by luck, and had stopped working

The amended `.potx` introduced a notes master with an **empty shape tree** — no
body placeholder. python-pptx builds a slide's notes by cloning that master, so
every generated notes slide came back with nowhere to put text and
`notes_text_frame` was `None`. `export_editable` dereferenced it directly, so
this wasn't degraded notes: **the whole editable-PPTX export raised
`AttributeError` and produced no file**, for both themes.

It had worked before only because the previous template had no notes master at
all, letting python-pptx fall back to its own default (which has a body).

Fixed in both places:

- **The template.** `rewst-slides.potx`'s notes master now carries the standard
  placeholder set (hdr / dt / sldImg / body / ftr / sldNum), so notes work on the
  native path. Notes slides get sldImg, body and sldNum cloned onto them;
  header, date and footer aren't cloned, which is python-pptx's behaviour and
  PowerPoint's convention.
- **The exporter.** `_set_speaker_notes` builds the body placeholder when the
  clone comes back without one, and reports rather than raises if notes still
  can't be written. With the template repaired this path is now insurance
  against the next template edit rather than a live workaround.

### Changed — the template's Supporting graphics note no longer says to delete it

The slide's speaker note read "DELETE SLIDE WHEN FINISHED", which directly
contradicts the rule above. It now reads "Reference sheet — leave in place. Copy
any graphic onto a slide; delete this page only if sharing externally."

Both `.potx` edits are scripted in `rewst-slides-dev/fix_template.py` — the
template is a binary asset, so the edits are reproducible rather than living
only in the file. The script is idempotent and backs up to
`rewst-slides-dev/backups/` before writing. Verified afterwards that exactly two
parts changed, the part count held at 136, every part is well-formed, the
content type is still `presentationml.template`, and all 83 spot-art SVGs and 90
shapes on the graphics slide survived.

### Changed — `test_pptx_pictures.py` was measuring the template, not the exporter

Four checks broke on contact with the new `.potx`, and all four were the test's
fault. It counted SVG parts and `<a:blip>` elements package-wide; the spot-art
slide contributed 83 SVGs of its own. It also read `ppt/slides/slide1.xml` by
part name — which is now the template slide, even though that slide is *last* in
reading order.

Both counts are now scoped to the generated slides, addressed through
`prs.slides` order rather than by part name. Four checks added: the template
slide survives, exactly once, and is last; the slide count is deck + 1; and
speaker notes come through. 17 checks, up from 13.

**Two rules for anyone extending this test:** never address a slide by part name,
and never count anything package-wide.

## [1.7] — 2026-08-06

> **Verified 6 Aug 2026.** The PPTX half by automated test
> (`rewst-slides-dev/test_pptx_pictures.py`, 13/13); the browser half by a real
> `run-export.command` run with both `-editable.pptx` files opened in PowerPoint
> — no double-drawn art, no stretch/offset on the contain slots, opacity and the
> vector rendering confirmed by eye. The owner reviewed the un-squashed
> illustrations and approved the new look.

### Added — illustrations are native, swappable pictures in the editable PPTX

Illustrations no longer live inside the baked background image. Each one is
lifted out and placed as a native PowerPoint picture at its exact design
position, so it can be selected, moved, resized, or swapped via right-click →
Change Picture. Swapping art is the most likely edit anyone makes to a delivered
deck, and it was the one edit the editable PPTX couldn't support.

- **Scoped by source path, not by class** — any `<img>` served out of
  `illustrations/`. That catches the unclassed pieces in `s-image` and `s-quote`
  without maintaining a class list, and excludes the logo lockups under `logo/`,
  which stay baked on purpose.
- **Vector, with a raster fallback.** Each picture carries the source SVG via the
  Office 2016 `asvg:svgBlip` extension, so PowerPoint 2016/365 draws vector while
  any older viewer reads the embedded PNG. One SVG part per source file across
  the whole package — the template repeats `Object-gear-cloud` four times, and
  python-pptx only dedupes rasters.
- **Named for their source** (`Illustration - Object-gear-cloud`) so they're
  findable in the Selection pane rather than being `Picture 7`.
- **`object-fit: contain` is resolved before placing.** `.s-image .art img` and
  `.s-process .ic` letterbox their art inside a larger element box, so the
  element rect is not the art's rect; placing at the element rect would have
  stretched them. The painted rect is computed from `naturalWidth`/`Height`.
  Where object-fit is the default `fill` the art is stretched in the design, and
  that is reproduced rather than corrected — the PPTX matches the PDF.
- **`opacity` carries over** as `alphaModFix` (`.s-process .ic` runs at 0.92).
- **Rastered on a transparent ground, not screenshotted in place.** An element
  screenshot captures the composited page, so lifting art off a slide that way
  would have brought the slide's ground with it — every illustration would have
  arrived on an opaque teal rectangle. Each SVG is re-rendered alone, inlined as
  a data URI, and captured with `omit_background`.
- **Z-order is background → illustrations → text**, matching deck.css, where
  `.content-area` paints over `.illus-topright` / `.illus-corner`.
- **Degrades instead of failing.** A rasterize failure un-marks that illustration
  so it stays painted in the background; a failure in the hand-written XML leaves
  a plain raster picture. Neither takes the export down.

### Fixed — fixed-size art slots were squashing every illustration

Every art slot that pins both dimensions had no `object-fit`, so the browser
default `fill` stretched each non-square SVG to the slot's shape. The approved
set is entirely non-square (350×445, 412×249, ...), which means **every
`.ic-item` had been squashed to a 96px square in every deck and every export
since the slots were introduced**. Nobody flagged it — isometric art distorts
gracefully — but it was an oversight, not a decision. Found while wiring the
PPTX illustration lift, whose `object-fit` handling made the missing property
visible.

All fixed-size slots now `contain`, each anchored where its placement wants it:

| Slot | object-position | Why there |
|------|-----------------|-----------|
| `.ic-item` (and the 72px timeline variant) | `left bottom` | aligned with the text column under it; hugs the headline below |
| `.illus-corner` | `right bottom` | into its corner, box already clears the footer |
| `.illus-topright` | `right top` | into its corner of the header band |
| `.illus-panel-corner` | centered | preserves the above/below-the-panel-edge balance it straddles |
| `.s-quote .qmark img` | centered | 130px slot, mild correction |

Visible change: `s-bullets`, `s-timeline`, `s-pricing`, `s-table`, `s-quote`,
and any deck using the corner slots render the art at its true aspect ratio —
narrower than before, never distorted. Layout boxes are unchanged; only the
paint inside them.

The exporter's `_ILLUS_JS` also stopped assuming `object-position` is centered —
it was already wrong for `.s-agenda .illus-col` (`left bottom`, pre-existing)
and would have misplaced every newly anchored slot by up to ~20px. Both `N%` and
`Npx` components resolve per CSS Images 3 (percentage distributes the free
space).

### Added — `test_pptx_pictures.py`

The illustration lift introduced the first hand-written OOXML in the exporter,
which is the one thing here that can produce a file PowerPoint refuses to open.
It now has a test that stubs the browser out entirely (no playwright, no
Chromium) and checks package integrity, placement, dedupe, z-order, the svgBlip
extension, and `CT_Blip` child order. It does **not** check that the right things
were lifted or that they left the background — that still needs a real export.

### Not done, deliberately

Inset boxes, cards, dividers, pills, badges, and the masked glyphs stay baked.
Lifting those means reproducing one-sided borders as separate shapes, writing
`outerShdw` effect XML, and un-painting each box property-by-property rather than
hiding it — and it couples `deck.css` to the exporter, so a new card class starts
breaking exports silently. Recommend rebuilding on the branded `.potx` layouts
instead when someone needs to restyle chrome.

## [1.6] — 2026-08-06

> **Browser-verified 6 Aug 2026.** `deck.py check` passes on both the vibrant
> 15-slide test deck and the shipped dark template, including the new
> illustration-margin rule, and the exports were reviewed by eye. The static
> audit (widened this release) reports 0 failures across 121 text elements in
> both themes. Contrast ratios remain static estimates, as before.

### Fixed — one root cause behind three archetypes

`--t-bg-card` was a fill token with no type partner. `--t-panel` has always
travelled with `--t-on-panel`, but a card painted with `--t-bg-card` resolved its
type from the *slide's* tokens, which are tuned for the ground. On the dark deck
that is invisible, because card and ground are both dark teal. The moment the
vibrant theme filled cards white, it painted the ground's pale type onto a pale
fill:

| | was | now |
|---|---|---|
| `s-process` step title | `#BAB3CF` on white — **2.01:1** | `#005655` — 8.53:1 |
| `s-process` step description | `#BAB3CF` on white — **2.01:1** | `#005655` — 8.53:1 |
| `s-team` name | `#A5DFDF` on white — **1.48:1** | `#082C2C` — 14.93:1 |
| `s-team` role | `#D8EDED@0.8` on white — **1.17:1** | `#005655@0.8` — 5.13:1 |

Fixed with a card-interior type set — `--t-on-card-label`, `-strong`, `-body`,
`-mark`, `-divider` — that stands to `--t-bg-card` as `--t-on-panel` stands to
`--t-panel`. Defaults **alias** the ground tokens rather than restating the dark
deck's literal values, so unset is provably no change; verified by resolving every
one of them in both themes.

A fourth archetype had the same wiring and was converted with them:
`s-compare`'s "before" column. Its existing vibrant remap targeted the ground
type tokens, which also paint that slide's headline — the scope was load-bearing.
On the card set it no longer is.

### Fixed — glyph colours were unreachable by any theme

Five check/cross/chevron glyphs had their stroke baked into a `background-image`
data URI, so no theme could re-band them. That caused a real defect and hid a
second:

- **`s-pricing` featured tier:** hardcoded `#082C2C` ticks on a `#082C2C` fill —
  **1.00:1, literally invisible.** Now `--t-on-panel`, 10.11:1.
- **`s-compare` ✕:** hardcoded `#FF4C54`, off-palette (canonical Alert Coral is
  `#F15B5B`). Now `--t-coral`. *Closes a known open item from 1.5.*

All five are now masks painted by a token. They use the **longhand** mask
properties: the `mask:` shorthand silently renders nothing in headless Chromium,
which is what every PDF and PPTX export goes through — the same trap already
documented on `.bleed-stewart`.

Coral on the vibrant `#7D5100` before-column is 2.10:1 either way, so that
column steps its ✕ up to Coral Light (3.37:1). Pre-existing; it only became
fixable once the colour was a token.

### Fixed — two more invisible marks on the primary-teal ground

Both are the same failure as the `--t-on-panel` bug found in 1.5: a token whose
default resolves to the slide ground, on a slide whose ground is bright.

- **`s-timeline` Q1 dot:** `--t-mark` is meant to hold primary Bot Teal when the
  family darkens. On a ground that *is* primary Bot Teal that intent is
  self-defeating — `#00BBB4` on `#00BBB4`, **1.00:1**. Steps one rung to
  teal-deep, 6.23:1. Set on the ground, not the archetype, so `inset-teal` gets
  it too.
- **`s-pricing` "MOST POPULAR" ribbon:** `--t-on-accent` defaults to
  `--t-bg-deep`, so the ribbon painted `#00BBB4` type on its own `#F9A100` fill —
  **1.15:1**, on the one badge whose entire job is to mark the featured tier.
  Now amber-deep, 6.62:1. *Found by the widened audit, not reported.*

### Fixed — archetype geometry (both themes)

- **`s-process` steps share a baseline.** The step interior is now a grid with
  explicit rows instead of a flex column. Two independent causes of the ~25px
  drift: `margin-top:auto` bottom-aligned the text, so a title's position was set
  by how many lines its own description wrapped to; and the 200px art box was
  flex-shrinkable, so a taller intrinsic SVG squeezed differently from its
  neighbours. Fixed rows remove both.
- **`s-timeline` rail is a band above the content, not a line through it.** The
  rule sat at y=90 while the dots sat at y=48 and the art started at y=60 — the
  rule cut through the art and the dots overlapped it. Rule to y=30, dots centred
  on it at y=19, content from y=76.
- **`s-agenda` and `s-close` fill the canvas.** The agenda list spreads its rows
  over the full column height and the lead column gained an illustration; the
  close slide centres in its content area instead of banking ~400px of empty
  space at the bottom.

### Changed

- `.dur` and `.contacts strong` opacity 0.6 → 0.7. Both sat at 2.88–2.92:1,
  a hair under the 3:1 their size requires. Affects the dark deck too,
  deliberately — it was equally under the line there.

### Fixed — teal background and logo showing behind every exported PPTX slide

`_branded_presentation()` bases generated slides on the layout with the fewest
placeholders. That resolves to layout 4, **"big statement"**, whose full-bleed
background image is `#00BBB4` with the Rewst logo — so every exported slide
carried a teal-and-logo plate underneath its real design.

Generated slides now set `showMasterSp="0"`, which suppresses inherited shapes
from the layout and master (PowerPoint's "Hide background graphics"). It does not
touch the background fill, and it's per-slide, so the `.potx` keeps its six
branded layouts intact for anyone adding a slide by hand — which is the reason
the template ships in the first place.

**The `.potx` was not edited.** Verified structurally: the attribute lands on
`<p:sld>` and the generated slide inherits zero shapes.

### Fixed — `s-compare`'s teal "after" column, and the wrong belief behind it

`--t-panel: var(--t-headline)` in `:root` does **not** mean "whatever
`--t-headline` is on this slide." CSS substitutes `var()` inside a custom
property at the element where it is *declared*, and the resulting literal is what
inherits. `--t-panel` therefore computes once, on `:root`, to primary Bot Teal,
and no slide-level `--t-headline` remap reaches back to change it.

The header comment in `deck.css` asserted the opposite, and the theme was built
on that assertion. The dark deck never exposed it, because there `:root`'s teal
*is* the wanted panel fill. In vibrant it meant:

- **`s-compare`:** the "after" column rendered as a Bot Teal box beside an
  amber-dark "before" column — not one rung apart, not even the same family,
  on an amber ground. Now amber-deep `#3F2900` / `#FDD999` (10.18:1), which is
  the pairing `references/slides.md` documented all along.
- **`s-table`:** the "good" pill was teal by accident rather than decision. Teal
  is right for a positive pill, so it's now named explicitly.

Same root cause as the `s-pricing` featured tier fixed in 1.5 — that one was
patched, the lesson was written down, but the rest of the stylesheet was never
swept. The header comment is corrected, and there is now a test.

Also fixed alongside it: `.s-compare .col.before li` still drew from
`--t-body-on-dark`, giving `#3F2900` on `#7D5100` — **1.99:1**. Now
`--t-on-card-body`, 5.10:1. Missed in the first pass because the element audit
only sees classed elements, and a bullet is a bare `<li>`.

### Fixed — every content area had silently lost its footer reserve (since 1.5)

The overlay rule added with the 1.5 illustration work —
`deck-stage section .content-area { position: relative; z-index: 1; }` — has
higher specificity (0-1-2) than the base `.content-area` rule (0-1-0), so its
`position: relative` beat the base rule's `absolute` and every content area
became a normal-flow, auto-height box. Three mechanisms depended on that height
being definite, and all three failed without a visible error:

- **the 130px footer reserve** — content could run straight over the logo and
  page number, which is exactly what the agenda did the moment it gained an
  illustration (`img.illus-col bottom @1050px`);
- **the headline autofit** — an auto-height box never reports
  `scrollHeight > clientHeight`, so it never fired once between 1.5 and now;
- **percentage row tracks** — indefinite container, so `minmax(0, 100%)`
  resolved to `auto` and capped nothing.

The rule now sets `z-index` only; the base rule's `absolute` positioning stands.
Caught by the new illustration-margin check on its first real run — the two
"failures" it reported were both symptoms of this.

### Changed — `s-image` features its illustration bare

The `.frame` inset box is gone; the illustration sits directly on the slide
ground at up to 680px. Consequence: **the pairing table now applies to the
ground itself**, and both themes put `s-image` on a teal-family ground, so the
teal-dominant `Workflow-playbook` the template shipped would have gone flat.
Swapped for `Education-thinking` (indigo), which clears both themes — this also
closes the long-standing "Workflow-playbook on `s-image`" clash from the 1.5
open items.

### New rule — illustrations bleed top/right only

Art never enters the bottom footer band (logo and page number live there) and
never crosses the left gutter. `deck.py check` gained a fourth geometry rule
enforcing both edges on every illustration, including the two pieces exempt
from the right-margin rule. Prompted by the agenda's new illustration running
straight over the brand mark.

### Fixed — `s-agenda` list overflow (and that illustration)

The agenda's grid row was content-sized: when the lead column (headline + body
+ illustration) ran taller than the content area, the row grew, and the list —
`height:100%` *of that row* — grew with it, pushing its last entry over the
page number while the illustration overlapped the logo. The row is now pinned
to the content area's height (`grid-template-rows: minmax(0, 100%)`), the lead
became a flex column, and its illustration is the shrinkable element, anchored
bottom-left and never past the footer line.

### Fixed — editable PPTX text no longer overlaps (word-wrap off)

The exporter has always written each text box with the browser's own wrap
points as hard line breaks — but left PowerPoint's word-wrap on. PowerPoint's
slightly wider font metrics could then re-wrap one hard line into two, shifting
every line below it down and over the next box; on the vibrant `s-image` slide
that put a 96px headline through its own body copy. Wrap is now off for every
box with captured lines (worst case becomes a few px of right overhang, which
the +6% width buffer absorbs), and stays on only for the raw-text fallback,
which has no measured breaks. Cost, documented in the source: text hand-edited
in PowerPoint won't reflow.

### Tooling — two source-level lints (T9)

The DOM audit structurally cannot see either of the bugs above, so they're
checked at source level instead:

- **T9a** — every archetype consuming `--t-panel` on a non-teal ground must name
  the pair. Catches the inheritance trap directly.
- **T9b** — inside a painted box, `color` may not come from a ground type token.
  Handles the case where the selector's subject is a bare tag (`.col.before li`),
  which is what hid the bullet defect.

Both were verified by reverting the fixes and confirming they fire.

### Tooling — why 1.5 shipped these defects past a clean audit

`rewst-slides-dev/test_theme.py` reported 1.5 as passing. It was wrong four ways,
all now fixed. Re-running the *shipped* 1.5 stylesheet through the corrected
audit gives **23 failures**, not zero.

1. **It scored a theme that doesn't exist.** `deck.css` has two
   `.theme-vibrant {}` blocks; the audit read only the first with `re.search`.
   Every theme-wide token declared in the second — `--t-card-shadow`, `--t-tint`,
   `--t-mark`, `--t-on-coral` — silently resolved to its `:root` default.
2. **It only looked at 15 of 40 text roles.** `TEXT_ROLES` is hand-maintained and
   contained the shared type helpers but no per-archetype roles, so it never
   examined a step title, a person's name, a tier price or a tick. It now covers
   30 and says so: *a role missing from that list is not passing, it is
   unexamined.*
3. **It confused descendants with their parents.** Any rule *containing* `.step`
   answered for `.step`, so the coral badge fill was treated as the step card's
   surface. Selector subject is now required to match, and `::before` glyphs are
   no longer mistaken for surfaces at all.
4. **It couldn't tell `.tier` from `.tier.feature`.** It took the first painted
   class on an element, so the featured tier was scored against the plain tier's
   fill, and the featured tier's colour rules won for all three tiers. It now
   tracks each element's ancestor class chain, honours `:not()`, and resolves
   tokens in the scope that element actually sees.

Coverage went from 58 elements to 121. **This is the finding worth carrying
forward:** every colour defect in this release was reachable by static analysis
the whole time.

### Unchanged by request

The vibrant featured tier keeps its `#082C2C` fill. It is the darker half of the
one-rung pair and so reads as the least prominent of the three tiers, with only
the ribbon marking it — correct by the rule, and left as is.

## [1.5] — 2026-08-06

> **Browser-verified 6 Aug 2026.** `scripts/deck.py check` passes on both the
> vibrant test deck and the shipped dark template: right margin, box padding,
> footers, no retired teal. That run covered the Bot Teal rule removal, the
> panel-corner illustration and the `s-bullets` boxes. The three colour changes
> that followed — the paired-box fills, the explicit `s-pricing` panel pair, and
> dropping the `s-pricing` illustration — are static-verified only; none of them
> moves geometry, but re-run `check` if you want the full set confirmed.
>
> Note that `check` has no contrast rule — the ratios quoted below come from a
> static audit, not from a browser's computed styles. The static audit also
> resolves each slide's ground as `--t-bg-deep`, so it does not model type
> sitting on a `--t-item-fill` box (the `s-bullets` copy really renders at
> 10.11:1, better than the 6.23:1 it is scored at).

### Removed
- **The per-slide Bot Teal rule, and the footer indicator dot with it.** Primary
  `#00BBB4` no longer has to appear on every slide, in either theme. Bot Teal
  remains the brand anchor and the exact canonical shade — it just anchors the
  deck as a whole rather than being audited slide by slide. Removed: the
  `deck-stage section::after` dot and its `.no-teal-dot` escape hatch in
  `deck.css`, the teal-presence verification in `deck.py check` (with the
  `BOT_TEAL` / `MIN_TEAL_PIXELS` constants and the `_count_teal` helper), and the
  native anchor-dot shape the editable PPTX exporter drew on each slide. The
  retired-teal (`#1EAFAF` / `#1CAFAF`) source scan is unaffected and still fails
  the deck. Because `check` no longer needs pixels, it skips the PNG render pass
  entirely and runs faster.

### Changed
- **`s-pricing` drops its illustration.** The `.illus-topright` gold star is gone
  from the template — three tiers of copy is dense enough without it. The class
  itself stays and is still used by `s-table`.
- **Vibrant `s-pricing` names its panel pair explicitly.** `--t-panel` and
  `--t-on-panel` were both falling through the `:root` defaults, which resolve
  *relative to the slide*: `--t-on-panel: var(--t-bg-deep)` meant the featured
  tier's type was painted in `#00BBB4` — the same colour as the ground behind the
  box. Now set outright to `#082C2C` fill (6.23:1 against the ground) and
  `#A5DFDF` type (10.11:1 on that fill). Two indirections deep through tokens the
  slide remaps for other purposes was too fragile for the one box on the slide
  that has to stand out.
- **Paired inset boxes now sit one rung apart, not five (vibrant).** Both slides
  that paint two filled boxes side by side had the widest possible split, because
  the second box inherited the theme-wide white `--t-bg-card` while the first
  resolved `--t-panel` through the slide's *deep* `--t-headline`:
  - `s-compare`: the "before" column moves from `#FFFFFF` to Trigger Amber Dark
    `#7D5100`, beside the amber-deep "after" panel. Both columns now run
    light-on-dark on the bright amber ground.
  - `s-pricing`: the non-featured tiers move from `#FFFFFF` to Bot Teal Dark
    `#005655`, beside the teal-deep featured tier, which is unchanged.

  Both overrides are scoped to the box (`.col.before`, `.tier:not(.feature)`)
  rather than the slide, because the same type tokens also paint the headline and
  eyebrow sitting on the ground, which must stay dark. The `:not(.feature)` scope
  matters for a second reason: `--t-panel` resolves through `--t-headline`, so
  remapping it on a bare `.tier` would drag the featured tier's fill with it.
  All type on the two changed boxes clears AA (lowest 3.56:1, large-text).

### Added
- **Vibrant `s-bullets` points become inset boxes.** The three columns now sit in
  pale-teal (`#A5DFDF`) rounded boxes on the primary-teal ground, each holding
  its illustration and copy together; the amber top rule is gone, since it
  competed with the illustrations. **The dark deck is untouched** — it keeps the
  bare column and the amber rule.

  Done as tokens, not overrides, so the theme's zero-property-override
  architecture holds: four new `:root` tokens (`--t-item-fill`, `--t-item-radius`,
  `--t-item-pad`, `--t-item-rule`) whose defaults reproduce the dark deck's
  previous computed values exactly, with `theme-vibrant .s-bullets` remapping
  them. Side effects: on-box text contrast improves from 6.23:1 to 10.11:1
  (teal-deep now reads on pale teal rather than primary teal), the box sits a
  soft 1.62:1 off the ground by design, and `#A5DFDF` joins the teal row of the
  illustration pairing table because art now sits on it.
- **`.illus-panel-corner` — a fourth illustration placement.** Art hung on an
  inset panel's top-right corner, straddling it: the upper part sits on the slide
  ground, the lower part on the panel fill. Drop it in as the first child of any
  card or panel — the host box becomes the positioning context automatically via
  `:has()`, so no per-archetype CSS is needed. Two things are specific to it:
  it is **allowed to bleed past the 110px right gutter** (the bleed Stewart is no
  longer the sole exception; `deck.py check` exempts it by class name in
  `_MARGIN_JS`), and because it crosses two grounds the pairing rule is stricter
  — the illustration must clear **both** the slide ground and the panel fill.
  Applied to `s-stat` in the template, whose card art moves out of the left
  column onto the card corner; the now-unused `.s-stat .illus-col` sizing
  override was removed with it.
- **Two deck-level themes.** The template is now the dark deck; putting
  `class="theme-vibrant"` on `<deck-stage>` re-bands every slide. Per-slide theme
  mixing is no longer the intended usage, and the four cream "light variant"
  demo slides were removed from the template. (The second theme is named
  **vibrant**, not "light" — it's a saturated colour system, not a pale one.)
- **Vibrant-theme bands from the styleguide showcase.** Hero (`s-title`, primary
  Bot Teal ground with deep-teal type), testimonial (`s-quote` on Ops Indigo),
  feature pair (`s-image`), stat card, and bottom-of-funnel CTA (`s-close`).
- **One tone-on-tone convention for the Stewart slides: dark on primary, one
  step.** The title and section dividers now share a single rule — the ground is
  the family's saturated primary, the Stewart and type are that family's *dark*
  stop, exactly one rung below. `s-title` is a `#00BBB4` field with a `#005655`
  Stewart; `s-section` keeps its `#F9A100` field and its Stewart moves from
  `#3F2900` (two steps) to `#7D5100` (one). Previously the title was
  primary-on-dark while the divider was dark-on-primary, so the two silhouettes
  read at different weights. The vibrant title also drops back to the dark logo
  lockup, matching the base deck's bright-teal title.
- **Primary ground families for the vibrant theme.** Grounds are saturated
  primaries — `#00BBB4` Bot Teal, `#F9A100` Trigger Amber, `#7D5100` Trigger Amber
  Dark, `#504384` Ops Indigo — over a `#005655` Bot Teal Dark working surface.
  Light and pale stops no longer carry a slide; they supply type and small fills
  only. Assigned per archetype so it's deterministic, with `inset-teal` /
  `inset-amber` / `inset-amber-dark` / `inset-indigo` as per-slide overrides.
  Replaces the earlier `-light` tint families, which read washed out and put six
  of fifteen slides on a pale tint.
- **Nested panels are an explicit inverted pair.** `--t-panel` fills a panel and
  `--t-on-panel` types it — the stat card, quote box, CTA card, compare "after"
  column, feature pricing tier and table pills all read that pair. Which half is
  light doesn't matter, only that they invert, so the same base CSS drives
  bright-ground and dark-ground families alike. The earlier vibrant palette had
  the equivalent relationship broken, which is why nearly every panel needed a
  per-archetype override; `s-image` and `s-team` now need no theme rule at all.
- **Ops Indigo documented as the one light-on-dark family.** It has no dark stop
  in the styleguide, so its primary is the darkest of the four and no in-family
  colour clears AA against it (indigo-deep: 1.77:1). It takes white headlines and
  `#BAB3CF` body, like the working surface.
- **Alert Coral is never a ground, in either theme.** `brand.md`'s "small accent
  only" rule stands as written. There is no `inset-coral` family; the fourth
  ground is `inset-amber-dark` instead. Coral survives as the process step badge,
  the third team avatar, `.tag-coral`, `.accent-coral`, and the "before" glyphs.
- **Trigger Amber Dark `#7D5100` added as a ground family** (`inset-amber-dark`,
  default on `s-agenda` and `s-table`). Runs light-on-dark with `#FDD999` accents
  and white headlines. It keeps the deck's warm register without spending primary
  amber — the CTA colour — on a third and fourth full slide.
- **Ops Indigo limited to two slides** (`s-process` and the `s-quote` testimonial
  band), rather than three.
- **Illustrations used across far more of the deck, in both themes.** Three new
  utility classes — `.ic-item` (96px, one per repeating item), `.illus-col` (an
  in-column feature piece), and `.illus-topright` (a header-band slot for dense
  archetypes) — wired into `s-bullets`, `s-compare`, `s-timeline`, `s-stat`,
  `s-table`, `s-pricing` and `s-close`. The template now places 13 illustrations
  where it previously placed 6. `.illus-topright` sits inside the 110px gutter and
  clear of the footer band, so it doesn't trip `check`.
  The art is **not** recoloured per slide — it's fixed-palette multi-colour SVG,
  which is the point of it — so each piece is paired against a ground from a
  different family. The compatibility table is in `references/slides.md`.
- **Ground-driven logo and page number.** The authored `<img>` variant and the
  `.pageno` `on-light`/`on-dark` modifiers are now ignored; CSS picks the
  correct lockup and numeral color from the slide's actual ground in both
  themes. Deck markup no longer has to get this right.

### Refactored
- **The vibrant theme is now tokens only — zero property overrides** (was 29,
  spread across 10 archetypes). Restyling a slide means changing a value, not
  adding a rule. `theme-vibrant` rule count went 37 → 11, all of them token
  blocks, and the whole theme now reads as one ~45-line colour map.
- **New semantic tokens** so nothing needs patching. Every default reproduces the
  dark deck exactly, so an unset token means "no change":
  `--t-panel` / `--t-on-panel` (the nested-panel pair used by the stat card, quote
  box, CTA card, compare "after" column, feature tier and table pills),
  `--t-accent-soft`, `--t-on-accent`, `--t-on-coral`, `--t-mark`, `--t-hero-title`,
  `--t-stewart`, `--t-card-shadow`, `--t-tint` / `--t-tint-strong`.
- **`s-title` is modelled as panel-shaped**, since its ground is the panel fill and
  its type the on-panel colour — the same relationship every card has.
- **Footer chrome consolidated.** The logo and page-numeral rules now sit with the
  rest of the footer chrome instead of in the theme section, and both are still
  CSS-driven so markup can't pick the wrong variant.
- **Reasoning moved out of the stylesheet.** Long-form explanation lives in
  `references/`; the CSS keeps short notes. Comment volume down from 20% to ~17%.
- Verified by diffing a full per-element colour audit before and after: the dark
  deck is byte-identical, and the vibrant theme changed in exactly two places,
  both improvements — the stat card eyebrow (4.55:1 → 6.68:1) and the quote
  attribution (3.18:1 → 4.61:1, previously the deck's tightest pairing) — because
  on-panel type consolidated onto the family's deep stop.

### Removed
- **The dead `s-qa` archetype** (43 lines in `deck.css`, plus `.prompts` and
  `.chip`). It had no markup in the template, no mapping in `scripts/deck.py`, no
  layout in the `.potx`, and no mention in either reference — the Q&A slide is
  handled by `s-close`. Verified inert: the full per-element colour audit is
  byte-identical for both themes after removal.

### Fixed
- **Removed two dead type tokens.** `--type-eyebrow: 18px` and
  `--type-caption: 16px` were defined but referenced nowhere — `.eyebrow` and
  `.caption` both set 24px directly. The stale values also misrepresented those
  roles as small text when auditing contrast (24px is WCAG large scale, so the
  applicable floor is 3:1, not 4.5:1).
- **`s-close` eyebrow referenced an undefined token.** The template carried
  `style="color:var(--t-accent-soft)"`, which was defined nowhere, so the browser
  dropped it and the eyebrow rendered an inherited colour. The inline style was
  removed; `--t-accent-soft` now genuinely exists (see Refactored) and is used by
  the quote lead-in, which is what it was presumably meant for.

### Changed
- **Palette renamed to the styleguide's ladder:** `pale → light → base → dark
  → deep`, with the unsuffixed name always the saturated base. Bot Teal is the
  only family with a pale stop; Ops Indigo has no dark stop.
  **BREAKING:** `--c-amber` was `#FDD999` and is now `#F9A100` (formerly
  `--c-orange`) — a silent shift rather than an error for any deck referencing
  it directly. `--c-aqua` → `--c-teal-pale`, `--c-seafoam` → `--c-teal-light`,
  `--c-lavender` → `--c-indigo-light`, `--c-purple-dark` → `--c-indigo-deep`,
  old `--c-amber` → `--c-amber-light`, `--c-brown` → `--c-amber-dark`,
  `--c-brown-dark` → `--c-amber-deep`, `--c-pink-soft` → `--c-coral-light`,
  `--c-red-dark` → `--c-coral-dark`, `--c-burgundy` → `--c-coral-deep`.
- **The palette is now load-bearing.** 59 hardcoded hex values in `deck.css`
  were replaced with `var(--c-*)` references, leaving the palette file as the
  single source of truth. Verified as a pure refactor: all 32 slides across
  both themes rendered pixel-identical before and after. `--brand-teal` stays
  literal `#00BBB4` because the brand-compliance rule keys off it.
- **Dark theme carries no light grounds.** `s-title` is a Bot Teal field,
  section dividers are Bot Teal Dark with a Bot Teal Stewart outline, and the
  stat card and quote box moved from pale teal to Bot Teal — matching what the
  comparison, pricing, and CTA cards already did. Amber and coral remain as
  callouts only; their darker shades are not used as grounds.
- Cream (`#F5F1EA` / `#EBE3D6`) is retired. It was never in the palette.
- `s-stat` card and quote-box text moved to Bot Teal Deep; Bot Teal Dark on a
  Bot Teal fill was about 1.9:1.

### Fixed
- **Three template slides were bypassing the token system with inline styles:**
  `s-compare`'s "before" column (`background-color: rgb(14, 61, 61)`) and
  `s-image`'s section and frame (`#00BBB4`). Inline styles outrank every
  stylesheet, so these were unthemeable in *both* themes. All removed; the
  template now contains zero hardcoded hex.
- **`s-stat` shipped with an empty `<div class="stat-num"></div>`,** so any deck
  started from the template had a blank hero number. Now carries placeholders.
- `--c-brown-dark` was `#432800` against the styleguide's `#3F2900` — the same
  class of error as the `00BBB3` theme value.

### Removed
- `--t-accent-soft` from both themes.
- Five unreferenced, off-palette tokens: `--c-light-amber`, `--c-pink`,
  `--c-lavender-muted`, `--c-black-deep`, `--c-gray`.

## [1.4] — 2026-08-04

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

[Unreleased]: https://github.com/Stepherglades/rewst-slides/compare/v1.9.2...HEAD
[1.9.2]: https://github.com/Stepherglades/rewst-slides/compare/v1.9.1...v1.9.2
[1.9.1]: https://github.com/Stepherglades/rewst-slides/compare/v1.9...v1.9.1
[1.9]: https://github.com/Stepherglades/rewst-slides/compare/v1.8...v1.9
[1.8]: https://github.com/Stepherglades/rewst-slides/compare/v1.7...v1.8
[1.7]: https://github.com/Stepherglades/rewst-slides/compare/v1.6...v1.7
[1.6]: https://github.com/Stepherglades/rewst-slides/compare/v1.5...v1.6
[1.5]: https://github.com/Stepherglades/rewst-slides/compare/v1.4...v1.5
[1.4]: https://github.com/Stepherglades/rewst-slides/compare/v1.3.1...v1.4
[1.3.1]: https://github.com/Stepherglades/rewst-slides/compare/v1.3...v1.3.1
[1.3]: https://github.com/Stepherglades/rewst-slides/compare/v1.2...v1.3
[1.2]: https://github.com/Stepherglades/rewst-slides/compare/v1.1...v1.2
[1.1]: https://github.com/Stepherglades/rewst-slides/compare/v1.0...v1.1
[1.0]: https://github.com/Stepherglades/rewst-slides/releases/tag/v1.0

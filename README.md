rewst-slides

Claude skill for branded presentations in PDF, HTML, and editable PPTX.

rewst-slides builds decks that look like Rewst made them — and enforces it,
slide by slide. A deck is authored as a self-contained HTML file (the source of
truth), then exported to three formats. Brand fidelity comes first: the Rewst
palette (Bot Teal #00BBB4 as the anchor), Poppins/Montserrat type, correct
logo usage, and the rule that primary Bot Teal appears on every slide.

What's in here

PathPurposeSKILL.mdThe skill itself — workflow, brand rules, export commands.references/brand.mdPalette, type, logo, voice, and the Bot Teal rule.references/slides.mdEvery archetype, what it's for, and where teal lives.assets/deck-template.htmlStarting deck — 16 archetypes + light variants, placeholder copy.assets/deck.css, deck-stage.js, design-system/, logo/, illustrations/, fonts/The brand kit the HTML depends on.scripts/deck.pycheck (verify brand compliance) and export (write the full set).CHANGELOG.mdVersion history.

Exports

A single export always writes three deliverables:


.pdf — one page per slide, full fidelity; the share/print format.
-editable.pptx — native PowerPoint with editable text, bullet
characters, and shape autoshapes.
-html.zip — the portable self-contained deck.


Brand compliance

deck.py check renders every slide in a real browser and verifies: Bot Teal
#00BBB4 is present, no content bleeds past the right gutter, content boxes keep
minimum padding, footers show the logo and slide number, and no retired teal
remains in source. A FAIL is a real defect — decks that fail don't ship.

Installing the skill

Grab the latest .skill file from
Releases and save it into your Claude profile, or add the files
in this repo to a skill directory directly.

Versioning

Released as vMAJOR.MINOR tags. See CHANGELOG.md for what
changed in each version. The current release is v1.3.


Private repo — Rewst internal tooling.

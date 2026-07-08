# Fonts (optional, one-time)

Headings use **Poppins**, which is already installed in the render environment,
so headings export perfectly with no setup.

Body text uses **Montserrat**, which usually is *not* installed. Without it, the
PDF/PPTX exports fall back to a system sans for body copy (the live HTML deck is
unaffected — browsers load Montserrat from Google Fonts).

For pixel-perfect body text in the PDF/PPTX, drop the Montserrat `.ttf` files
here once:

    Montserrat-Regular.ttf
    Montserrat-Medium.ttf
    Montserrat-SemiBold.ttf
    Montserrat-Bold.ttf
    Montserrat-Black.ttf

`scripts/deck.py` auto-detects and embeds any `Montserrat-*.ttf` it finds in
this folder at render time. Get them from Google Fonts (Open Font License).

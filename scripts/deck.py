#!/usr/bin/env python3
"""
deck.py — render, brand-check, and export a Rewst HTML deck.

The deck is the source of truth: a self-contained HTML file whose slides are the
direct <section> children of <deck-stage>. This script renders each slide in a
real headless Chromium (so masks, pseudo-elements, web fonts, and the exact CSS
all resolve faithfully), then:

  check   verify layout compliance — right-margin gutter, box padding, footers,
          and that the retired teal (#1EAFAF / #1CAFAF) is absent from the source
  export  write <name>.pdf (one full-bleed slide per page), the editable
          <name>-editable.pptx, and the <name>-html.zip source bundle,
          carrying speaker notes into the editable PPTX notes pane
  render  just dump per-slide PNGs (mostly for debugging)

The three shipped formats are the PDF, the editable PPTX (a design-background +
native text boxes, illustrations, and markers rebuild), and the HTML bundle;
`--formats pdf,pptx,html` selects a subset. The older faithful (image-per-slide, non-editable) PPTX has
been retired from the standard set. The editable PPTX is built on the Rewst
template (assets/template/rewst-slides.potx), so the delivered file carries the
branded slide master, six layouts, and the #00BBB4 theme for hand-added slides.

Usage:
  python deck.py check  deck.html
  python deck.py export deck.html --out /mnt/user-data/outputs/deck
  python deck.py export deck.html --out out/deck --formats pdf,pptx
  python deck.py render deck.html --pngdir /tmp/slides --scale 2
"""
import argparse, base64, json, os, re, sys, tempfile, shutil
import urllib.parse, urllib.request

# Chromium lives here in this environment; harmless if already correct elsewhere.
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")

DESIGN_W, DESIGN_H = 1920, 1080
SAFE_RIGHT_PX = 110               # content right-margin safe zone (matches --pad-x)
MIN_BOX_PAD = 32                  # min internal padding inside content boxes/cards (matches --box-pad-min)
SKILL_FONTS = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
SKILL_TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "assets",
                              "template", "rewst-slides.potx")


def _font_face_css():
    """Embed Montserrat from assets/fonts if the team dropped the files in.
    Poppins is expected from the system; Montserrat usually isn't, so without
    this the body font falls back. Headings (Poppins) are unaffected."""
    if not os.path.isdir(SKILL_FONTS):
        return ""
    faces, weights = [], {"Regular": 400, "Medium": 500, "SemiBold": 600,
                          "Bold": 700, "Black": 900}
    for fn in sorted(os.listdir(SKILL_FONTS)):
        if not fn.lower().startswith("montserrat") or not fn.lower().endswith((".ttf", ".otf")):
            continue
        w = next((v for k, v in weights.items() if k.lower() in fn.lower()), 400)
        style = "italic" if "italic" in fn.lower() else "normal"
        path = os.path.abspath(os.path.join(SKILL_FONTS, fn)).replace("\\", "/")
        faces.append(f"@font-face{{font-family:'Montserrat';font-weight:{w};"
                     f"font-style:{style};src:url('file://{path}');}}")
    return "\n".join(faces)


def _build_export_html(deck_path):
    """Return a temp HTML (written next to the deck so relative asset paths
    resolve) that lays every slide out flat at design size, with no component
    JS doing show/hide or scaling."""
    html = open(deck_path, encoding="utf-8").read()
    # Don't run the deck component: without it, sections are plain flow children.
    html = re.sub(r'<script[^>]*deck-stage\.js[^>]*>\s*</script>', '', html)
    override = f"""
    <style id="__export_override__">
      html,body {{ margin:0; padding:0; background:#000; }}
      deck-stage {{ display:block; }}
      deck-stage > section {{
        display:block !important; position:relative !important;
        width:{DESIGN_W}px !important; height:{DESIGN_H}px !important;
        visibility:visible !important; opacity:1 !important;
        transform:none !important; overflow:hidden; margin:0;
      }}
      {_font_face_css()}
    </style>"""
    html = html.replace("</head>", override + "\n</head>")
    fd, tmp = tempfile.mkstemp(suffix=".html", dir=os.path.dirname(os.path.abspath(deck_path)))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html)
    return tmp


def _speaker_notes(deck_path):
    html = open(deck_path, encoding="utf-8").read()
    m = re.search(r'id="speaker-notes"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except Exception:
        return []


def render(deck_path, pngdir, scale=2):
    from playwright.sync_api import sync_playwright
    os.makedirs(pngdir, exist_ok=True)
    tmp = _build_export_html(deck_path)
    pngs = []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--no-sandbox", "--force-color-profile=srgb"])
            pg = b.new_page(viewport={"width": DESIGN_W, "height": DESIGN_H},
                            device_scale_factor=scale)
            # No network in this environment — abort external fetches so nothing hangs.
            pg.route(re.compile(r"^https?://"), lambda r: r.abort())
            pg.goto("file://" + os.path.abspath(tmp))
            try:
                pg.evaluate("document.fonts.ready")
                pg.wait_for_timeout(400)
            except Exception:
                pass
            sections = pg.query_selector_all("deck-stage > section")
            if not sections:
                sections = pg.query_selector_all("section")
            for i, sec in enumerate(sections, 1):
                out = os.path.join(pngdir, f"slide-{i:02d}.png")
                sec.screenshot(path=out)
                pngs.append(out)
            b.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return pngs


def check(deck_path, scale=1):
    (margin_ok, mrows, box_ok, brows, footer_ok, frows,
     illus_ok, irows) = check_margins(deck_path)
    print("Right-margin check (content must stay within the 110px gutter;\n"
          "bleed Stewart, panel-corner art and footers exempt) — "
          + f"{len(mrows)} slides\n" + "-" * 46)
    for r in mrows:
        if r["bad"]:
            print(f"  slide {r['s']+1:02d}  FAIL — crosses margin: {', '.join(r['bad'])}")
        else:
            print(f"  slide {r['s']+1:02d}  PASS  (rightmost {r['worst']}px ≤ 1810)")

    print(f"\nBox-padding check (cards/boxes need ≥ {MIN_BOX_PAD}px inner padding;\n"
          "chips, badges, avatars, table cells exempt) — " + f"{len(brows)} slides\n" + "-" * 46)
    for r in brows:
        if r["bad"]:
            print(f"  slide {r['s']+1:02d}  FAIL — box too tight: {', '.join(r['bad'])}")
        else:
            print(f"  slide {r['s']+1:02d}  PASS")

    print("\nFooter check (logo bottom-left + page number bottom-right on every\n"
          "slide) — " + f"{len(frows)} slides\n" + "-" * 46)
    for r in frows:
        if r["bad"]:
            print(f"  slide {r['s']+1:02d}  FAIL — {', '.join(r['bad'])}")
        else:
            print(f"  slide {r['s']+1:02d}  PASS")

    print("\nIllustration-margin check (art may bleed top/right only; must stay\n"
          "out of the footer band and off the left gutter) — " + f"{len(irows)} slides\n" + "-" * 46)
    for r in irows:
        if r["bad"]:
            print(f"  slide {r['s']+1:02d}  FAIL — {', '.join(r['bad'])}")
        else:
            print(f"  slide {r['s']+1:02d}  PASS")

    teal_src_ok, teal_hits = check_retired_teal(deck_path)
    print("\nRetired-teal check (deck source must not contain the retired "
          "#1EAFAF / #1CAFAF)\n" + "-" * 46)
    if teal_hits:
        for h in teal_hits:
            print(f"  FAIL — {h}")
    else:
        print("  PASS  (no retired teal in the deck HTML or its deck.css)")

    ok = margin_ok and box_ok and footer_ok and teal_src_ok and illus_ok
    print("-" * 46)
    print("RESULT:", "ALL CHECKS PASS ✓" if ok else "FAILURES ABOVE ✗")
    return ok


def check_retired_teal(deck_path):
    """Fail if the deck's own source (its HTML or the deck.css beside it) contains
    the retired teal #1EAFAF / #1CAFAF. Illustrations are external SVGs and are not
    scanned — their internal legacy teal is left as-is by design."""
    retired = ("#1eafaf", "#1cafaf")
    targets = [deck_path]
    css = os.path.join(os.path.dirname(os.path.abspath(deck_path)), "deck.css")
    if os.path.exists(css):
        targets.append(css)
    hits = []
    for f in targets:
        try:
            txt = open(f, encoding="utf-8", errors="ignore").read().lower()
        except Exception:
            continue
        for h in retired:
            if h in txt:
                hits.append(f"{os.path.basename(f)} contains {h.upper()}")
    return (len(hits) == 0), hits


def export(deck_path, out_base, scale=2):
    pngdir = tempfile.mkdtemp(prefix="rewst-export-")
    try:
        pngs = render(deck_path, pngdir, scale=scale)
        if not pngs:
            print("No slides rendered.", file=sys.stderr); return False
        from PIL import Image
        os.makedirs(os.path.dirname(os.path.abspath(out_base)) or ".", exist_ok=True)

        # ---- PDF: one full-bleed slide per page ----
        frames = [Image.open(p).convert("RGB") for p in pngs]
        pdf_path = out_base + ".pdf"
        frames[0].save(pdf_path, save_all=True, append_images=frames[1:], resolution=150.0)

        # NOTE: the faithful (image-per-slide, non-editable) PPTX has been
        # intentionally removed from the standard deliverable set. The three
        # shipped formats are the PDF (this function), the editable PPTX
        # (export_editable), and the HTML bundle (export_html_bundle). To restore
        # the faithful PPTX, re-add a python-pptx block here that pastes each PNG
        # full-bleed onto a 13.333x7.5in blank slide with speaker notes, saved as
        # out_base + ".pptx".

        print(f"Exported {len(pngs)} slides:\n  {pdf_path}")
        return True
    finally:
        shutil.rmtree(pngdir, ignore_errors=True)


# Text elements to lift out as editable boxes. Curated to this template, plus a
# pure-text-leaf fallback for anything not in the list. Generated content
# (agenda counters via counter(), checkmarks) has no DOM text, so it is never
# matched here and stays baked into the background image — which is what we want.
_EXTRACT_JS = r"""
() => {
  // Read the text as it visually wraps in the design (Chromium, with
  // text-wrap: balance applied) so the editable PPTX can reproduce the exact
  // same line breaks — no re-wrapping, no widows, stable across viewers.
  const visualLines = (e) => {
    const lines = []; let cur = []; let curTop = null;
    const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT, null);
    let node;
    while (node = w.nextNode()) {
      const s = node.nodeValue; if (!s || !s.trim()) { continue; }
      const re = /\s*\S+/g; let m;
      while (m = re.exec(s)) {
        const rng = document.createRange();
        rng.setStart(node, m.index); rng.setEnd(node, m.index + m[0].length);
        const rects = rng.getClientRects(); if (!rects.length) continue;
        const top = Math.round(rects[0].top);
        if (curTop === null) curTop = top;
        if (Math.abs(top - curTop) > 4) { lines.push(cur.join("").trim()); cur = []; curTop = top; }
        cur.push(m[0]);
      }
    }
    if (cur.length) lines.push(cur.join("").trim());
    return lines.filter(x => x.length);
  };
  const SEL = ".eyebrow,.h-display,.h-title,.h-2,.h-3,.h-4,.body,.body-sm,.caption," +
              ".num,.stat-num,.label,.dur,.name,.role,.price,.per,.desc,.lbl,.ribbon," +
              ".qtext,.qname,.qrole,.badge,.heading,.lead,td,th,.contacts div,li";
  const cand = new Set();
  document.querySelectorAll("deck-stage > section " + SEL).forEach(e => cand.add(e));
  document.querySelectorAll("deck-stage > section *").forEach(e => {
    if (e.children.length === 0 && e.textContent.trim()) cand.add(e);
  });
  const sections = [...document.querySelectorAll("deck-stage > section")];
  const out = [];
  sections.forEach((sec, si) => {
    const sr = sec.getBoundingClientRect();
    cand.forEach(e => {
      if (!sec.contains(e)) return;
      for (const d of e.querySelectorAll("*")) if (cand.has(d)) return; // keep leaves
      let txt = (e.innerText || "").trim();
      if (!txt && e.classList.contains("num")) {
        // Agenda numbers are drawn by a CSS counter, so there's no text node to
        // lift. Resolve the value from the item's position so it becomes a real,
        // editable box (marking the span hides the baked counter via !important).
        const li = e.closest("li"), ol = e.closest("ol");
        if (li && ol) {
          const idx = [...ol.children].filter(c => c.tagName === "LI").indexOf(li) + 1;
          if (idx > 0) txt = String(idx).padStart(2, "0");
        }
      }
      if (!txt) return;
      const r = e.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) return;
      const cs = getComputedStyle(e);
      e.setAttribute("data-edit-hide", "1");
      const pl = parseFloat(cs.paddingLeft) || 0, pr = parseFloat(cs.paddingRight) || 0;
      const pt = parseFloat(cs.paddingTop) || 0, pb = parseFloat(cs.paddingBottom) || 0;
      const centered = (cs.display.indexOf("flex") >= 0 || cs.display.indexOf("grid") >= 0)
                       && cs.justifyContent === "center" && cs.alignItems === "center";
      let bx = r.left - sr.left + pl, by = r.top - sr.top + pt;
      let bw = r.width - pl - pr, bh = r.height - pt - pb;
      // List markers: for a real <ol>/<ul> item whose marker is a plain number or
      // a plain bullet, emit a NATIVE, editable PPTX marker (PowerPoint draws it)
      // instead of baking it into the background. Custom/semantic glyphs (✓/✕ etc.)
      // are left exactly as before — baked, with the box shifted past them.
      // List markers: for a real <ol>/<ul> item, reproduce the marker as a NATIVE,
      // editable PPTX marker (PowerPoint draws it) so it reflows and stays aligned
      // when the text is edited — the whole point of the editable PPTX. We read the
      // item's actual ::before to recover the glyph + brand color:
      //   • an SVG check/cross (compare, pricing)  -> ✓ / ✕ in the SVG's stroke color
      //   • a solid bar/dot (timeline)             -> – / • in that color
      //   • a genuine text glyph                   -> that glyph
      // Ordered lists get a real auto-number. The exact SVG stroke shape isn't
      // pixel-reproduced (Unicode glyph instead) — an accepted trade for editability.
      let bullet = null, marL = 0;
      if (e.tagName === "LI") {
        const listEl = e.closest("ol, ul");
        if (listEl) {
          if (listEl.tagName === "OL") {
            // Each item is its own text box, so numbering can't count across boxes —
            // pin the value with startAt. Still a real auto-number: reflows, and
            // re-typing keeps it numeric.
            const idx = [...listEl.children].filter(c => c.tagName === "LI").indexOf(e) + 1;
            bullet = { kind: "num", scheme: "arabicPeriod", startAt: idx > 0 ? idx : 1 };
          } else {
            const hexToRgb = (h) => { const n = parseInt(h, 16);
              return `rgb(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255})`; };
            const bcs = getComputedStyle(e, "::before");
            const raw = (bcs.content || "").replace(/^["']|["']$/g, "").trim();
            const bgImg = bcs.backgroundImage || "";
            const bgCol = bcs.backgroundColor || "";
            let glyph = null, gcolor = null;
            if (raw && raw !== "none" && raw !== "normal") {
              glyph = raw; gcolor = bcs.color;                 // a genuine text glyph
            } else if (bgImg && bgImg !== "none" && bgImg.indexOf("url(") === 0) {
              const cm = bgImg.match(/(?:stroke|fill)=['"]?%23([0-9A-Fa-f]{6})/);
              gcolor = cm ? hexToRgb(cm[1]) : bcs.color;       // SVG marker
              if (/polyline/i.test(bgImg)) glyph = "\u2713";        // ✓ check
              else if ((bgImg.match(/<line/gi) || []).length >= 2) glyph = "\u2715"; // ✕ cross
              else glyph = "\u2022";                                 // • fallback
            } else if (bgCol && bgCol !== "transparent" && bgCol !== "rgba(0, 0, 0, 0)") {
              const w = parseFloat(bcs.width) || 0, h = parseFloat(bcs.height) || 0;
              glyph = (w > h * 1.5) ? "\u2013" : "\u2022";     // – bar, else • dot
              gcolor = bgCol;
            }
            if (glyph) bullet = { kind: "char", char: glyph, color: gcolor };
            // no detectable marker (e.g. a card list) -> leave unchanged, no bullet
          }
        }
      }
      if (!centered) {
        // Horizontal only: start the box at the ACTUAL text, clearing any marker
        // in front of it (a list's left padding OR an inline ::before ✓/✕/• flex
        // marker) and extend to the content edge — this keeps bullets/numbers and
        // hanging indents aligned. Vertical stays on the element content box so
        // large-type items (e.g. a big stat number) never ride up into a neighbor.
        try {
          const rng = document.createRange(); rng.selectNodeContents(e);
          const tr = rng.getBoundingClientRect();
          if (tr && tr.width > 0.5 && tr.height > 0.5) {
            if (bullet) {
              // Anchor the box at the item's border box — the marker origin, where
              // the design's ::before sits (a padded list's bx is otherwise on the
              // content box, past the marker) — and record the marker-to-text gap
              // as the hanging indent, so PowerPoint's native marker lands where
              // the design's did, with the design's gap before the text begins.
              bx = r.left - sr.left;
              bw = r.width - pr;
              marL = Math.max((tr.left - sr.left) - bx, 0);
            } else {
              bx = tr.left - sr.left;
              bw = Math.max((r.right - pr) - tr.left, tr.width);
            }
          }
        } catch (_) {}
      }
      if (bullet) e.setAttribute("data-edit-marker", "1");
      out.push({
        s: si, x: bx, y: by, w: bw, h: bh,
        text: txt, lines: visualLines(e),
        size: parseFloat(cs.fontSize) || 16, weight: cs.fontWeight,
        color: cs.color, align: cs.textAlign, family: cs.fontFamily,
        transform: cs.textTransform, lh: cs.lineHeight, ls: cs.letterSpacing,
        footer: !!e.closest(".pageno, .brand-mark"),
        centered: centered,
        bullet: bullet, marL: marL
      });
    });
  });
  return out;
}
"""


# Decorative timeline/roadmap dots. These are the small colored circles that sit
# under each column's label on the s-timeline archetype. Left baked into the
# background they can't be recolored or nudged in PowerPoint, so we lift each one
# into a NATIVE, editable PPTX oval at its exact position/size/color and mark it
# (data-edit-shape) so it's dropped from the background screenshot. Scoped to the
# s-timeline archetype only.
_SHAPES_JS = r"""
() => {
  const sections = [...document.querySelectorAll("deck-stage > section")];
  const out = [];
  sections.forEach((sec, si) => {
    if (!sec.classList.contains("s-timeline")) return;
    const sr = sec.getBoundingClientRect();
    sec.querySelectorAll(".qtr .dot").forEach(e => {
      const r = e.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) return;
      const cs = getComputedStyle(e);
      e.setAttribute("data-edit-shape", "1");
      out.push({
        s: si,
        x: r.left - sr.left, y: r.top - sr.top,
        w: r.width, h: r.height,
        color: cs.backgroundColor
      });
    });
  });
  return out;
}
"""


# Illustrations. Lifted out of the background image and placed as NATIVE PPTX
# pictures so they can be swapped, moved, or resized in PowerPoint — swapping art
# is the single most likely edit anyone makes to a delivered deck.
#
# Scoped by SOURCE PATH, not by class: any <img> served out of illustrations/.
# That deliberately catches the unclassed pieces in s-image and s-quote, and just
# as deliberately excludes the logo lockups (logo/rewst-logo*.png), which stay
# baked — the logo is fixed brand furniture and nobody should be nudging it.
#
# The one subtlety is object-fit. Every fixed-size art slot uses `contain`, so
# the painted art is letterboxed inside a larger element box; the element rect is
# NOT the art's rect. Placing a picture at the element rect would stretch it to
# fill. We resolve the painted rect from naturalWidth/Height (every approved SVG
# carries intrinsic width/height plus a viewBox, so these are reliable) and from
# object-position, which is NOT always centered — .ic-item anchors `left bottom`,
# .illus-topright `right top`, and so on. Computed object-position comes back as
# two components, each `N%` or `Npx`; a percentage distributes the free space
# (CSS Images 3 §5.4: offset = (box - painted) * p). Where object-fit is the
# default `fill`, the element rect IS the painted rect and the art is stretched —
# reproducing that keeps the PPTX identical to the PDF, which is the contract.
_ILLUS_JS = r"""
() => {
  const sections = [...document.querySelectorAll("deck-stage > section")];
  const out = [];
  sections.forEach((sec, si) => {
    const sr = sec.getBoundingClientRect();
    sec.querySelectorAll('img[src*="illustrations/"]').forEach(e => {
      const r = e.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) return;
      const cs = getComputedStyle(e);
      if (cs.display === "none" || cs.visibility === "hidden") return;
      if (parseFloat(cs.opacity) === 0) return;
      let x = r.left - sr.left, y = r.top - sr.top, w = r.width, h = r.height;
      const nw = e.naturalWidth || 0, nh = e.naturalHeight || 0;
      if (cs.objectFit === "contain" && nw > 0 && nh > 0) {
        const k = Math.min(w / nw, h / nh), pw = nw * k, ph = nh * k;
        // offset = (free space) * percentage, or a raw px length (CSS Images 3)
        const pos = (cs.objectPosition || "50% 50%").split(" ");
        const off = (comp, free) => {
          const v = parseFloat(comp) || 0;
          return (comp || "").endsWith("%") ? free * v / 100 : v;
        };
        x += off(pos[0], w - pw); y += off(pos[1] || "50%", h - ph);
        w = pw; h = ph;
      }
      e.setAttribute("data-edit-illus", "1");
      out.push({
        s: si,
        x: Math.round(x * 100) / 100, y: Math.round(y * 100) / 100,
        w: Math.round(w * 100) / 100, h: Math.round(h * 100) / 100,
        src: e.currentSrc || e.src,
        opacity: parseFloat(cs.opacity) || 1
      });
    });
  });
  return out;
}
"""


_MARGIN_JS = r"""
() => {
  const SAFE_RIGHT = 1920 - 110;     // content must not paint past this x
  const TOL = 3;
  const sections = [...document.querySelectorAll("deck-stage > section")];
  return sections.map((sec, si) => {
    const sr = sec.getBoundingClientRect();
    let worst = 0; const bad = [];
    sec.querySelectorAll("*").forEach(e => {
      // exempt: bleed art + footers. .illus-panel-corner hangs off a panel's top
      // corner and is allowed to cross the gutter by design (see deck.css).
      if (e.closest(".bleed-stewart, .illus-panel-corner, .pageno, .brand-mark")) return;
      const cs = getComputedStyle(e);
      if (cs.visibility === "hidden" || cs.display === "none" || parseFloat(cs.opacity) === 0) return;
      const hasText = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      const hasBg = cs.backgroundColor && cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== "transparent";
      const hasBgImg = cs.backgroundImage && cs.backgroundImage !== "none";
      const hasBorder = parseFloat(cs.borderRightWidth) > 0 && cs.borderRightStyle !== "none";
      const isImg = e.tagName === "IMG" || e.tagName === "svg";
      if (!(hasText || hasBg || hasBgImg || hasBorder || isImg)) return;  // paints nothing at its edge
      const right = e.getBoundingClientRect().right - sr.left;
      if (right > worst) worst = right;
      if (right > SAFE_RIGHT + TOL) {
        const cls = (typeof e.className === "string" ? e.className : "").trim().split(/\s+/).slice(0, 2).join(".");
        bad.push((e.tagName.toLowerCase() + (cls ? "." + cls : "")) + " @" + Math.round(right) + "px");
      }
    });
    return { s: si, worst: Math.round(worst), bad: [...new Set(bad)] };
  });
}
"""


_ILLUS_MARGIN_JS = r"""
() => {
  // Illustrations may bleed at the TOP and RIGHT only (the panel-corner hang,
  // the header-band slot). They must NEVER enter the bottom footer band — the
  // logo and page number live there — and never cross the left gutter. This
  // rule exists because an unconstrained agenda illustration once ran straight
  // over the brand mark. The bleed Stewart is art with its own placement rules
  // and is exempt; logos/footer imagery are the thing being protected, so they
  // are not treated as illustrations.
  const SAFE_BOTTOM = 1080 - 130;   // top of the footer band (matches --pad-bottom)
  const SAFE_LEFT   = 110;          // left gutter (matches --pad-x)
  const TOL = 3;
  const SEL = "img.ic-item, img.ic, img.illus-col, img.illus-corner, " +
              "img.illus-topright, img.illus-panel-corner, .art img, .frame img";
  const sections = [...document.querySelectorAll("deck-stage > section")];
  return sections.map((sec, si) => {
    const sr = sec.getBoundingClientRect();
    const bad = [];
    sec.querySelectorAll(SEL).forEach(e => {
      if (e.closest(".bleed-stewart, .brand-mark, .pageno")) return;
      const cs = getComputedStyle(e);
      if (cs.visibility === "hidden" || cs.display === "none" || parseFloat(cs.opacity) === 0) return;
      const r = e.getBoundingClientRect();
      const bottom = r.bottom - sr.top, left = r.left - sr.left;
      const cls = (typeof e.className === "string" ? e.className : "").trim().split(/\s+/).slice(0, 2).join(".");
      const tag = "img" + (cls ? "." + cls : "");
      if (bottom > SAFE_BOTTOM + TOL) bad.push(tag + " bottom @" + Math.round(bottom) + "px (limit " + SAFE_BOTTOM + ")");
      if (left < SAFE_LEFT - TOL)     bad.push(tag + " left @" + Math.round(left) + "px (limit " + SAFE_LEFT + ")");
    });
    return { s: si, bad: [...new Set(bad)] };
  });
}
"""


_FOOTER_JS = r"""
() => {
  const W = 1920, H = 1080;
  const sections = [...document.querySelectorAll("deck-stage > section")];
  const vis = el => {
    if (!el) return null;
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden" || parseFloat(cs.opacity) === 0) return null;
    const r = el.getBoundingClientRect();
    return (r.width > 0 && r.height > 0) ? r : null;
  };
  return sections.map((sec, si) => {
    const bad = [];
    const sr = sec.getBoundingClientRect();
    const bm = vis(sec.querySelector(".brand-mark"));
    const pg = vis(sec.querySelector(".pageno"));
    // Title + divider slides carry the bleed Stewart in the lower-right, so the
    // page number is intentionally dropped there to avoid colliding with it.
    const hasStewart = !!sec.querySelector(".bleed-stewart");
    if (!bm) bad.push("logo missing/hidden");
    else {
      const cx = (bm.left + bm.right) / 2 - sr.left, by = bm.bottom - sr.top;
      if (cx > W / 2) bad.push("logo not on the left");
      if (by < H - 220) bad.push("logo not at the bottom");
    }
    if (!pg) { if (!hasStewart) bad.push("page number missing/hidden"); }
    else {
      const cx = (pg.left + pg.right) / 2 - sr.left, by = pg.bottom - sr.top;
      if (cx < W / 2) bad.push("page number not on the right");
      if (by < H - 220) bad.push("page number not at the bottom");
    }
    return { s: si, bad };
  });
}
"""


def check_margins(deck_path):
    """One page load, layout rules:
    - right margin: no content paints past the right gutter (the bleed Stewart,
      the .illus-panel-corner art, and the footers are exempt)
    - box padding: content boxes/cards keep a minimum internal padding so content
      never touches the box edge (small chips, badges, avatars, table cells exempt)
    - footers: every slide shows the logo bottom-left and the page number bottom-right
    - illustration margins: art may bleed top/right only; it never enters the
      bottom footer band and never crosses the left gutter
    Returns (margin_ok, margin_rows, box_ok, box_rows, footer_ok, footer_rows,
    illus_ok, illus_rows)."""
    from playwright.sync_api import sync_playwright
    tmp = _build_export_html(deck_path)
    boxpad_js = (r"""
    () => {
      const MIN = __MIN__, TOL = 0.5;
      const sections = [...document.querySelectorAll("deck-stage > section")];
      return sections.map((sec, si) => {
        const bad = [];
        sec.querySelectorAll("*").forEach(e => {
          // exempt small UI chips, badges, ribbons, circular avatars, and footers
          if (e.closest(".pill, .badge, .ribbon, .avatar, .pageno, .brand-mark, .dot")) return;
          const cs = getComputedStyle(e);
          if (cs.visibility === "hidden" || cs.display === "none") return;
          const bg = cs.backgroundColor;
          const opaque = bg && bg !== "transparent" && !bg.startsWith("rgba(0, 0, 0, 0");
          if (!opaque) return;                                   // only filled boxes
          const r = e.getBoundingClientRect();
          if (Math.min(r.width, r.height) < 150) return;         // chips/tags, not cards
          if (!((e.innerText || "").trim())) return;             // image frames have no text
          const pad = {
            left: parseFloat(cs.paddingLeft) || 0, right: parseFloat(cs.paddingRight) || 0,
            top: parseFloat(cs.paddingTop) || 0, bottom: parseFloat(cs.paddingBottom) || 0,
          };
          const tight = Object.entries(pad).filter(([k, v]) => v < MIN - TOL);
          if (tight.length) {
            const cls = (typeof e.className === "string" ? e.className : "").trim().split(/\s+/).slice(0, 2).join(".");
            bad.push((e.tagName.toLowerCase() + (cls ? "." + cls : "")) +
                     " [" + tight.map(([k, v]) => k + ":" + Math.round(v)).join(", ") + "]");
          }
        });
        return { s: si, bad: [...new Set(bad)] };
      });
    }
    """).replace("__MIN__", str(MIN_BOX_PAD))
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--no-sandbox"])
            pg = b.new_page(viewport={"width": DESIGN_W, "height": DESIGN_H})
            pg.route(re.compile(r"^https?://"), lambda r: r.abort())
            pg.goto("file://" + os.path.abspath(tmp))
            try:
                pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
            except Exception:
                pass
            mrows = pg.evaluate(_MARGIN_JS)
            brows = pg.evaluate(boxpad_js)
            frows = pg.evaluate(_FOOTER_JS)
            irows = pg.evaluate(_ILLUS_MARGIN_JS)
            b.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    margin_ok = all(not r["bad"] for r in mrows)
    box_ok = all(not r["bad"] for r in brows)
    footer_ok = all(not r["bad"] for r in frows)
    illus_ok = all(not r["bad"] for r in irows)
    return margin_ok, mrows, box_ok, brows, footer_ok, frows, illus_ok, irows


def _rgb_hex(css_color):
    import re as _re
    m = _re.findall(r"[\d.]+", css_color or "")
    if len(m) >= 3:
        r, g, b = (int(round(float(x))) for x in m[:3])
        return f"{r:02X}{g:02X}{b:02X}"
    return "000000"


def _first_family(css_family):
    fam = (css_family or "").split(",")[0].strip().strip('"').strip("'")
    return fam or "Montserrat"


def _url_to_path(u):
    """file:// URL -> local path. Returns None for anything else."""
    try:
        p = urllib.parse.urlparse(u or "")
        if p.scheme == "file":
            return urllib.request.url2pathname(p.path)
    except Exception:
        pass
    return None


def _rasterize_illustrations(browser, illus, outdir, scale=2):
    """Raster each illustration on a TRANSPARENT ground, at its layout size.

    Screenshotting the <img> in the deck itself would bake the slide ground in
    behind it (an element screenshot captures the composited page, and every
    slide has a painted ground), so the picture would arrive in PowerPoint as
    art sitting on an opaque teal rectangle. Instead each SVG is re-rendered
    alone, inlined as a data URI to sidestep file:// origin rules, and captured
    with omit_background so the alpha survives.

    Identical (src, width, height) triples are rendered once and shared.
    """
    cache, page = {}, None
    for it in illus:
        path = _url_to_path(it.get("src"))
        it["png"] = it["svg"] = None
        if not path or not os.path.isfile(path):
            continue
        it["svg"] = path
        w = max(int(round(it["w"])), 1)
        h = max(int(round(it["h"])), 1)
        key = (path, w, h)
        if key in cache:
            it["png"] = cache[key]
            continue
        try:
            if page is None:
                page = browser.new_page(device_scale_factor=scale)
            with open(path, "rb") as f:
                uri = "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode()
            page.set_viewport_size({"width": w + 8, "height": h + 8})
            page.set_content(
                '<body style="margin:0;background:transparent">'
                f'<img id="a" src="{uri}" style="display:block;width:{w}px;height:{h}px">'
                "</body>")
            page.wait_for_function("document.getElementById('a').complete", timeout=5000)
            out = os.path.join(outdir, "illus-%03d.png" % len(cache))
            page.locator("#a").screenshot(path=out, omit_background=True)
            cache[key] = it["png"] = out
        except Exception as e:
            print(f"note: could not rasterize {os.path.basename(path)} ({e}); "
                  f"leaving it baked into the background", file=sys.stderr)
            it["png"] = None
    if page is not None:
        page.close()
    return illus


def _render_textless_and_extract(deck_path, scale=2):
    """One page load: pull every text box's geometry+style, then hide that text
    and screenshot each section as the editable slide's background."""
    from playwright.sync_api import sync_playwright
    tmp = _build_export_html(deck_path)
    pngdir = tempfile.mkdtemp(prefix="rewst-edit-bg-")
    pngs, illus = [], []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--no-sandbox", "--force-color-profile=srgb"])
            pg = b.new_page(viewport={"width": DESIGN_W, "height": DESIGN_H},
                            device_scale_factor=scale)
            pg.route(re.compile(r"^https?://"), lambda r: r.abort())
            pg.goto("file://" + os.path.abspath(tmp))
            try:
                pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
            except Exception:
                pass
            boxes = pg.evaluate(_EXTRACT_JS)
            # decorative timeline dots -> lifted to native ovals (see _SHAPES_JS)
            shapes = pg.evaluate(_SHAPES_JS)
            # illustrations -> lifted to native pictures (see _ILLUS_JS). Raster
            # them BEFORE the hide rule lands: geometry is already captured, but
            # the source <img> elements must still be live to resolve.
            illus = pg.evaluate(_ILLUS_JS)
            illus = _rasterize_illustrations(b, illus, pngdir, scale=scale)
            # A rasterize failure leaves png=None; un-mark those so they stay
            # painted in the background rather than vanishing from the slide.
            # Document order is identical on both sides, so index maps 1:1.
            if any(not i.get("png") for i in illus):
                pg.evaluate(
                    "(keep) => document.querySelectorAll('[data-edit-illus]')"
                    ".forEach((e, i) => { if (!keep[i]) e.removeAttribute('data-edit-illus'); })",
                    [bool(i.get("png")) for i in illus])
            illus = [i for i in illus if i.get("png")]
            # Drop everything that was lifted, keep the rest (cards, dividers,
            # pills, badges, masked glyphs, the Stewart bleed). All text lifts
            # into native boxes — including the agenda numbers, whose CSS counter
            # is hidden here and re-emitted as real text. The timeline column
            # dots (data-edit-shape) and the illustrations (data-edit-illus) are
            # dropped and redrawn native so they stay editable.
            # visibility:hidden (not display:none) throughout — it stops the
            # paint without changing layout, so the background screenshot keeps
            # the exact geometry the lifted objects were measured against. Safe
            # on <img>, which has no children to take down with it.
            pg.add_style_tag(content="[data-edit-hide]{color:transparent !important;"
                                     "text-shadow:none !important;}"
                                     "[data-edit-shape]{visibility:hidden !important;}"
                                     "[data-edit-illus]{visibility:hidden !important;}"
                                     "[data-edit-marker]::before{display:none !important;}"
                                     "[data-edit-marker]::marker{color:transparent !important;}"
                                     "[data-edit-marker]{list-style:none !important;}")
            for i, sec in enumerate(pg.query_selector_all("deck-stage > section"), 1):
                out = os.path.join(pngdir, f"bg-{i:02d}.png")
                sec.screenshot(path=out); pngs.append(out)
            b.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return pngs, boxes, shapes, illus, pngdir


def _branded_presentation():
    """Open the deck on the Rewst .potx so its slide master, six branded
    layouts, and theme (Bot Teal #00BBB4 palette + Poppins/Montserrat) ship
    inside the delivered PPTX. The generated slides look identical — every
    slide carries its full-bleed design background and self-styled text runs —
    but anyone adding a new slide in PowerPoint gets the real branded layouts,
    and the theme palette shows in the color picker.

    python-pptx refuses the .potx content type, so the template is copied to a
    temp .pptx with the main content type patched from
    presentationml.template to presentationml.presentation. The .potx in
    assets/template/ stays the editable source of truth.

    Returns (Presentation, base_layout, is_branded). Falls back to the plain
    python-pptx default (blank layout 6) if the template is missing or
    unreadable, so export never breaks over branding."""
    from pptx import Presentation
    try:
        if os.path.isfile(SKILL_TEMPLATE):
            import zipfile
            fd, tmp = tempfile.mkstemp(suffix=".pptx")
            os.close(fd)
            try:
                with zipfile.ZipFile(SKILL_TEMPLATE) as zin, \
                     zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        data = zin.read(item.filename)
                        if item.filename == "[Content_Types].xml":
                            data = data.replace(
                                b"presentationml.template.main+xml",
                                b"presentationml.presentation.main+xml")
                        zout.writestr(item, data)
                prs = Presentation(tmp)
                # Base generated slides on the layout with the fewest
                # placeholders; the clones are stripped per slide anyway.
                base = min(prs.slide_layouts,
                           key=lambda l: len(l.placeholders))
                return prs, base, True
            finally:
                os.unlink(tmp)
    except Exception as e:
        print(f"note: branded template unavailable ({e}); "
              f"using plain PPTX base", file=sys.stderr)
    prs = Presentation()
    return prs, prs.slide_layouts[6], False


def _set_speaker_notes(slide, text):
    """Write speaker notes, building the body placeholder if the template's
    notes master doesn't supply one.

    python-pptx makes a new notes slide by cloning the notes master's shape
    tree, then hands back the placeholder it finds. The Rewst .potx carries a
    notes master with an EMPTY spTree — no placeholders at all — so the clone
    has nowhere to put text and `notes_text_frame` comes back None. Before the
    template shipped a notes master, python-pptx fell back to its own default
    (which has a body), and this worked by luck rather than design.

    So: if the clone came back without a text frame, add the standard body
    placeholder ourselves. Geometry is the PowerPoint default for a 7.5x10in
    notes page (notesSz 6858000 x 9144000 EMU) — bottom half of the page,
    under the slide image."""
    from pptx.oxml import parse_xml
    from pptx.oxml.ns import nsdecls
    ns = slide.notes_slide
    tf = ns.notes_text_frame
    if tf is None:
        ns.shapes._spTree.append(parse_xml(
            '<p:sp %s>'
            '<p:nvSpPr>'
            '<p:cNvPr id="2" name="Notes Placeholder 1"/>'
            '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr>'
            '</p:nvSpPr>'
            '<p:spPr><a:xfrm>'
            '<a:off x="685800" y="4343400"/>'
            '<a:ext cx="5486400" cy="4114800"/>'
            '</a:xfrm></p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>'
            '</p:sp>' % nsdecls("p", "a")))
        tf = ns.notes_text_frame
    if tf is None:                      # still nothing — don't kill the export
        return False
    tf.text = text
    return True


def _template_slide_ids(prs):
    """The <p:sldId> elements the .potx shipped with, before generation.

    The template carries one real slide — "Supporting graphics", a library of
    the brand's SVG spot art — and it is meant to survive into the delivered
    PPTX so a presenter has the pieces to hand. Capture its id element up front;
    _move_template_slides_to_end puts it back after the generated deck.

    Returns [] for a template with no slides, which is what a stock .potx and
    the plain python-pptx fallback both look like."""
    try:
        return list(prs.slides._sldIdLst)
    except Exception:
        return []


def _move_template_slides_to_end(prs, template_ids):
    """Send the template's own slides to the back of the deck.

    python-pptx appends every add_slide() after whatever is already in
    <p:sldIdLst>, so a template that ships a slide emits it FIRST — the
    Supporting graphics library would open the presentation. Reordering the id
    list is the whole move: the slide parts and their relationships are
    untouched, only the order PowerPoint reads them in changes.

    Wrapped, like the rest of the template handling: a failure here should cost
    the ordering, not the export."""
    if not template_ids:
        return
    try:
        lst = prs.slides._sldIdLst
        for el in template_ids:
            lst.remove(el)
            lst.append(el)
    except Exception as e:
        print(f"note: could not move the template slide(s) to the end ({e}); "
              f"they stay at the front", file=sys.stderr)


# The Office 2016 SVG extension. A picture is stored as a PNG blip (the fallback
# every viewer understands) with the source SVG hung off it in an extLst; a
# PowerPoint that knows the extension draws the vector and ignores the raster.
_SVG_EXT_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
_SVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"


def _lock_background(pic):
    """Name the full-bleed background picture and mark it no-move / no-resize.

    The background is the one shape on a generated slide that is never a
    legitimate edit target: the slide IS that picture, and every text box and
    illustration above it is positioned in absolute EMU against its frame. A
    stray drag while editing copy — it's the thing under every click that misses
    a text box — shifts the whole design out from under content that doesn't
    move with it, and nothing about the result looks like an accident.

    noMove + noResize only, deliberately. `noSelect` would also make the
    background unclickable and therefore undeletable, turning "get this out of
    my way" into a dead end with no in-app escape; these two stop the actual
    accident while leaving every intentional action available. The name carries
    "(locked)" because PowerPoint's selection pane shows no lock indicator for
    these two flags, so otherwise a refused drag looks like a broken file.

    Caveat worth keeping in mind: PowerPoint's honouring of `picLocks` is uneven
    across versions and historically weakest on Mac. This is a guard rail, not a
    guarantee — an edition that ignores it renders exactly as before.

    Wrapped like the rest of the raw-XML handling: a failure here costs the lock,
    not the export.
    """
    from pptx.oxml.ns import qn
    try:
        pic.name = "Background - slide design (locked)"
    except Exception:
        pass
    try:
        cNvPicPr = pic._element.nvPicPr.find(qn("p:cNvPicPr"))
        if cNvPicPr is None:
            return False
        # python-pptx already writes <a:picLocks noChangeAspect="1"/> here, so
        # the usual case is adding attributes to an existing element. Build one
        # only if that ever stops being true, and insert at 0 — picLocks precedes
        # extLst in CT_NonVisualPictureProperties, so a blind append is wrong.
        locks = cNvPicPr.find(qn("a:picLocks"))
        if locks is None:
            locks = cNvPicPr.makeelement(qn("a:picLocks"), {})
            cNvPicPr.insert(0, locks)
        locks.set("noMove", "1")
        locks.set("noResize", "1")
        return True
    except Exception as e:
        print(f"note: could not lock the background picture ({e}); "
              f"it stays movable", file=sys.stderr)
        return False


def _dress_picture(pic, slide_part, svg_path=None, opacity=1.0, svg_cache=None):
    """Add the vector upgrade and any CSS opacity to a placed PNG picture.

    Both are raw XML on the blip — python-pptx has no API for either — so both
    are individually wrapped: a failure here degrades to the plain raster
    picture, which still looks right and is still swappable. It never takes the
    export down. Child order inside CT_Blip matters: alphaModFix before extLst.

    svg_cache holds one image part per source file for the whole package. Without
    it each placement writes its own copy, and the template repeats a single
    ~90KB illustration up to four times — python-pptx dedupes rasters by hash,
    but these SVG parts are hand-built so nothing dedupes them for us.
    """
    from pptx.opc.package import Part
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    from pptx.oxml.ns import qn
    blip = pic._element.blipFill.blip
    if opacity is not None and opacity < 0.999:
        try:
            amt = max(0, min(100000, int(round(float(opacity) * 100000))))
            blip.append(blip.makeelement(qn("a:alphaModFix"), {"amt": str(amt)}))
        except Exception:
            pass
    if not svg_path or not os.path.isfile(svg_path):
        return False
    try:
        key = os.path.abspath(svg_path)
        part = (svg_cache or {}).get(key)
        if part is None:
            with open(svg_path, "rb") as f:
                blob = f.read()
            pkg = slide_part.package
            part = Part(pkg.next_partname("/ppt/media/illustration%d.svg"),
                        "image/svg+xml", pkg, blob)
            if svg_cache is not None:
                svg_cache[key] = part
        rId = slide_part.relate_to(part, RT.IMAGE)
        extLst = blip.makeelement(qn("a:extLst"), {})
        ext = blip.makeelement(qn("a:ext"), {"uri": _SVG_EXT_URI})
        ext.append(blip.makeelement("{%s}svgBlip" % _SVG_NS, {qn("r:embed"): rId}))
        extLst.append(ext)
        blip.append(extLst)
        return True
    except Exception as e:
        print(f"note: SVG vector upgrade unavailable ({e}); "
              f"illustration stays raster", file=sys.stderr)
        return False


def export_editable(deck_path, out_base, scale=2):
    """Hybrid editable PPTX: full-bleed design background + native text boxes."""
    from PIL import Image  # noqa: F401 (ensures Pillow present)
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.oxml.ns import qn
    pngs, boxes, shapes, illus, pngdir = _render_textless_and_extract(deck_path, scale=scale)
    try:
        if not pngs:
            print("No slides rendered.", file=sys.stderr); return False
        prs, blank, branded = _branded_presentation()
        # Grab these before any add_slide() call — afterwards the generated
        # slides are in the same list and there's no way to tell them apart.
        template_ids = _template_slide_ids(prs)
        prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
        EMU_PER_PX = prs.slide_width / DESIGN_W            # 1920px -> 13.333in
        PT_PER_PX = 0.5                                     # 1920px == 960pt
        notes = _speaker_notes(deck_path)
        align_map = {"center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT,
                     "justify": PP_ALIGN.JUSTIFY, "left": PP_ALIGN.LEFT,
                     "start": PP_ALIGN.LEFT, "end": PP_ALIGN.RIGHT}
        by_slide = {}
        for bx in boxes:
            by_slide.setdefault(bx["s"], []).append(bx)
        shapes_by_slide = {}
        for sh in shapes:
            shapes_by_slide.setdefault(sh["s"], []).append(sh)
        illus_by_slide = {}
        for il in illus:
            illus_by_slide.setdefault(il["s"], []).append(il)
        svg_cache = {}          # one SVG image part per source file, package-wide

        for i, png in enumerate(pngs):
            s = prs.slides.add_slide(blank)
            # Don't inherit shapes from the layout or master. Every branded
            # layout in the .potx carries a full-bleed background picture at
            # 0,0 — teal field plus logo — which is correct for someone adding
            # a slide by hand in PowerPoint, but wrong here: these slides ARE
            # their design, painted as a full-bleed PNG, so the inherited art
            # only ever showed up behind (and around) the real background.
            #
            # showMasterSp="0" is the PowerPoint-native way to say "this slide
            # draws its own chrome". It suppresses inherited SHAPES only, not
            # the background fill, and it's per-slide — so the .potx keeps its
            # branded layouts intact for manual authoring.
            s._element.set("showMasterSp", "0")
            if branded:
                # The branded layouts all carry placeholders; the generated
                # slides don't use them (the design is the baked background +
                # explicit text boxes), so drop the empty clones — otherwise
                # PowerPoint shows "Click to add ..." ghosts in edit view.
                for ph in list(s.placeholders):
                    ph._element.getparent().remove(ph._element)
            bg = s.shapes.add_picture(png, 0, 0, width=prs.slide_width,
                                      height=prs.slide_height)
            # Locked: no-move, no-resize. The illustrations below are left
            # unlocked on purpose — swapping one is a supported edit, which is
            # why they're named for the selection pane in the first place.
            _lock_background(bg)
            # Illustrations, above the background and BELOW the text boxes and
            # dots added after them. That z-order is the design's: deck.css puts
            # .content-area over .illus-topright / .illus-corner, so if art and
            # copy ever share space the copy wins, exactly as on the slide.
            for il in illus_by_slide.get(i, []):
                pic = s.shapes.add_picture(
                    il["png"],
                    Emu(int(il["x"] * EMU_PER_PX)), Emu(int(il["y"] * EMU_PER_PX)),
                    width=Emu(int(max(il["w"], 1) * EMU_PER_PX)),
                    height=Emu(int(max(il["h"], 1) * EMU_PER_PX)))
                # Name it for the PowerPoint selection pane, so "swap that
                # illustration" is a findable object and not an anonymous Picture 7.
                base = os.path.splitext(os.path.basename(il.get("svg") or ""))[0]
                if base:
                    pic.name = "Illustration - " + base
                _dress_picture(pic, s.part, il.get("svg"), il.get("opacity", 1),
                               svg_cache=svg_cache)
            for bx in by_slide.get(i, []):
                left = Emu(int(bx["x"] * EMU_PER_PX)); top = Emu(int(bx["y"] * EMU_PER_PX))
                # Right-margin rule: content keeps a safe gutter on the right so
                # PowerPoint's slightly wider text wrapping can't push it toward
                # the edge or under the bleed Stewart. Footers (page number,
                # brand mark) are exempt and keep their exact position; the bleed
                # Stewart is art, not text, so it's never touched here.
                if bx.get("centered"):
                    width_px = bx["w"]          # keep the exact box so centering matches
                elif bx.get("footer"):
                    width_px = bx["w"] + 4
                else:
                    buf = min(bx["w"] * 0.06, 70) + 6
                    width_px = bx["w"] + buf
                    max_right = DESIGN_W - SAFE_RIGHT_PX
                    if bx["x"] + width_px > max_right:
                        width_px = max(max_right - bx["x"], bx["w"])
                width = Emu(int(max(width_px, 8) * EMU_PER_PX))
                height = Emu(int(max(bx["h"], 8) * EMU_PER_PX))
                tb = s.shapes.add_textbox(left, top, width, height)
                tf = tb.text_frame
                # word_wrap OFF, deliberately. Every box is written with the
                # browser's own wrap points as hard <a:br> breaks, so PowerPoint
                # has nothing legitimate to wrap. With wrap on, its slightly
                # wider font metrics would re-wrap a long hard line into two,
                # and every line below shifted down — which is how a 96px
                # headline ended up overlapping the body copy under it. With
                # wrap off the worst case inverts: a line can poke a few px past
                # its box (the +6% width buffer absorbs most of it), which reads
                # as nothing, instead of a cascade that collides two boxes.
                # Cost: hand-EDITED text won't reflow — a long insertion runs
                # right instead of wrapping. Fidelity of the delivered file wins.
                #
                # Guard: only safe when the browser's measured lines are present.
                # If line capture failed, the raw-text fallback would render as
                # ONE unbroken line, so re-enable wrapping for that box only.
                tf.word_wrap = not bool(bx.get("lines"))
                tf.vertical_anchor = MSO_ANCHOR.TOP
                for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
                    setattr(tf, m, 0)
                try:
                    from pptx.enum.text import MSO_AUTO_SIZE
                    tf.auto_size = MSO_AUTO_SIZE.NONE
                except Exception:
                    pass
                para = tf.paragraphs[0]
                para.alignment = align_map.get((bx["align"] or "left").lower(), PP_ALIGN.LEFT)
                if bx.get("centered"):   # flex/grid-centered (badges, avatars): center both axes
                    para.alignment = PP_ALIGN.CENTER
                    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
                # Match CSS line-height exactly. Use an EXACT point value (not a
                # multiple) — PowerPoint renders a line-spacing multiple looser
                # than CSS, which pushes wrapped lines down toward the next item.
                try:
                    if bx["lh"] and bx["lh"].endswith("px"):
                        lh_px = float(bx["lh"][:-2])
                        if lh_px > 0:
                            para.line_spacing = Pt(round(lh_px * PT_PER_PX, 2))
                except Exception:
                    pass
                lines = bx.get("lines") or [bx["text"]]
                if not lines:
                    lines = [bx["text"]]
                upper = (bx["transform"] or "").startswith("upper")
                fam = _first_family(bx["family"])
                fsize = Pt(max(bx["size"] * PT_PER_PX, 6))
                try:
                    fbold = int(float(bx["weight"])) >= 600
                except Exception:
                    fbold = bx["weight"] in ("bold", "bolder")
                fcolor = _rgb_hex(bx["color"])
                for li_i, line in enumerate(lines):
                    if li_i:   # native line break — reproduces the design's own wrap point
                        para._p.append(para._p.makeelement(qn("a:br"), {}))
                    run = para.add_run()
                    run.text = line.upper() if upper else line
                    f = run.font
                    f.size = fsize
                    f.name = fam
                    f.bold = fbold
                    f.color.rgb = RGBColor.from_string(fcolor)
                # Native, editable list marker — PowerPoint draws the bullet/number
                # itself. marL/indent give the hanging indent so wrapped lines align
                # under the text, and the marker lands where the design's did. Emit
                # pPr children in schema order: buClr -> buFont -> buChar|buAutoNum.
                b = bx.get("bullet")
                if b:
                    pPr = para._p.get_or_add_pPr()
                    marL_emu = int(max(bx.get("marL", 0) or 0, 0) * EMU_PER_PX)
                    if marL_emu > 0:
                        pPr.set("marL", str(marL_emu))
                        pPr.set("indent", str(-marL_emu))
                    mcolor = _rgb_hex(b.get("color") or bx["color"])
                    buClr = pPr.makeelement(qn("a:buClr"), {})
                    buClr.append(pPr.makeelement(qn("a:srgbClr"), {"val": mcolor}))
                    pPr.append(buClr)
                    if b.get("kind") == "num":
                        pPr.append(pPr.makeelement(qn("a:buFont"), {"typeface": fam}))
                        pPr.append(pPr.makeelement(qn("a:buAutoNum"),
                                                   {"type": b.get("scheme", "arabicPeriod"),
                                                    "startAt": str(b.get("startAt", 1))}))
                    else:
                        pPr.append(pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"}))
                        pPr.append(pPr.makeelement(qn("a:buChar"), {"char": b.get("char", "•")}))
            # Timeline column dots — native, editable ovals lifted out of the
            # background so they can be recolored or moved in PowerPoint. Each keeps
            # the design's exact position, size, and fill (the source dots were
            # dropped from the background screenshot above).
            for sh in shapes_by_slide.get(i, []):
                oval = s.shapes.add_shape(
                    MSO_SHAPE.OVAL,
                    Emu(int(sh["x"] * EMU_PER_PX)), Emu(int(sh["y"] * EMU_PER_PX)),
                    Emu(int(max(sh["w"], 1) * EMU_PER_PX)),
                    Emu(int(max(sh["h"], 1) * EMU_PER_PX)))
                oval.fill.solid()
                oval.fill.fore_color.rgb = RGBColor.from_string(_rgb_hex(sh["color"]))
                oval.line.fill.background()
                try:
                    oval.shadow.inherit = False
                except Exception:
                    pass
            if i < len(notes) and notes[i]:
                if not _set_speaker_notes(s, notes[i]):
                    print(f"note: speaker notes for slide {i + 1} could not be "
                          f"written (template notes master has no body "
                          f"placeholder)", file=sys.stderr)

        # The template's Supporting graphics slide ships in the deliverable, but
        # at the BACK — it's a resource for the presenter, not part of the deck.
        _move_template_slides_to_end(prs, template_ids)

        out_path = out_base + "-editable.pptx"
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        prs.save(out_path)
        extra = (f" + {len(template_ids)} template slide"
                 f"{'s' if len(template_ids) != 1 else ''} at the end"
                 if template_ids else "")
        print(f"Editable PPTX: {out_path}  ({len(pngs)} slides, "
              f"{len(boxes)} text boxes, {len(illus)} illustrations{extra})")
        return True
    finally:
        shutil.rmtree(pngdir, ignore_errors=True)


def export_html_bundle(deck_path, out_base):
    """Zip the source HTML together with its asset kit so the HTML is portable
    and editable (open in a browser, edit, re-render). Written as <out>-html.zip."""
    import zipfile
    deck_dir = os.path.dirname(os.path.abspath(deck_path))
    html_name = os.path.basename(deck_path)
    kit = ["deck.css", "deck-stage.js", "logo", "illustrations", "design-system", "fonts"]
    zip_path = out_base + "-html.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(deck_path, html_name)
        for item in kit:
            p = os.path.join(deck_dir, item)
            if os.path.isfile(p):
                z.write(p, item)
            elif os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        fp = os.path.join(root, f)
                        z.write(fp, os.path.relpath(fp, deck_dir))
    print("  " + zip_path + "  (editable HTML + asset kit)")
    return True


def main():
    ap = argparse.ArgumentParser(description="Render / check / export a Rewst HTML deck.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="verify layout compliance (margins, padding, footers)")
    c.add_argument("deck"); c.add_argument("--scale", type=int, default=1)
    e = sub.add_parser("export", help="write the standard set: <out>.pdf, "
                                      "<out>-editable.pptx, and <out>-html.zip")
    e.add_argument("deck"); e.add_argument("--out", required=True); e.add_argument("--scale", type=int, default=2)
    e.add_argument("--formats", default="pdf,pptx,html",
                   help="comma-separated subset of pdf,pptx,html to write "
                        "(default: all three). 'pptx' is the editable PPTX.")
    e.add_argument("--editable", action="store_true",
                   help="(default behavior) also write the editable PPTX — kept for compatibility")
    e.add_argument("--no-editable", action="store_true",
                   help="skip the editable PPTX (kept for compatibility; same as "
                        "omitting pptx from --formats)")
    r = sub.add_parser("render", help="dump per-slide PNGs")
    r.add_argument("deck"); r.add_argument("--pngdir", required=True); r.add_argument("--scale", type=int, default=2)
    a = ap.parse_args()
    if a.cmd == "check":
        sys.exit(0 if check(a.deck, a.scale) else 1)
    elif a.cmd == "export":
        fmts = {f.strip().lower() for f in a.formats.split(",") if f.strip()}
        bad = fmts - {"pdf", "pptx", "html"}
        if bad:
            print(f"unknown format(s): {', '.join(sorted(bad))} "
                  f"(choose from pdf, pptx, html)", file=sys.stderr)
            sys.exit(2)
        if a.no_editable:
            fmts.discard("pptx")
        if not fmts:
            print("nothing to export: no formats selected", file=sys.stderr)
            sys.exit(2)
        ok = True
        if "pdf" in fmts:
            ok = export(a.deck, a.out, a.scale)          # <out>.pdf
        if ok and "pptx" in fmts:
            ok = export_editable(a.deck, a.out, a.scale) and ok   # <out>-editable.pptx
        if ok and "html" in fmts:
            export_html_bundle(a.deck, a.out)            # <out>-html.zip (editable source)
        sys.exit(0 if ok else 1)
    elif a.cmd == "render":
        render(a.deck, a.pngdir, a.scale); print("rendered to", a.pngdir)


if __name__ == "__main__":
    main()

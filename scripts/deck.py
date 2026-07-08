#!/usr/bin/env python3
"""
deck.py — render, brand-check, and export a Rewst HTML deck.

The deck is the source of truth: a self-contained HTML file whose slides are the
direct <section> children of <deck-stage>. This script renders each slide in a
real headless Chromium (so masks, pseudo-elements, web fonts, and the exact CSS
all resolve faithfully), then:

  check   verify every slide contains primary Bot Teal (#00BBB4)
  export  write <name>.pdf (one full-bleed slide per page), the editable
          <name>-editable.pptx, and the <name>-html.zip source bundle,
          carrying speaker notes into the editable PPTX notes pane
  render  just dump per-slide PNGs (mostly for debugging)

The three shipped formats are the PDF, the editable PPTX (a design-background +
native text boxes rebuild), and the HTML bundle. The older faithful
(image-per-slide, non-editable) PPTX has been retired from the standard set.

Usage:
  python deck.py check  deck.html
  python deck.py export deck.html --out /mnt/user-data/outputs/deck
  python deck.py render deck.html --pngdir /tmp/slides --scale 2
"""
import argparse, json, os, re, sys, tempfile, shutil

# Chromium lives here in this environment; harmless if already correct elsewhere.
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")

BOT_TEAL = (0, 187, 180)           # #00BBB4 — the only shade that satisfies the rule
MIN_TEAL_PIXELS = 150              # a real teal element vs. a stray antialiased pixel
DESIGN_W, DESIGN_H = 1920, 1080
SAFE_RIGHT_PX = 110               # content right-margin safe zone (matches --pad-x)
MIN_BOX_PAD = 32                  # min internal padding inside content boxes/cards (matches --box-pad-min)
SKILL_FONTS = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")


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


def _count_teal(png):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    try:
        import numpy as np
        a = np.asarray(im)
        return int(((a[:, :, 0] == BOT_TEAL[0]) &
                    (a[:, :, 1] == BOT_TEAL[1]) &
                    (a[:, :, 2] == BOT_TEAL[2])).sum())
    except ImportError:
        return sum(c for c, col in im.getcolors(maxcolors=1 << 24) if col == BOT_TEAL)


def check(deck_path, scale=1):
    pngdir = tempfile.mkdtemp(prefix="rewst-check-")
    try:
        pngs = render(deck_path, pngdir, scale=scale)
        rows, teal_ok = [], True
        for i, png in enumerate(pngs, 1):
            n = _count_teal(png)
            passed = n >= MIN_TEAL_PIXELS
            teal_ok = teal_ok and passed
            rows.append((i, passed, n))
        print(f"Bot Teal (#00BBB4) check — {len(rows)} slides\n" + "-" * 46)
        for i, passed, n in rows:
            print(f"  slide {i:02d}  {'PASS' if passed else 'FAIL — no Bot Teal'}  ({n} px)")

        margin_ok, mrows, box_ok, brows, footer_ok, frows = check_margins(deck_path)
        print("\nRight-margin check (content must stay within the 110px gutter;\n"
              "bleed Stewart and footers exempt) — " + f"{len(mrows)} slides\n" + "-" * 46)
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

        teal_src_ok, teal_hits = check_retired_teal(deck_path)
        print("\nRetired-teal check (deck source must not contain the retired "
              "#1EAFAF / #1CAFAF)\n" + "-" * 46)
        if teal_hits:
            for h in teal_hits:
                print(f"  FAIL — {h}")
        else:
            print("  PASS  (no retired teal in the deck HTML or its deck.css)")

        ok = teal_ok and margin_ok and box_ok and footer_ok and teal_src_ok
        print("-" * 46)
        print("RESULT:", "ALL CHECKS PASS ✓" if ok else "FAILURES ABOVE ✗")
        return ok
    finally:
        shutil.rmtree(pngdir, ignore_errors=True)


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
            bx = tr.left - sr.left;
            bw = Math.max((r.right - pr) - tr.left, tr.width);
          }
        } catch (_) {}
      }
      out.push({
        s: si, x: bx, y: by, w: bw, h: bh,
        text: txt, lines: visualLines(e),
        size: parseFloat(cs.fontSize) || 16, weight: cs.fontWeight,
        color: cs.color, align: cs.textAlign, family: cs.fontFamily,
        transform: cs.textTransform, lh: cs.lineHeight, ls: cs.letterSpacing,
        footer: !!e.closest(".pageno, .brand-mark"),
        centered: centered
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
      if (e.closest(".bleed-stewart, .pageno, .brand-mark")) return;  // exempt: art + footers
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
    - right margin: no content paints past the right gutter (Stewart/footers exempt)
    - box padding: content boxes/cards keep a minimum internal padding so content
      never touches the box edge (small chips, badges, avatars, table cells exempt)
    - footers: every slide shows the logo bottom-left and the page number bottom-right
    Returns (margin_ok, margin_rows, box_ok, box_rows, footer_ok, footer_rows)."""
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
            b.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    margin_ok = all(not r["bad"] for r in mrows)
    box_ok = all(not r["bad"] for r in brows)
    footer_ok = all(not r["bad"] for r in frows)
    return margin_ok, mrows, box_ok, brows, footer_ok, frows


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


def _render_textless_and_extract(deck_path, scale=2):
    """One page load: pull every text box's geometry+style, then hide that text
    and screenshot each section as the editable slide's background."""
    from playwright.sync_api import sync_playwright
    tmp = _build_export_html(deck_path)
    pngdir = tempfile.mkdtemp(prefix="rewst-edit-bg-")
    pngs = []
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
            # which slides carry the Bot Teal anchor dot (all except .no-teal-dot)
            has_dot = pg.evaluate("() => [...document.querySelectorAll('deck-stage > section')]"
                                  ".map(s => !s.classList.contains('no-teal-dot'))")
            # hide the lifted text, keep everything else (shapes, art, decorative
            # markers). All text lifts into native boxes — including the agenda
            # numbers, whose CSS counter is hidden here and re-emitted as real text.
            # Drop the baked footer dot here — the editable PPTX draws it as a native
            # centered shape instead, so it can never sit off-center.
            pg.add_style_tag(content="[data-edit-hide]{color:transparent !important;"
                                     "text-shadow:none !important;}"
                                     "deck-stage section::after{content:none !important;}")
            for i, sec in enumerate(pg.query_selector_all("deck-stage > section"), 1):
                out = os.path.join(pngdir, f"bg-{i:02d}.png")
                sec.screenshot(path=out); pngs.append(out)
            b.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return pngs, boxes, has_dot, pngdir


def export_editable(deck_path, out_base, scale=2):
    """Hybrid editable PPTX: full-bleed design background + native text boxes."""
    from PIL import Image  # noqa: F401 (ensures Pillow present)
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.oxml.ns import qn
    pngs, boxes, has_dot, pngdir = _render_textless_and_extract(deck_path, scale=scale)
    try:
        if not pngs:
            print("No slides rendered.", file=sys.stderr); return False
        prs = Presentation()
        prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
        EMU_PER_PX = prs.slide_width / DESIGN_W            # 1920px -> 13.333in
        PT_PER_PX = 0.5                                     # 1920px == 960pt
        blank = prs.slide_layouts[6]
        notes = _speaker_notes(deck_path)
        align_map = {"center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT,
                     "justify": PP_ALIGN.JUSTIFY, "left": PP_ALIGN.LEFT,
                     "start": PP_ALIGN.LEFT, "end": PP_ALIGN.RIGHT}
        by_slide = {}
        for bx in boxes:
            by_slide.setdefault(bx["s"], []).append(bx)

        for i, png in enumerate(pngs):
            s = prs.slides.add_slide(blank)
            s.shapes.add_picture(png, 0, 0, width=prs.slide_width, height=prs.slide_height)
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
                tf.word_wrap = True
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
            # Bot Teal anchor dot — native shape, locked to the exact footer center
            # (x = 960px of 1920, 18px circle, 54px up from the bottom). Independent
            # of the background, so it is always perfectly centered.
            if i < len(has_dot) and has_dot[i]:
                d = 18
                dot = s.shapes.add_shape(
                    MSO_SHAPE.OVAL,
                    Emu(int((DESIGN_W - d) / 2 * EMU_PER_PX)),
                    Emu(int((DESIGN_H - 54 - d) * EMU_PER_PX)),
                    Emu(int(d * EMU_PER_PX)), Emu(int(d * EMU_PER_PX)))
                dot.fill.solid(); dot.fill.fore_color.rgb = RGBColor.from_string("00BBB4")
                dot.line.fill.background()
                try:
                    dot.shadow.inherit = False
                except Exception:
                    pass
            if i < len(notes) and notes[i]:
                s.notes_slide.notes_text_frame.text = notes[i]

        out_path = out_base + "-editable.pptx"
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        prs.save(out_path)
        print(f"Editable PPTX: {out_path}  ({len(pngs)} slides, "
              f"{len(boxes)} text boxes)")
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
    c = sub.add_parser("check", help="verify Bot Teal #00BBB4 on every slide")
    c.add_argument("deck"); c.add_argument("--scale", type=int, default=1)
    e = sub.add_parser("export", help="write the standard set: <out>.pdf, "
                                      "<out>-editable.pptx, and <out>-html.zip")
    e.add_argument("deck"); e.add_argument("--out", required=True); e.add_argument("--scale", type=int, default=2)
    e.add_argument("--editable", action="store_true",
                   help="(default behavior) also write the editable PPTX — kept for compatibility")
    e.add_argument("--no-editable", action="store_true",
                   help="skip the editable PPTX (not recommended; editable is part of the standard deliverable)")
    r = sub.add_parser("render", help="dump per-slide PNGs")
    r.add_argument("deck"); r.add_argument("--pngdir", required=True); r.add_argument("--scale", type=int, default=2)
    a = ap.parse_args()
    if a.cmd == "check":
        sys.exit(0 if check(a.deck, a.scale) else 1)
    elif a.cmd == "export":
        ok = export(a.deck, a.out, a.scale)          # <out>.pdf
        if ok and not a.no_editable:
            ok = export_editable(a.deck, a.out, a.scale) and ok   # <out>-editable.pptx
        if ok:
            export_html_bundle(a.deck, a.out)          # <out>-html.zip (editable source)
        sys.exit(0 if ok else 1)
    elif a.cmd == "render":
        render(a.deck, a.pngdir, a.scale); print("rendered to", a.pngdir)


if __name__ == "__main__":
    main()

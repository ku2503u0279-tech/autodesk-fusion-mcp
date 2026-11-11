"""Build the illustrated portfolio and build guide.

    python make_pdf.py

Writes ../fusion_desk_setup/DESK_SETUP_DESIGNER_PORTFOLIO_AND_GUIDE.pdf
"""
import os

from reportlab.lib.utils import ImageReader

import catalog as C
import geometry as G
import pdfkit as K
from pdfkit import (AMBER, AMBER_L, BLUE, CW, Doc, FAINT, GREEN, H, INK, INK2,
                    ML, MUTE, RED, RULE, W, WASH)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
DEST = os.path.join(os.path.dirname(HERE), "fusion_desk_setup",
                    "DESK_SETUP_DESIGNER_PORTFOLIO_AND_GUIDE.pdf")
SHORT = "630 \u00d7 280 \u00d7 21 mm MODULAR DESK SYSTEM"

DEFAULT_NOTE = ("All dimensions millimetres. Part names match the exported "
                "STL / STEP files exactly.")


# --------------------------------------------------------------- furniture
def header(d, section, dark=False):
    d.rule(ML, W - K.MR, 34, color=K.hx("#2C333D") if dark else RULE, width=0.7)
    d.track("DESIGNER HYBRID V2", ML, 26.5, 7.6, AMBER_L if dark else AMBER, 1.5)
    d.track(SHORT, 205, 26.5, 6.9, K.hx("#7E8894") if dark else MUTE, 0.7, "H")
    if section:
        d.track(section, W - K.MR, 26.5, 6.9,
                K.hx("#7E8894") if dark else MUTE, 1.3, align="r")
    return d


def footer(d, folio, note=DEFAULT_NOTE):
    d.rule(ML, W - K.MR, H - 40, color=RULE, width=0.7)
    d.para(note, ML, H - 26, CW - 40, 7.2, 9.0, MUTE)
    d.text("%02d" % folio, W - K.MR, H - 24, 8.6, "HB", INK, "r")


def title(d, t, kicker=None, sub=None, size=25, y=52):
    if kicker:
        d.track(kicker, ML, y, 7.3, AMBER, 1.35)
        y += 15
    d.text(t, ML, y + 7, size, "HB", INK)
    y += size * 0.62 + 8
    if sub:
        y = d.para(sub, ML, y + 3, CW * 0.68, 9.6, 13.6, MUTE)
    return y


def bullets(d, items, x, y, w, size=9.0, leading=12.8, color=INK2, gap=4.4):
    for it in items:
        d.text("\u2022", x, y, size, "H", AMBER_L)
        y = d.para(it, x + 11, y, w - 11, size, leading, color)
        y += gap
    return y


def numbered(d, items, x, y, w, size=9.0, leading=12.8, gap=4.4):
    for i, it in enumerate(items, 1):
        d.text(str(i), x, y, size, "HB", AMBER)
        y = d.para(it, x + 11, y, w - 11, size, leading, INK2)
        y += gap
    return y


def section_head(d, label, x, y, w=280):
    d.track(label, x, y, 7.1, INK, 1.25)
    d.rule(x, x + w, y + 6, color=INK, width=0.9)
    return y + 21


def side_panel(d, x, y, w, head, items, size=8.4, leading=12.0, gap=3.4):
    y = section_head(d, head, x, y, w)
    return bullets(d, items, x, y, w, size, leading, INK2, gap)


def warm(d, x, y, w, h, head, body, size=8.4, leading=12.0):
    d.rect(x, y, x + w, y + h, fill=K.hx("#FBF3E9"), r=2)
    d.track(head, x + 14, y + 20, 6.8, AMBER, 1.2)
    return d.para(body, x + 14, y + 38, w - 28, size, leading, INK2)


def panel(d, x, y, w, h, rgb=WASH):
    d.rect(x, y, x + w, y + h, fill=rgb, r=2)


# ------------------------------------------------------------ fitted views
def fit_box(img, x, y, w, h):
    """Return a box that matches the image's own aspect, so there is no dead band."""
    ir = ImageReader(img)
    iw, ih = ir.getSize()
    sc = min((w - 12) / iw, (h - 12) / ih)
    return x, y, iw * sc + 12, ih * sc + 12


def draw_view(d, img, box, cap=None):
    """Fit a view inside `box` without distortion. Returns the drawn rect."""
    x, y, w, h = box
    panel(d, x, y, w, h)
    ir = ImageReader(img)
    iw, ih = ir.getSize()
    sc = min((w - 12) / iw, (h - 12) / ih)
    dw, dh = iw * sc, ih * sc
    dx, dy = x + (w - dw) / 2, y + (h - dh) / 2
    d.image(img, dx, dy, dw, dh)
    if cap:
        d.para(cap, x, y + h + 11, w, 7.4, 9.6, MUTE)
    return dx, dy, dw, dh


DIM_CEILING = 528.0


def dim_h(d, x0, x1, y, label, color=None, tick=3.4, size=7.2):
    """Horizontal dimension line with end ticks and a centred label."""
    if y > DIM_CEILING:
        raise AssertionError("dimension at y=%.1f would hit the footer" % y)
    color = INK2 if color is None else color
    d.c.setStrokeColor(K.C(color))
    d.c.setLineWidth(0.55)
    yy = K.H - y
    d.c.line(x0, yy, x1, yy)
    for xx in (x0, x1):
        d.c.line(xx, yy - tick, xx, yy + tick)
    d.text(label, (x0 + x1) / 2, y - 4.4, size, "H", color, "c")


def scale_line(d, view, mapper, u0, u1, y, label, color=None):
    """Dimension between two WORLD u values, using the rect returned by draw_view."""
    dx, _, dw, _ = view
    sx = dw / mapper.w
    a = dx + mapper.to_px(u0, 0)[0] * sx
    b = dx + mapper.to_px(u1, 0)[0] * sx
    dim_h(d, a, b, y, label, color)


# ------------------------------------------------------------------- pages
def p_cover(d):
    d.page(bg=K.hx("#0E1319"))
    d.rule(ML, W - K.MR, 44, color=K.hx("#9A6B33"), width=0.9)
    d.track("DESIGNER HYBRID V2", ML, 32, 8.0, AMBER_L, 1.9)
    d.text("The 630 \u00d7 280 Desk System", ML, 78, 34, "HB", K.hx("#FFFFFF"))
    d.text("Six clamp-on products, forty-three pieces, zero screws in the desk.",
           ML, 98, 11.4, "H", K.hx("#9AA5B1"))
    top, bot = 120.0, H - 130.0
    d.image(os.path.join(OUT, "hero_dark.png"), ML, top, CW, bot - top)
    y = H - 100
    for i, (big, small) in enumerate([("630 \u00d7 280 \u00d7 21", "desk + mat footprint"),
                                      ("43", "pieces catalogued"),
                                      ("6", "clamp-on products"),
                                      ("0", "screws or glue in the desk")]):
        x = ML + i * (CW / 4)
        d.text(big, x, y, 15.5, "HB", K.hx("#FFFFFF"))
        d.text(small, x, y + 14, 8.4, "H", K.hx("#7D8794"))
    d.rule(ML, W - K.MR, H - 72, color=K.hx("#2A313A"), width=0.7)
    d.text("Built from Autodesk Fusion parametric models \u2014 every dimension checked by "
           "verify_fusion_scripts.py", ML, H - 54, 8.0, "H", K.hx("#7D8794"))
    d.text("2026", W - K.MR, H - 54, 8.2, "H", K.hx("#7D8794"), "r")


def p_contents(d):
    d.page()
    header(d, "CONTENTS")
    title(d, "What is in this book")
    y = 90.0
    for num, head, sub, folio in C.CONTENTS:
        d.text(num, ML, y + 7, 8.4, "HB", AMBER_L)
        d.text(head, ML + 26, y + 7, 10.2, "HB", INK)
        d.text(sub, ML + 26, y + 18, 8.2, "H", MUTE)
        d.text(folio, W - K.MR, y + 8, 10.2, "H", INK, "r")
        d.rule(ML, W - K.MR, y + 25, color=RULE)
        y += 29.6
    if y > H - 52:
        raise AssertionError("contents overflows the page (ends at %.1f)" % y)
    footer(d, 2, "Page numbers are the printed folio at the bottom right of every page.")


def p_howto(d):
    d.page()
    header(d, "01 \u00b7 HOW TO READ THIS BOOK")
    title(d, "Three drawings per product, always in the same order")

    y = 108.0
    cols = [("A", "The shaded view",
             "A product render built from the same geometry as the Fusion file. This is what the assembled "
             "product looks like on the desk. Brown is wood, grey-black is printed, bright metal is a \u00d88 mm rod."),
            ("B", "Top / Front / Side",
             "True orthographic projections drawn from the same geometry. Every dimension is in millimetres "
             "and can be measured with a ruler on a print-out."),
            ("C", "The piece list",
             "A table naming each part exactly as it is named in Fusion, with its size, its material and how you "
             "make it. The same names appear in the exported STL / STEP files.")]
    cw = (CW - 24) / 3
    for i, (k, head, body) in enumerate(cols):
        x = ML + i * (cw + 12)
        panel(d, x, y, cw, 118)
        d.text(k, x + 16, y + 40, 25, "HB", AMBER_L)
        d.text(head, x + 46, y + 34, 11.6, "HB", INK)
        d.para(body, x + 16, y + 58, cw - 32, 8.7, 12.4, INK2)

    y = 262.0
    d.track("MATERIAL COLOUR KEY", ML, y, 7.2, INK, 1.3)
    d.rule(ML, ML + 210, y + 6, color=INK, width=0.9)
    y += 26
    key = [(G.WALNUT, "Warm walnut / birch", "12 mm and 6 mm sheet \u2014 arches, decks, trays, coasters"),
           (G.METAL, "Brushed aluminium / steel", "\u00d88 mm tie-rods, 608 bearing seats"),
           (G.PRINT, "Stealth matte black", "PETG precision nodes \u2014 clamps, collars, hubs"),
           (G.RED, "Cyber-Red accent", "Dovetail collars, axle collars, visors, spires"),
           (G.GLASS, "K9 optical glass", "The 25.4 mm beam-splitter cube in HoloBuddy")]
    cw = (CW - 4 * 10) / 5
    for i, (col, head, sub) in enumerate(key):
        x = ML + i * (cw + 10)
        d.rect(x, y - 8, x + 34, y + 6, fill=col, r=2)
        d.text(head, x + 42, y - 1, 8.8, "HB", INK)
        d.para(sub, x + 42, y + 9, cw - 42, 7.5, 9.8, MUTE)

    y = 366.0
    d.rect(ML, y, W - K.MR, y + 96, fill=None, stroke=RULE, r=2)
    d.track("READING THE DIMENSIONS", ML + 16, y + 22, 7.2, INK, 1.3)
    d.para("Every length is in millimetres. A size such as 184 \u00d7 131.4 \u00d7 12 means length \u00d7 height \u00d7 "
           "thickness for a flat part, or X \u00d7 Y \u00d7 Z for an assembly. Angles are in degrees. The desk "
           "coordinate system runs X = 0...630 mm left to right, Y = 0 at the mat surface (positive up), and "
           "Z = 0 at the back wall with Z = 280 mm at the front edge you sit at. A round part is given as "
           "\u00d8diameter \u00d7 thickness.",
           ML + 16, y + 42, W - K.MR - ML - 32, 9.0, 13.4, INK2)
    footer(d, 3)


def p_glance(d):
    d.page()
    header(d, "02 \u00b7 THE SYSTEM AT A GLANCE")
    title(d, "Where each product clamps, and the space it must leave free")

    fw, fh = 500.0, 352.0
    panel(d, ML, 92, fw, fh)
    d.image(os.path.join(OUT, "hero.png"), ML + 5, 97, fw - 10, fh - 10)
    d.para("Assembled, seen from the user's front-right. Products 1-5 are in place; the keyboard sits in the garage.",
           ML, 92 + fh + 12, fw, 7.6, 10.0, MUTE)

    x = ML + fw + 34
    y = 108.0
    for key, (name, sub, folio) in C.PRODUCTS.items():
        d.text(key, x, y, 8.4, "HB", AMBER)
        d.text(name, x + 26, y, 9.6, "HB", INK)
        d.text(sub, x + 26, y + 11, 8.2, "H", MUTE)
        d.text(folio, W - K.MR, y, 9.6, "H", INK, "r")
        y += 30

    y += 8
    warm(d, x, y, W - K.MR - x, 104, "CLEAR ZONES \u2014 NEVER BLOCK THESE",
         "Knee void X 195...610 under the desk \u00b7 mouse sweep X 470...628, Z 90...278 \u00b7 keyboard garage "
         "332 mm wide by 62 mm high.", 8.6, 12.4)

    y = H - 96
    facts = [("TABLE", "630 \u00d7 280 \u00d7 18 mm dark wood"),
             ("MAT", "630 \u00d7 280 \u00d7 3 mm"),
             ("EDGE STACK", "21 mm"),
             ("BACK WALL", "Z = 0, flush, no rear clamp"),
             ("USER", "right-handed, seated at X = 315")]
    cw = CW / 5
    d.rule(ML, W - K.MR, y - 12, color=RULE)
    for i, (k, v) in enumerate(facts):
        xx = ML + i * cw
        d.track(k, xx, y, 6.8, MUTE, 1.2)
        d.text(v, xx, y + 15, 8.6, "H", INK)
    footer(d, 4)


def p_top(d, mapper, img):
    d.page()
    header(d, "03 \u00b7 DIMENSIONS")
    title(d, "Top plan \u2014 where everything sits",
          sub="Top plan, lid and keyboard removed for clarity. Z = 0 is the back wall.")
    view = draw_view(d, img, fit_box(img, ML, 94, 566, 306),
                     "Assembled from above. Wood is brown, printed nodes grey-black, the mat near-black.")
    y0 = min(view[1] + view[3] + 46, 470.0)
    scale_line(d, view, mapper, 0, 630, y0, "630.0   desk + mat width")
    scale_line(d, view, mapper, 100, 436, y0 + 22, "336.0   bridge span", AMBER)
    scale_line(d, view, mapper, 470, 628, y0 + 44, "158   mouse sweep", BLUE)

    x = ML + 590
    side_panel(d, x, 106, W - K.MR - x, "READ THIS VIEW LIKE A DRAWING",
               ["X runs 0...630 mm left to right; Z runs 0...280 mm from the back wall to the front edge you sit at.",
                "Products 2 and 3 work entirely outboard: negative X or Z beyond 280 mm. They never take desk space.",
                "The right-hand area X 470...628, Z 90...278 is deliberately empty \u2014 that is your mouse sweep.",
                "The keyboard garage is the 332 mm gap between the two AeroBridge arches, X 106.5...429.5."])
    footer(d, 5, "Top plan drawn from the same geometry as the Fusion model.")


def p_front(d, mapper, img):
    d.page()
    header(d, "03 \u00b7 DIMENSIONS")
    title(d, "Front elevation \u2014 clearances you can measure",
          sub="Front elevation. The 21 mm edge stack is the wood slab plus the mat.")
    view = draw_view(d, img, fit_box(img, ML, 94, 520, 330),
                     "The keyboard sits in the garage and the lid stands clear of the wall.")
    y0 = min(view[1] + view[3] + 46, 470.0)
    scale_line(d, view, mapper, 0, 630, y0, "630.0   overall width")
    scale_line(d, view, mapper, 100, 436, y0 + 22, "336.0   bridge span", AMBER)
    scale_line(d, view, mapper, 195, 610, y0 + 44, "415.0   knee void", GREEN)

    x = ML + 524
    side_panel(d, x, 112, W - K.MR - x, "READ THIS VIEW LIKE A DRAWING",
               ["The 62 mm gap under the bridge is the keyboard garage: the AULA F75 is 43.1 mm tall, leaving "
                "18.9 mm of finger room.",
                "The 415 mm void between the left vault and the right caddy is where your knees go. Nothing hangs into it.",
                "Both \u00d88 mm rods pass through the arches at 89 mm and 71.5 mm, and they are what keeps the "
                "bridge square.",
                "Every clamp descends below the slab inside its own footprint, which is what lets it grip with no screws."])
    footer(d, 6, "Front elevation drawn from the same geometry as the Fusion model.")


def p_side(d, mapper, img):
    d.page()
    header(d, "03 \u00b7 DIMENSIONS")
    title(d, "Right side elevation \u2014 the depth stack",
          sub="Right side elevation. The desk is 280 mm deep; the bottle hangs 103.5 mm beyond it.")
    view = draw_view(d, img, fit_box(img, ML, 94, 252, 368),
                     "Depth stack from the right. The lid stands 2\u00b0 off vertical, so it reads as a thin edge "
                     "at the back wall.")
    y0 = view[1] + view[3] + 62
    dim_h(d, view[0] + mapper.to_px(0, 0)[0] * (view[2] / mapper.w),
          view[0] + mapper.to_px(280, 0)[0] * (view[2] / mapper.w), y0, "280.0   desk depth")
    dim_h(d, view[0] + mapper.to_px(280, 0)[0] * (view[2] / mapper.w),
          view[0] + mapper.to_px(383.5, 0)[0] * (view[2] / mapper.w), y0, "103.5", GREEN)

    x = ML + 316
    w = W - K.MR - x
    y = side_panel(d, x, 104, w, "READ THIS VIEW LIKE A DRAWING",
                   ["The laptop deck sits at 18\u00b0 and the 245 mm screen stands almost vertical, so a laptop at "
                    "eye level still clears the wall.",
                    "The whole build stays inside Z = 0...280 except the bottle cage, which hangs 103.5 mm past "
                    "the front edge.",
                    "HoloBuddy floats at Y = 65...156 mm, well above the 43 mm mouse, so the sweep stays clear.",
                    "Nothing protrudes behind Z = 0 \u2014 the desk is flush to the wall with no rear clamp at all."])

    y += 12
    d.track("THE DEPTH BUDGET", x, y, 7.1, INK, 1.25)
    d.rule(x, x + w, y + 6, color=INK, width=0.9)
    yy = y + 26
    for k, big, sub in [("TOTAL RISE ABOVE THE MAT", "406 mm", "top of the laptop screen"),
                        ("TALLEST FIXED PART", "383.5 mm", "the top of the bottle, in the chalice"),
                        ("BELOW THE DESK", "176 mm", "the bottom of the vault and the headphone saddle"),
                        ("DESK DEPTH USED", "280 mm", "the full mat, including the front lip")]:
        d.track(k, x, yy, 6.3, MUTE, 1.0)
        d.text(big, x, yy + 13, 10.4, "HB", INK)
        d.text(sub, x + 76, yy + 13, 8.0, "H", MUTE)
        yy += 30
    footer(d, 7, "Right side elevation drawn from the same geometry as the Fusion model.")


def p_why(d):
    d.page()
    header(d, "04 \u00b7 WHY WOOD, METAL AND PRINT")
    title(d, "Cheaper, stiffer, faster to make \u2014 and it looks like furniture, not a print farm", size=21)

    x, y = ML, 112.0
    d.track("THE 70 % SAVING", x, y, 7.2, INK, 1.3)
    d.rule(x, x + 210, y + 6, color=INK, width=0.9)
    y += 24
    for label, grams, frac, col in [("v1 \u2014 all printed", "1080 g", 1.0, K.hx("#9AA6B4")),
                                    ("v2 \u2014 hybrid", "330 g", 330 / 1080, AMBER_L)]:
        d.text(label, x, y, 8.8, "H", INK2)
        bx = x + 100
        d.rect(bx, y - 8.5, bx + 150, y + 1.5, fill=K.hx("#E7EBF0"), r=1)
        d.rect(bx, y - 8.5, bx + 150 * frac, y + 1.5, fill=col, r=1)
        d.text(grams, bx + 160, y, 8.6, "HB", INK)
        y += 22
    y += 4
    d.para("Filament only. Print time falls from about 34 h to about 10.5 h.", x, y, 300, 8.2, 11.4, MUTE)
    y += 26

    for label, big, sub in [("PRINT TIME", "\u2248 34 h \u2192 \u2248 10.5 h",
                             "Every node fits a 200 mm bed, so one machine finishes the set overnight."),
                            ("STIFFNESS", "> 15 kg, < 0.2 mm sag",
                             "A 6 mm walnut deck between two \u00d88 mm rods beats a 6 mm printed slab."),
                            ("COST", "\u2248 $35 in total",
                             "Walnut offcuts plus one rod cost less than the filament they replace."),
                            ("LOOK", "furniture, not prototype",
                             "Oiled walnut beside matte-black nodes and brushed metal reads as designed.")]:
        d.track(label, x, y, 6.8, MUTE, 1.2)
        d.text(big, x, y + 15, 10.6, "HB", INK)
        y = d.para(sub, x, y + 29, 296, 8.2, 11.4, MUTE) + 14

    x2 = ML + 336
    y2 = section_head(d, "WHAT EACH MATERIAL IS ACTUALLY DOING", x2, 112, W - K.MR - x2) + 6
    for col, head, body in [
            (G.WALNUT, "Wood \u2014 12 mm & 6 mm sheet",
             "Carries the load and sets the look. Arches, the laptop deck, the vault shield, trays and coasters are "
             "all flat parts: a saw, a drill and sandpaper are enough. Wood is the cheapest way to make something "
             "big, warm and stiff."),
            (G.METAL, "Metal \u2014 \u00d88 mm rod",
             "Ties the two wood arches into one rigid bridge and gives the 608 bearings a true axle. Two 360 mm rods "
             "replace what would otherwise be a printed beam far too long for most beds, and far too flexible."),
            (G.PRINT, "Print \u2014 26 compact nodes",
             "Does the jobs only printing can do: dovetail sockets held to \u00b10.15 mm, magnet pockets, bearing "
             "seats, cable channels and the optical chamber. Nothing is bigger than 186.5 mm, so any 200 mm printer "
             "makes the whole set."),
            (G.GLASS, "Glass \u2014 one cube",
             "The only optical part. A 25.4 mm 50:50 K9 cube splits the OLED image so it appears to float. "
             "Bought, not made.")]:
        d.rect(x2, y2 - 9, x2 + 3.2, y2 + 52, fill=col, r=1)
        d.text(head, x2 + 16, y2, 10.2, "HB", INK)
        y2 = d.para(body, x2 + 16, y2 + 14, W - K.MR - x2 - 16, 8.7, 12.5, INK2) + 18

    warm(d, ML, H - 168, 300, 76, "FINISH SEQUENCE",
         "Sand to 320 grit \u2192 damp cloth \u2192 one coat Danish oil (or mineral oil + beeswax) \u2192 buff after 24 h.")
    footer(d, 8)


# ------------------------------------------------------------ product pages
PRODUCT_COPY = {
    "p0": dict(
        folio=9, num="04", key="P0", name="Fit Check Gauge", kicker="PRINT THIS FIRST",
        blurb="A single 90 \u00d7 150 \u00d7 14 mm coupon that tests your printer and six pieces of hardware before you "
              "commit to the full set. If the coupon fits, every other print in this book will fit.",
        does=["Check that your printer holds \u00b10.15 mm on a dovetail.",
              "Press a 608 bearing in and feel whether the seat is right.",
              "Drop a 6 \u00d7 3 mm magnet into its pocket and confirm it sits flush.",
              "Confirm the M3 and M4 brass inserts melt in square.",
              "Check the DT-30 tongue slides \u2014 the same joint every product uses.",
              "Keep it in the spares box: it is the reference for every reprint."],
        build=["Print at 0.2 mm layers with the material you intend to use, not a test spool.",
               "Fit each hardware item as soon as the coupon cools \u2014 the pockets are a warm-room press fit.",
               "If anything is too tight, adjust only that pocket in Fusion and re-print the coupon."],
        mats=["PETG"],
        caption="The coupon. Six hardware tests on one 14 mm plate, printed before anything else."),
    "p1": dict(
        folio=10, num="05", key="P1", name="AeroBridge G16 + MagPivot S24+",
        kicker="LAPTOP STAND, KEYBOARD GARAGE, PHONE ARM",
        blurb="Two 12 mm walnut arches joined by two \u00d88 mm aluminium rods carry a 6 mm walnut slat deck. It lifts "
              "the ROG Strix G16 to eye level at 18\u00b0 and leaves a 62 mm-high garage underneath for the keyboard. "
              "A magnetic arm on the left arch holds the S24+ where you can see it.",
        does=["Slide the keyboard into the garage at the end of the day and the desk is instantly clear.",
              "The 18\u00b0 deck angle and the open slats let the G16 breathe \u2014 intakes are never against a surface.",
              "The phone arm tilts from \u22128\u00b0 to +62\u00b0, so it works as a video-call screen or a bedside clock.",
              "Two silicone-capped stoppers stop the laptop sliding without marking it.",
              "The right-hand DT-30 collar is where HoloBuddy (Product 5) docks."],
        build=["Lay the two arches face to face, then slide both rods through. The bridge is self-squaring.",
               "Drop the slat deck into the two notches \u2014 no fasteners, it locates on the arch profile.",
               "Clip the stoppers onto the front deck edge and slide the phone arm onto the left rod."],
        mats=["12 mm walnut / birch ply", "6 mm walnut", "6061 aluminium / 304 stainless", "TPU 95A", "PETG"],
        caption="AeroBridge with the G16 and the S24+ in place, at the 34\u00b0 / 24\u00b0 review angle."),
    "p2": dict(
        folio=11, num="06", key="P2", name="StealthVault 280 + SideDock ULT",
        kicker="HIDE THE BRICK, HANG THE HEADPHONES",
        blurb="A walnut-shielded box that clamps under the left edge and swallows the 280 W ROG power brick and its "
              "cable nest. Below it, a 608 bearing swings the Sony ULT WEAR out of the way in one 90\u00b0 movement.",
        does=["The brick stops living on the floor, so it stops collecting dust and tripping feet.",
              "Nine vent slots and an open bottom keep the brick cool; it is never fully enclosed.",
              "Swing the headphones out to put them on, push them back and they vanish under the desk.",
              "Cables route through the printed spine and out of sight \u2014 one cable to the wall, the rest hidden.",
              "The clamp jaws carry 2 mm EVA pads, so the walnut desk is never marked."],
        build=["Clamp the two printed arches over the left edge, 184 mm apart, and tighten the thumbscrews by hand.",
               "Slide the walnut floor into the arches, then hook the shield on from outside.",
               "Seat the 608 bearing into the hub, push the axle collar through the saddle and nip the M4 grub screw."],
        mats=["6 mm birch ply", "6 mm walnut", "20 mm walnut block", "PETG"],
        caption="Vault and SideDock from the outboard side: vent slots on the shield, the 608 dock with the headphones on it, and the two clamp arches."),
    "p3": dict(
        folio=12, num="07", key="P3", name="HydroSling",
        kicker="BOTTLE OUTSIDE THE DESK, NOTEBOOK UNDERNEATH",
        blurb="A sculpted PETG chalice hangs a 65\u201384 mm bottle outboard of the front-left edge, entirely off the "
              "work surface. Below the desk, a 6 mm walnut tray slides 110 mm on two DT-30 rails and holds an A5 "
              "notebook and pen.",
        does=["The bottle is off the desk, so a spill cannot reach the laptop \u2014 the main reason this product exists.",
              "The walnut coaster inside the chalice catches condensation.",
              "Pull the notebook tray out while you write, push it back and it disappears under the desk.",
              "Two tulip windows in the chalice let you see how much water is left.",
              "The whole thing lifts off in one piece when you need the corner of the desk."],
        build=["Clamp the two runners over the front-left edge, 148 mm apart.",
               "Slide the chalice body down onto the runners until it seats.",
               "Drop the walnut coaster into the base, hang the tray on its cleats and check the 110 mm travel."],
        mats=["6 mm walnut", "6 mm birch ply", "PETG"],
        caption="HydroSling at 34\u00b0 / 17\u00b0. The chalice hangs the bottle clear of the desk; the notebook tray sits under it."),
    "p4": dict(
        folio=13, num="08", key="P4", name="HexWing + Chimera Spire",
        kicker="PENS, DRAWER AND A MOUSE BUNGEE THAT CLEARS THE SWEEP",
        blurb="A stadium-shaped walnut-and-black caddy clamps to the right edge at Z = 16...52 mm only, so the rest "
              "of the edge stays completely clear for your forearm. Six pen wells, a magnetic micro-drawer and a "
              "94 mm airfoil spire that keeps the mouse cable off the mat.",
        does=["Six \u00d823 mm wells hold pens, a stylus, an SD reader and a USB stick upright and findable.",
              "The micro-drawer swallows dongles, a spare tip and a microSD \u2014 the things you lose.",
              "The spire holds the mouse cable 94 mm up, so the cable never drags across the mat.",
              "Because the clamp is tucked to the rear 36 mm, nothing touches your forearm at the front edge.",
              "The whole caddy lifts off in one movement if you need the right edge back."],
        build=["Clamp P4A over the right edge; it should stop with the walnut deck level and the jaw under the slab.",
               "Screw W4A to the clamp with two M3 \u00d7 12 through the deck.",
               "Drop P4B onto the deck, add W4B on top, then press P4D into its socket."],
        mats=["6 mm walnut", "PETG"],
        caption="HexWing at 40\u00b0 / 14\u00b0: the clamp disappears behind the desk edge, exactly as designed."),
    "p5": dict(
        folio=14, num="09", key="P5", name="HoloBuddy", kicker="A HOLOGRAM IN A 25.4 MM CUBE",
        blurb="A 38 \u00d7 40 \u00d7 42 mm matte-black optical chamber holds a 1-inch 50:50 K9 beam-splitter cube, a "
              "0.96 inch 128 \u00d7 64 OLED, an ESP32-C3 and a head-pat touch sensor. It mounts three ways: on the "
              "right DT-30 wing of the AeroBridge, on its own 608 pedestal, or freestanding on the desk.",
        does=["Tap the top and the image flips or pauses \u2014 that is the TTP223 head-pat sensor.",
              "Speak and the INMP441 microphone picks it up; the ESP32 streams levels to the PC over USB or Wi-Fi.",
              "The floating image sits above the mouse sweep, so it never gets in the way of your hand.",
              "A magnetic brow visor snaps over the cube to kill glare in a bright room.",
              "Two walnut cheeks hide the seams and make it look like a piece of furniture."],
        build=["Slide the DT-30 tongue on P5D into the right collar at X = 459 mm until it clicks.",
               "Or press the 608 into P5E, drop W5B on the desk and set the head on the hub for the pedestal mount.",
               "Load the ESP32 firmware, run the PC streamer, and the OLED image appears inside the cube."],
        mats=["6 mm walnut", "K9 optical glass, 50:50 coat", "matte-black PETG", "PETG"],
        caption="HoloBuddy on its right-wing DT-30 mount: the wing arm slides into the red collar and the joint disappears.",
        hero="p5m", inset="p5",
        inset_cap="The pedestal mount: walnut coaster, printed 608 hub, head docks straight on it."),
}


def pieces_for(key):
    out = []
    for part, size, mat, how, used in C.ALL:
        if used == key:
            tag = part.split("  ")[0]
            name = part.split("  ", 1)[1] if "  " in part else ""
            out.append((tag, name, size))
    return out


def p_product(d, which):
    cfg = PRODUCT_COPY[which]
    d.page()
    header(d, "%s \u00b7 %s" % (cfg["num"], cfg["key"]))
    y = title(d, "%s \u00b7 %s" % (cfg["key"], cfg["name"]), kicker=cfg["kicker"], size=23)
    y = d.para(cfg["blurb"], ML, y - 2, CW * 0.99, 9.3, 12.8, MUTE)

    # right column
    x = ML + 392.0
    w = W - K.MR - x
    yy = 124.0
    yy = section_head(d, "WHAT IT DOES FOR YOU", x, yy, w)
    yy = bullets(d, cfg["does"], x, yy, w, 8.4, 11.9, INK2, 3.2)
    yy += 9
    yy = section_head(d, "PUTTING IT TOGETHER", x, yy, w)
    yy = numbered(d, cfg["build"], x, yy, w, 8.4, 11.9, 3.2)
    yy += 9
    yy = section_head(d, "MATERIALS IN THIS PRODUCT", x, yy, w)
    for m in cfg["mats"]:
        d.text("\u00b7", x, yy, 8.4, "H", AMBER_L)
        d.text(m, x + 10, yy, 8.4, "H", INK2)
        yy += 12.4

    # left: picture well, sized so the piece list below always fits
    pieces = pieces_for(cfg["key"])
    rows = (len(pieces) + 1) // 2
    list_h = 26 + rows * 12.4
    fw = 358.0
    top = max(y + 16, 124.0)
    fh = min(300.0, H - 118 - list_h - top)
    if cfg.get("inset"):
        fh = min(fh, 250.0)
    panel(d, ML, top, fw, fh)
    img = os.path.join(OUT, "prod_%s.png" % (cfg.get("hero") or which))
    ir = ImageReader(img)
    iw, ih0 = ir.getSize()
    s = min((fw - 10) / iw, (fh - 10) / ih0)
    d.image(img, ML + (fw - iw * s) / 2, top + (fh - ih0 * s) / 2, iw * s, ih0 * s)
    cap_end = d.para(cfg["caption"], ML, top + fh + 12, fw, 7.5, 10.0, MUTE)

    py = cap_end + 14
    d.track("%d PIECE%s IN THIS PRODUCT" % (len(pieces), "" if len(pieces) == 1 else "S"),
            ML, py, 7.1, INK, 1.25)
    d.rule(ML, ML + fw, py + 6, color=INK, width=0.9)
    colw = (fw - 14) / 2
    for i, (tag, name, size) in enumerate(pieces):
        cx = ML + (i // rows) * (colw + 14)
        cy = py + 21 + (i % rows) * 12.4
        d.fit("%s  %s" % (tag, name), cx, cy, colw - 62, 7.7, "H", INK2, 6.2)
        d.text(size, cx + colw, cy, 7.4, "H", MUTE, "r")

    if cfg.get("inset"):
        ix, iy = x, yy + 16
        ih2 = min(H - 78 - iy, 150.0)
        if ih2 > 56:
            panel(d, ix, iy, w, ih2)
            d.image(os.path.join(OUT, "prod_%s.png" % cfg["inset"]), ix + 4, iy + 4, w - 8, ih2 - 8)
            d.para(cfg["inset_cap"], ix, iy + ih2 + 11, w, 7.4, 9.8, MUTE)
    footer(d, cfg["folio"])


# --------------------------------------------------------------- catalogue
FRAC = [0.205, 0.125, 0.175, 0.415, 0.080]
HEADS = ["PART", "SIZE mm", "MATERIAL", "HOW TO MAKE IT", "USED IN"]


def piece_table(d, title_label, blocks, note=None, x=None, w=None, y=104.0):
    """Dense catalogue table. Every row chains off the last write, so nothing overlaps."""
    x = ML if x is None else x
    w = CW if w is None else w
    cols, acc = [], 0.0
    for f in FRAC:
        cols.append(x + acc * w)
        acc += f
    widths = [f * w for f in FRAC]

    d.track(title_label, x, y, 7.1, INK, 1.3)
    d.rule(x, x + w, y + 6, color=INK, width=0.9)
    y += 19

    for head, rows in blocks:
        if head:
            d.track(head, x, y, 6.9, AMBER, 1.15)
            y += 15
        d.rect(x, y - 4, x + w, y + 8, fill=K.hx("#EDF0F4"), r=1)
        for i, name in enumerate(HEADS):
            d.track(name, cols[i] + 4, y + 3.5, 6.1, INK2, 0.9)
        y += 15
        for part, size, mat, how, used in rows:
            d.fit(part, cols[0] + 4, y, widths[0] - 8, 7.8, "HB", INK, 6.5)
            d.fit(size, cols[1] + 4, y, widths[1] - 8, 7.8, "H", INK2, 6.7)
            d.fit(mat, cols[2] + 4, y, widths[2] - 8, 7.8, "H", INK2, 6.5)
            d.fit(how, cols[3] + 4, y, widths[3] - 8, 7.8, "H", INK2, 6.3)
            d.fit(used, cols[4] + 4, y, widths[4] - 8, 7.8, "H", AMBER, 7.1)
            y += 12.4
        y += 11
    if note:
        y = d.para(note, x, y - 2, w, 7.5, 10.2, MUTE)
    return y


def p_catalog_wood(d):
    d.page()
    header(d, "11 \u00b7 PIECE CATALOG")
    title(d, "Every wood piece \u2014 14 parts", size=22)
    piece_table(d, "12 MM AND 6 MM SHEET", [
        ("THE TWO STRUCTURAL ARCHES ARE 12 mm", C.WOOD[:3]),
        ("DECKS, TRAYS AND COASTERS \u2014 ALL 6 mm", C.WOOD[3:]),
    ], note="Cut from 12 mm and 6 mm walnut / birch. All flat, all saw-and-drill work. Fixture and grain notes "
            "are on the cut-guide page.")
    footer(d, 15, "Cut from 12 mm and 6 mm walnut / birch. All flat, all saw-and-drill work.")


def p_catalog_metal(d):
    d.page()
    header(d, "11 \u00b7 PIECE CATALOG")
    title(d, "Metal, glass and the first printed nodes", size=21)
    y = piece_table(d, "METAL AND OPTICS \u2014 3 PARTS", [("", C.METAL)], y=104)
    piece_table(d, "3D-PRINTED NODES 1 OF 2 \u2014 13 PARTS", [("", C.PRINT_A)], y=y + 6)
    footer(d, 16, "PETG unless noted. 0.2 mm layers general, 0.16 mm on collars and hubs. Printed mass about 330 g.")


def p_catalog_print(d):
    d.page()
    header(d, "11 \u00b7 PIECE CATALOG")
    title(d, "The last 13 printed nodes", size=22)
    piece_table(d, "3D-PRINTED NODES 2 OF 2 \u2014 13 PARTS", [("", C.PRINT_B)], y=104)
    d.rect(ML, H - 128, W - K.MR, H - 86, fill=WASH, r=2)
    d.track("PRINT SETTINGS THAT MATTER", ML + 14, H - 110, 6.8, INK, 1.2)
    d.para("0.2 mm layers general \u00b7 0.16 mm on collars, hubs and the DT-30 joints \u00b7 4 walls \u00b7 25 % infill "
           "on structural nodes, 15 % on cosmetic parts \u00b7 no supports anywhere except P4D.",
           ML + 200, H - 110, W - K.MR - ML - 214, 8.1, 11.2, INK2)
    footer(d, 17, "Largest single node is P3A at 186.5 mm, so every part fits a 200 x 200 x 200 mm bed.")


# -------------------------------------------------------------- cut guides
SHEET_A = dict(w=450, h=220, t=12)
SHEET_C = dict(w=600, h=400, t=6)


def nest(d, x, y, w, h, sx, parts):
    """Nest stock into a sheet box drawn at `sx` px/mm.

    Each part is (px, py, pw, ph, name, kind), kind is "disc" for round stock,
    "round" for a rounded rectangular part, or None for square stock.
    """
    d.dash()
    d.rect(x, y, x + w * sx, y + h * sx, fill=None, stroke=FAINT)
    d.nodash()
    for px, py, pw, ph, name, kind in parts:
        cx, cy = x + (px + pw / 2) * sx, y + (py + ph / 2) * sx
        fill = K.hx("#C08B54") if kind else K.hx("#B07B3E")
        if kind == "disc":
            d.c.setFillColor(K.C(fill))
            d.c.circle(cx, K.H - cy, min(pw, ph) / 2 * sx, stroke=0, fill=1)
        else:
            d.rect(x + px * sx, y + py * sx, x + (px + pw) * sx, y + (py + ph) * sx,
                   fill=fill, r=2.5 if kind == "round" else 0.6)
        if name:
            d.fit(name, x + px * sx + 3, cy + 2.4, pw * sx - 6, 6.6, "HB", K.hx("#FFF6EA"), 4.8)


def p_cut(d):
    d.page()
    header(d, "12 \u00b7 CUT GUIDES")
    title(d, "Three stock items cover every wood and metal part", size=21)

    # ---- SHEET A (left column)
    y = 100.0
    d.track("SHEET A \u2014 12 mm WALNUT / BIRCH, 450 \u00d7 220 mm", ML, y, 7.0, INK, 1.15)
    sx = 250.0 / SHEET_A["w"]
    nest(d, ML, y + 10, SHEET_A["w"], SHEET_A["h"], sx, [
        (9, 9, 184, 131.4, "W1A  left arch", "round"),
        (201, 9, 184, 131.4, "W1B  right arch", "round"),
        (9, 149, 232, 62, "spare cauls  232 \u00d7 62", None),
    ])
    ya = y + 10 + SHEET_A["h"] * sx + 14
    ya = d.para("Both arches are 184 \u00d7 131.4 mm. They nest side by side, leaving 65 mm of spare stock at "
                "the right edge and 80 mm along the front for the cauls.",
                ML, ya, 250, 7.5, 10.0, MUTE)

    # ---- BAR B (left column, under sheet A)
    yb = ya + 22
    d.track("BAR B \u2014 \u00d88.0 mm ROD, 1000 mm STOCK", ML, yb, 7.0, INK, 1.15)
    by = yb + 14
    cx = ML
    for name, ln in [("M1A 360", 360), ("M1B 360", 360), ("spare 280", 280)]:
        wpx = 250.0 * ln / 1000.0
        d.rect(cx, by, cx + wpx - 2, by + 11, fill=K.hx("#C3CEDA"), r=5)
        d.text(name, cx + wpx / 2 - 1, by + 7.6, 6.6, "HB", K.hx("#33404E"), "c")
        cx += wpx
    d.para("Two straight cuts. De-burr, then draw the rod through 400-grit lengthwise for a brushed finish.",
           ML, by + 25, 250, 7.5, 10.0, MUTE)

    # ---- SHEET C (right column, the big one)
    xc = ML + 288
    d.track("SHEET C \u2014 6 mm WALNUT / BIRCH, 600 \u00d7 400 mm", xc, 100, 7.0, INK, 1.15)
    sxc = 380.0 / SHEET_C["w"]
    nest(d, xc, 110, SHEET_C["w"], SHEET_C["h"], sxc, [
        (8, 8, 360, 182, "W1C  deck 360 \u00d7 182", None),
        (378, 8, 172, 162, "W3B  notebook tray", None),
        (8, 200, 184, 84, "W2B  vault shield", None),
        (8, 294, 184, 52, "W2A  vault floor", None),
        (204, 198, 124, 72, "W4A  caddy floor", None),
        (204, 280, 124, 72, "W4B  pen collar", None),
        (204, 362, 56, 30, "W4C", None),
        (378, 186, 84, 84, "W3A", "disc"),
        (378, 282, 70, 70, "W5B", "disc"),
        (464, 282, 34, 30, "W5A", None),
    ])
    cap = d.para("All eleven 6 mm parts fit one 600 \u00d7 400 sheet with roughly 20 % spare. The two discs are "
                 "the coaster and the pedestal base; cut them with a hole saw.",
                 xc, 110 + SHEET_C["h"] * sxc + 14, 380, 7.5, 10.0, MUTE)

    # ---- WHAT TO BUY, chained off the caption so it cannot collide
    yq = cap + 20
    d.track("WHAT TO BUY", xc, yq, 7.1, INK, 1.25)
    d.rule(xc, xc + 380, yq + 6, color=INK, width=0.9)
    items = [("WALNUT / BIRCH PLY", "12 mm sheet and one 600 \u00d7 400 \u00d7 6 mm offcut"),
             ("ROD", "2 \u00d7 360 mm of \u00d88 mm 6061 or 304"),
             ("FILAMENT", "330 g PETG plus about 40 g TPU 95A"),
             ("OPTICS & ELECTRONICS", "K9 cube, 0.96 inch SSD1306, ESP32-C3, TTP223, INMP441"),
             ("HARDWARE", "2 \u00d7 608-2RS, 6 \u00d7 3 mm magnets, M3 / M4 inserts, 2 mm EVA")]
    yy = yq + 22
    for label, val in items[:3]:
        d.fit(label, xc, yy, 380, 6.3, "HB", AMBER, 5.8)
        yy = d.para(val, xc, yy + 9.4, 380, 7.5, 9.6, INK2) + 4.4
    # last two side by side, under the first three
    yy += 1
    for k, (label, val) in enumerate(items[3:]):
        col = xc + k * 196
        d.fit(label, col, yy, 180, 6.3, "HB", AMBER, 5.8)
        d.para(val, col, yy + 9.4, 180, 7.5, 9.6, INK2)
    yy += 26

    if yy > H - 56:
        raise AssertionError("shopping list runs into the footer at y=%.1f" % yy)
    footer(d, 18, "Sheet outlines are nested, not to exact scale. Allow a 3 mm kerf and 6 mm between parts.")


# ------------------------------------------------------------ closing pages
def p_build(d):
    d.page()
    header(d, "13 \u00b7 BUILDING IT")
    title(d, "The order matters: print the coupon, then the joints, then everything else", size=21)
    steps = [("Print P0 and test-fit the hardware",
              "60 min print. Press in a 608, drop in a magnet, slide a DT-30 tongue. Adjust your slicer, not the model."),
             ("Cut and finish the wood",
              "Rip the 12 mm arches, then route the 6 mm sheet. Sand to 320 and oil everything before assembly \u2014 "
              "it is far easier flat."),
             ("Cut the two rods",
              "Two 360 mm lengths. De-burr both ends; a burr will not pass through the \u00d88.1 bores in the arches."),
             ("Print the structural nodes",
              "P1E collars, P2A/P2B clamp arches, P2D hub, P3B runners, P4A clamp first \u2014 these set every fit. "
              "4 walls, 0.16 mm layers."),
             ("Assemble each product on the bench",
              "Build P1 through P5 one at a time and check each on the desk before starting the next. Every product "
              "is independent."),
             ("Fit the magnets and bearings",
              "Magnets last: check polarity with a marker dot before you press them in. A reversed magnet cannot be "
              "removed."),
             ("Set the clamp pads",
              "2 mm EVA on every jaw face. This is what keeps the desk unmarked, and the only thing you should ever "
              "replace."),
             ("Load the HoloBuddy firmware",
              "Flash the ESP32-C3, run pc_holo_streamer.py, then calibrate the 45\u00b0 mirror so the image sits "
              "upright.")]
    y = 104.0
    for i, (head, body) in enumerate(steps, 1):
        d.c.setFillColor(K.C(AMBER))
        d.c.circle(ML + 8, K.H - (y + 3), 8.6, stroke=0, fill=1)
        d.text(str(i), ML + 8, y + 6.4, 8.6, "HB", K.hx("#FFFFFF"), "c")
        d.text(head, ML + 28, y + 4, 10.4, "HB", INK)
        yy = d.para(body, ML + 28, y + 17, CW * 0.62, 8.4, 11.8, INK2)
        if i < len(steps):
            d.dash(1.2, 2.4, FAINT, 0.6)
            d.vline(ML + 8, y + 14, yy + 4, color=FAINT)
            d.nodash()
        y = yy + 12

    d.rect(ML, H - 104, W - K.MR, H - 56, fill=WASH, r=2)
    d.track("TOOLKIT \u2014 NOTHING EXOTIC", ML + 16, H - 84, 7.0, INK, 1.25)
    d.para("Jigsaw or band saw \u00b7 \u00d884 and \u00d870 hole saws \u00b7 6 mm router bit \u00b7 3 / 4 / 8 mm drill "
           "bits \u00b7 Torx and hex keys \u00b7 320-grit paper \u00b7 Danish oil \u00b7 a 3D printer with a 200 mm bed. "
           "No CNC, no laser and no sheet-metal brake is required anywhere in this build.",
           ML + 16, H - 66, W - K.MR - ML - 32, 8.4, 12.0, INK2)
    footer(d, 19)


def p_daily(d):
    d.page()
    header(d, "14 \u00b7 DAILY USE")
    title(d, "A normal working day with the system")
    events = [("08:40", "Sit down", "The keyboard comes out of the garage, the mouse is already on a clear mat. "
                                    "HoloBuddy shows the time and the first meeting."),
              ("09:15", "Laptop docked", "The G16 sits at 18\u00b0 with its intakes open. The phone tilts up on the "
                                         "MagPivot for a video call."),
              ("11:00", "Water", "The bottle goes into the chalice, outboard of the desk. It cannot spill onto the "
                                 "laptop because it is not on the desk."),
              ("13:30", "Lunch", "Headphones swing out on the 608, then swing back under. The notebook tray pulls "
                                 "out for notes."),
              ("15:00", "Heads-down", "Pens and the dongle come out of the HexWing drawer. The spire holds the mouse "
                                      "cable off the mat."),
              ("17:30", "Pack down", "Keyboard into the garage, lid closed, phone off the arm. The desk is clear in "
                                     "under a minute.")]
    y = 110.0
    for i, (t, head, body) in enumerate(events):
        d.text(t, ML, y, 9.0, "HB", MUTE)
        d.c.setFillColor(K.C(AMBER))
        d.c.circle(ML + 74, K.H - y - 3, 3.6, stroke=0, fill=1)
        d.text(head, ML + 90, y, 11.0, "HB", INK)
        yy = d.para(body, ML + 90, y + 14, CW * 0.66, 8.7, 12.2, INK2)
        if i < len(events) - 1:
            d.vline(ML + 74, y + 2, yy - 4, color=FAINT)
        y = yy + 20

    d.rect(ML + 200, H - 152, W - K.MR, H - 112, fill=K.hx("#FBF3E9"), r=2)
    d.track("MAINTENANCE", ML + 214, H - 137, 6.8, AMBER, 1.2)
    d.para("Re-oil the wood once a year \u00b7 brush the slat slots monthly \u00b7 replace the EVA pads when they "
           "compress \u00b7 re-flash the ESP32 only if you change the optics.",
           ML + 300, H - 137, W - K.MR - ML - 314, 8.1, 11.2, INK2)
    footer(d, 20)


def p_appendix(d):
    d.page()
    header(d, "APPENDIX")
    title(d, "Files, names and how this book stays true")
    x, y = ML, 104.0
    d.track("WHAT IS IN THE REPOSITORY", x, y, 7.1, INK, 1.25)
    d.rule(x, x + 250, y + 6, color=INK, width=0.9)
    yy = y + 24
    for name, sub in [("Product0_FitCheckGauge/", "Fit coupon \u2014 build_product() plus its .manifest"),
                      ("Product1_AeroBridgeG16/", "Bridge, deck, collars, MagPivot arm and disc"),
                      ("Product2_StealthVaultULT/", "Vault arches, shield, cable spine, bearing hub and saddle"),
                      ("Product3_HydroSling/", "Chalice, coaster, runners, cleats and notebook tray"),
                      ("Product4_HexWingSpire/", "Right clamp, fluted core, drawer and airfoil spire"),
                      ("Product5_HoloBuddy/", "Optical core, electronics base, visor, wing and pedestal"),
                      ("Master_FullDeskSetup/", "The whole desk in one script: exports STL, 3MF, STEP + CSV manifest"),
                      ("HoloBuddy_Firmware_And_PC/", "ESP32 firmware, PC streamer, wiring and optics guide"),
                      ("verify_fusion_scripts.py", "Rebuilds every model headless and checks 15 geometric rules")]:
        d.fit(name, x, yy, 250, 8.4, "HB", INK, 6.6)
        yy = d.para(sub, x, yy + 11, 250, 7.8, 10.2, MUTE) + 5

    x2 = ML + 316
    y2 = 104.0
    d.track("THE CHECKS THIS BOOK DEPENDS ON", x2, y2, 7.1, INK, 1.25)
    d.rule(x2, x2 + 300, y2 + 6, color=INK, width=0.9)
    yy = y2 + 24
    for c in ["Every part fits a 200 mm bed (max 186.5 mm)",
              "Nothing penetrates the back wall (Z \u2265 0)",
              "The vault and the headphone knuckle never overlap",
              "The HoloBuddy tongue seats at X = 459 mm",
              "The keyboard garage clears both arches",
              "The 165 \u00d7 230 mm mouse sweep is clear",
              "All 41 parts form 6 desk-anchored groups",
              "The 415 mm knee void is clear",
              "No part floats free of the assembly"]:
        d.text("\u2713", x2, yy, 8.6, "H", GREEN)
        d.text(c, x2 + 14, yy, 8.6, "H", INK2)
        yy += 15

    d.rect(ML, H - 164, W - K.MR, H - 92, fill=WASH, r=2)
    d.track("ON THE REFERENCE HARDWARE", ML + 16, H - 142, 7.1, INK, 1.25)
    d.para("The hardware in this build (ROG Strix G16, AULA F75, Kreo Chimera V2, Sony ULT WEAR, Samsung S24+, "
           "ROG 280 W brick) was specified in the brief. The amzn.to shortlinks in that brief could not be opened "
           "from the build environment, so no link-dependent specification is baked into any model. Every camera, "
           "port and pocket is driven by a named Fusion user parameter, so if a device changes you edit one number "
           "and rebuild.",
           ML + 16, H - 122, W - K.MR - ML - 32, 8.3, 12.0, INK2)
    footer(d, 21, "Autodesk Fusion models, drawings and this document were generated from the same geometry.")


# --------------------------------------------------------------------- main
def build():
    import assets
    import ortho

    print("rendering illustrations ...")
    assets.build_all()

    print("rendering orthographic views ...")
    s_plan = G.scene_full(lid=False, keyboard_on=False)     # plan: lid + keyboard lifted out
    s_full = G.scene_full()
    img_top, m_top = ortho.render_ortho(s_plan, "top", px_per_mm=1.8, pad_mm=8)
    img_front, m_front = ortho.render_ortho(s_full, "front", px_per_mm=1.8, pad_mm=8)
    img_side, m_side = ortho.render_ortho(s_full, "side", px_per_mm=1.8, pad_mm=8)
    p_top_img = os.path.join(OUT, "ortho_top.png")
    p_front_img = os.path.join(OUT, "ortho_front.png")
    p_side_img = os.path.join(OUT, "ortho_side.png")
    img_top.save(p_top_img)
    img_front.save(p_front_img)
    img_side.save(p_side_img)

    d = Doc(DEST)
    p_cover(d)
    p_contents(d)
    p_howto(d)
    p_glance(d)
    p_top(d, m_top, p_top_img)
    p_front(d, m_front, p_front_img)
    p_side(d, m_side, p_side_img)
    p_why(d)
    for w in ("p0", "p1", "p2", "p3", "p4", "p5"):
        p_product(d, w)
    p_catalog_wood(d)
    p_catalog_metal(d)
    p_catalog_print(d)
    p_cut(d)
    p_build(d)
    p_daily(d)
    p_appendix(d)
    d.save()
    print("wrote", DEST, d.n, "pages")
    return DEST


if __name__ == "__main__":
    build()

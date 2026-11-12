"""Small layout kit on top of reportlab.

Coordinate convention: the origin is the TOP-LEFT of the page and y grows
downwards, which is how a person lays out a document.  Conversion to
reportlab's bottom-left origin happens in `_Y`.

Two rules this file exists to enforce, both learned the hard way:

  * `para()` returns the baseline of the NEXT free line, never
    `y + leading` of a block that already consumed its last line.
    Getting this wrong is what made stacked label/value blocks collide.
  * Letter-spacing is drawn glyph by glyph with `pdfmetrics.stringWidth`.
    reportlab's Canvas has no `setCharSpace`, so tracked labels must be
    positioned manually.
"""
import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as rcanvas

from render3d import hx

def C(t):
    """Palette tuples are 0-255 (shared with the renderer); reportlab wants 0-1."""
    if isinstance(t, str):
        return tuple(int(t.lstrip("#")[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    if len(t) == 3 and max(t) <= 1.0:
        return tuple(t)
    return tuple(v / 255.0 for v in t)


W, H = 842.0, 595.0                      # A4 landscape, points
ML, MR = 34.0, 34.0
CW = W - ML - MR

INK = hx("#12171D")
INK2 = hx("#39424D")
MUTE = hx("#8A93A0")
FAINT = hx("#C9D0D9")
RULE = hx("#DCE2E9")
PAPER = hx("#FFFFFF")
WASH = hx("#F3F5F8")
AMBER = hx("#8A5626")
AMBER_L = hx("#B07B3E")
RED = hx("#C2212F")
GREEN = hx("#2E7D5B")
BLUE = hx("#2F6E9E")

FONTS = {"H": "Helvetica", "HB": "Helvetica-Bold", "HO": "Helvetica-Oblique",
         "HBO": "Helvetica-BoldOblique"}


class Doc:
    def __init__(self, path):
        self.path = path
        self.c = rcanvas.Canvas(path, pagesize=(W, H))
        self.c.setTitle("Designer Hybrid v2 - 630 x 280 desk system")
        self.c.setAuthor("Desk system build documentation")
        self.c.setSubject("Illustrated build guide, catalogue and cut sheets")
        self.n = 0

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _Y(y):
        return H - y

    def _font(self, font, size):
        self.c.setFont(FONTS.get(font, font), size)

    def _wrap(self, s, w, size, font):
        self._font(font, size)
        out = []
        for block in s.split("\n"):
            if not block:
                out.append("")
                continue
            words, line = block.split(), ""
            for wd in words:
                t = (line + " " + wd).strip()
                if pdfmetrics.stringWidth(t, FONTS.get(font, font), size) <= w or not line:
                    line = t
                else:
                    out.append(line)
                    line = wd
            out.append(line)
        return out

    # -------------------------------------------------------------- prims
    def page(self, bg=PAPER):
        if self.n:
            self.c.showPage()
        self.n += 1
        self.c.setFillColor(C(bg))
        self.c.rect(0, 0, W, H, stroke=0, fill=1)
        return self

    def text(self, s, x, y, size=10, font="H", color=INK, align="l", w=0):
        self._font(font, size)
        self.c.setFillColor(C(color))
        if align == "l":
            self.c.drawString(x, self._Y(y), s)
        elif align == "r":
            self.c.drawRightString(x, self._Y(y), s)
        elif align == "c":
            self.c.drawCentredString(x, self._Y(y), s)
        elif align == "j":                       # justify inside [x, x+w]
            words = s.split()
            if len(words) < 2:
                self.c.drawString(x, self._Y(y), s)
                return
            gap = (w - pdfmetrics.stringWidth(s, FONTS.get(font, font), size)) / (len(words) - 1)
            cx = x
            for wd in words:
                self.c.drawString(cx, self._Y(y), wd)
                cx += pdfmetrics.stringWidth(wd + " ", FONTS.get(font, font), size) + gap
        return self

    def fit(self, s, x, y, maxw, size=8.0, font="H", color=INK2, minsize=6.4):
        """Draw text that must not cross `maxw`: shrink to fit, then elide."""
        face = FONTS.get(font, font)
        sz = size
        while sz > minsize and pdfmetrics.stringWidth(s, face, sz) > maxw:
            sz -= 0.2
        if pdfmetrics.stringWidth(s, face, sz) > maxw:
            while s and pdfmetrics.stringWidth(s + "...", face, sz) > maxw:
                s = s[:-1]
            s = s.rstrip() + "..."
        self._font(font, sz)
        self.c.setFillColor(C(color))
        self.c.drawString(x, self._Y(y), s)
        return self

    def track(self, s, x, y, size=7.4, color=MUTE, spacing=1.05, font="HB", align="l"):
        """Letter-spaced label, drawn glyph by glyph (no setCharSpace in reportlab)."""
        face = FONTS.get(font, font)
        total = 0.0
        for i, ch in enumerate(s):
            total += pdfmetrics.stringWidth(ch, face, size) + (spacing if i < len(s) - 1 else 0)
        if align == "r":
            x -= total
        elif align == "c":
            x -= total / 2.0
        self._font(font, size)
        self.c.setFillColor(C(color))
        cx = x
        for ch in s:
            self.c.drawString(cx, self._Y(y), ch)
            cx += pdfmetrics.stringWidth(ch, face, size) + spacing
        return total

    def para(self, s, x, y, w, size=9.6, leading=13.6, color=INK2, font="H", align="l"):
        """Draw wrapped text; `y` is the FIRST BASELINE. Returns the next free baseline."""
        face = FONTS.get(font, font)
        self._font(font, size)
        self.c.setFillColor(C(color))
        yy = y
        for line in self._wrap(s, w, size, face):
            if align == "j" and line and not line.endswith("."):
                words = line.split()
                if len(words) > 1:
                    gap = (w - pdfmetrics.stringWidth(line, face, size)) / (len(words) - 1)
                    cx = x
                    for wd in words:
                        self.c.drawString(cx, self._Y(yy), wd)
                        cx += pdfmetrics.stringWidth(wd + " ", face, size) + gap
                else:
                    self.c.drawString(x, self._Y(yy), line)
            else:
                self.c.drawString(x, self._Y(yy), line)
            yy += leading
        return yy                                  # <- next free baseline

    def rule(self, x0, x1, y, color=RULE, width=0.6):
        self.c.setStrokeColor(C(color))
        self.c.setLineWidth(width)
        self.c.line(x0, self._Y(y), x1, self._Y(y))
        return self

    def rect(self, x0, y0, x1, y1, fill=None, stroke=None, width=0.6, r=0.0):
        if fill is not None:
            self.c.setFillColor(C(fill))
        if stroke is not None:
            self.c.setStrokeColor(C(stroke))
            self.c.setLineWidth(width)
        self.c.roundRect(x0, self._Y(y1), x1 - x0, y1 - y0, r,
                         stroke=1 if stroke is not None else 0,
                         fill=1 if fill is not None else 0)
        return self

    def vline(self, x, y0, y1, color=RULE, width=0.6):
        self.c.setStrokeColor(C(color))
        self.c.setLineWidth(width)
        self.c.line(x, self._Y(y0), x, self._Y(y1))
        return self

    def image(self, path, x, y, w, h, r=0.0):
        """Place an image whose TOP-LEFT corner is (x, y)."""
        if not path or not os.path.exists(path):
            return self
        if r:
            self.c.saveState()
            p = self.c.beginPath()
            p.roundRect(x, self._Y(y + h), w, h, r)
            self.c.clipPath(p, stroke=0, fill=0)
            self.c.drawImage(path, x, self._Y(y + h), w, h, mask=None)
            self.c.restoreState()
        else:
            self.c.drawImage(path, x, self._Y(y + h), w, h, mask=None)
        return self

    def dash(self, on=1.4, off=2.2, color=FAINT, width=0.5):
        self.c.setStrokeColor(C(color))
        self.c.setLineWidth(width)
        self.c.setDash(on, off)
        return self

    def nodash(self):
        self.c.setDash()
        return self

    def save(self):
        self.c.showPage()
        self.c.save()
        return self.path

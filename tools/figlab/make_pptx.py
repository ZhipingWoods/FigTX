#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 05 架构图 / 06 机制图导出为原生 PPTX（每个方框/箭头都是可拖动编辑的形状）。

用法：
    python3 make_pptx.py            # 生成两张
输出：
    public/renders-fig/edit/rep-05-architecture.pptx
    public/renders-fig/edit/rep-06-mechanism.pptx
"""
from __future__ import annotations

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "public", "renders-fig", "edit")
OUT = os.path.abspath(OUT)

# ---- 配色（与 frameworks_mpl 一致） ----
def _rgb(h):
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


C_BLUE = _rgb("D6E8F7")
C_SCALE = _rgb("FBF0C4")
C_MM = _rgb("DCDCDC")
C_ROPE = _rgb("F7941E")
C_RELU = _rgb("FBE4E0")
C_GRN = _rgb("D5F0D0")
C_PINK = _rgb("FADBD8")
C_BK = _rgb("000000")
C_WHITE = _rgb("FFFFFF")
C_GRN2 = _rgb("78B808")
C_KV = _rgb("A81838")
C_MASK = _rgb("B4B4B4")
C_CELL = _rgb("DCEBF8")
C_PAD = _rgb("1B6FD6")
C_GREY = _rgb("9A9A9A")
FONT = "Times New Roman"


class Canvas:
    """把图形单位坐标映射到 PPTX 的 EMU。"""

    def __init__(self, xmax, ymax, ar, slide_w_in=13.333):
        self.xmax, self.ymax = float(xmax), float(ymax)
        self.sw = Emu(int(slide_w_in * 914400))
        self.sh = Emu(int(self.sw * (ymax / xmax)))
        self.prs = Presentation()
        self.prs.slide_width = self.sw
        self.prs.slide_height = self.sh
        self.slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self.ar = ar

    def _x(self, x):
        return Emu(int(self.sw * (x / self.xmax)))

    def _y(self, y):
        return Emu(int(self.sh * (1 - y / self.ymax)))

    def _w(self, w):
        return Emu(int(self.sw * (w / self.xmax)))

    def _h(self, h):
        return Emu(int(self.sh * (h / self.ymax)))

    # ---------- 形状 ----------
    def rrect(self, cx, cy, w, h, fc, text=None, fs=11, rot=0, lw=1.6,
              bold=True, tc=None, pad=0.16):
        sp = self.slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            self._x(cx - w / 2), self._y(cy + h / 2), self._w(w), self._h(h))
        try:
            sp.adjustments[0] = pad
        except Exception:
            pass
        self._style(sp, fc, lw)
        if text:
            self._text(sp, text, fs, bold, tc or C_BK, rot)
        return sp

    def rect(self, x0, y0, w, h, fc, ec=None, lw=1.0, text=None, fs=10,
             tc=None, bold=False):
        sp = self.slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, self._x(x0), self._y(y0 + h), self._w(w), self._h(h))
        self._style(sp, fc, lw, ec)
        if text:
            self._text(sp, text, fs, bold, tc or C_BK)
        return sp

    def poly(self, pts, fc, lw=1.2, ec=None):
        """闭合多边形（自由曲线）。"""
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0 = min(xs), min(ys)
        w, h = max(xs) - x0, max(ys) - y0
        ff = self.slide.shapes.build_freeform(
            self._x(x0), self._y(y0 + h), scale=1.0)
        ff.add_line_segments([(self._x(p[0]), self._y(p[1])) for p in pts[1:]],
                             close=True)
        sp = ff.convert_to_shape()
        self._style(sp, fc, lw, ec)
        return sp

    def txt(self, x, y, s, fs=10, bold=False, color=None, ha="center",
            va="center", rot=0):
        """文本框：宽度按字符数估算，避免被挤压换行。"""
        lines = s.split("\n")
        ncol = max(len(ln) for ln in lines)
        # 1 字符 ≈ 0.62 * 字号(pt) 宽；换算到图形单位
        pt2unit_x = self.xmax / (13.333 * 72.0)
        w = max(4.0, ncol * fs * (0.72 if bold else 0.62) * pt2unit_x * 1.15)
        h = max(2.0, len(lines) * fs * 1.35 * (self.ymax / (self.sh / 914400 * 72.0)))
        x0 = x - w / 2 if ha == "center" else (x if ha == "left" else x - w)
        tb = self.slide.shapes.add_textbox(
            self._x(x0), self._y(y + h / 2), self._w(w), self._h(h))
        tf = tb.text_frame
        tf.word_wrap = len(lines) > 1
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = {"center": PP_ALIGN.CENTER, "left": PP_ALIGN.LEFT,
                       "right": PP_ALIGN.RIGHT}[ha]
        r = p.add_run()
        r.text = s
        r.font.size = Pt(fs)
        r.font.bold = bold
        r.font.name = FONT
        r.font.color.rgb = color or C_BK
        if rot:
            tb.rotation = rot
        return tb

    def arrow(self, pts, lw=1.4, color=None, head="triangle"):
        """正交折线箭头：中间段直线，末段带箭头。"""
        color = color or C_BK
        for i in range(len(pts) - 1):
            c = self.slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT,
                self._x(pts[i][0]), self._y(pts[i][1]),
                self._x(pts[i + 1][0]), self._y(pts[i + 1][1]))
            c.line.color.rgb = color
            c.line.width = Pt(lw)
            if i == len(pts) - 2:
                ln = c.line._get_or_add_ln()
                te = ln.makeelement(qn("a:tailEnd"),
                                    {"type": head, "w": "med", "len": "med"})
                ln.append(te)

    def line(self, pts, lw=1.4, color=None, dash=None):
        color = color or C_BK
        for i in range(len(pts) - 1):
            c = self.slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT,
                self._x(pts[i][0]), self._y(pts[i][1]),
                self._x(pts[i + 1][0]), self._y(pts[i + 1][1]))
            c.line.color.rgb = color
            c.line.width = Pt(lw)
            if dash:
                from pptx.enum.dml import MSO_LINE_DASH_STYLE
                c.line.dash_style = MSO_LINE_DASH_STYLE.DASH

    # ---------- 内部 ----------
    def _style(self, sp, fc, lw, ec=None):
        sp.fill.solid()
        sp.fill.fore_color.rgb = fc
        sp.line.color.rgb = ec or C_BK
        sp.line.width = Pt(lw)
        sp.shadow.inherit = False
        if sp.has_text_frame:
            sp.text_frame.word_wrap = True
            sp.text_frame.margin_left = sp.text_frame.margin_right = 0
            sp.text_frame.margin_top = sp.text_frame.margin_bottom = 0
            sp.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    def _text(self, sp, text, fs, bold, color, rot=0):
        tf = sp.text_frame
        lines = text.split("\n")
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = ln
            r.font.size = Pt(fs)
            r.font.bold = bold
            r.font.name = FONT
            r.font.color.rgb = color
        if rot:
            sp.rotation = rot

    def save(self, name):
        os.makedirs(OUT, exist_ok=True)
        p = os.path.join(OUT, name + ".pptx")
        self.prs.save(p)
        print("saved", p)
        return p


def _grid(cv, x0, y0, cw, ch, ncols, nrows, fn, lw=1.2):
    for r in range(nrows):
        for c in range(ncols):
            cv.rect(x0 + c * cw, y0 + (nrows - 1 - r) * ch, cw, ch, fn(r, c), lw=lw)


def _stack(cv, x, y, size, n=5, grey=False):
    for k in range(n - 1, -1, -1):
        o = k * size * 0.030
        fc = C_GREY if grey else _rgb("12101A")
        cv.rect(x - size / 2 + o, y - size / 2 + o, size, size, fc, lw=0.6)
        if grey:
            continue
        s = size / 18.0
        cv.rect(x - 6 * s + o, y - 3 * s + o, 8 * s, 9 * s, _rgb("1B7E96"), lw=0)
        cv.rect(x + 1 * s + o, y - 5 * s + o, 7 * s, 5 * s, _rgb("B03A2E"), lw=0)
        cv.rect(x - 3 * s + o, y + 1 * s + o, 4 * s, 6 * s, _rgb("7D3C98"), lw=0)


# ---------------------------------------------------------------- 06 机制图

def build_06():
    cv = Canvas(321, 100, 3.21)

    # 图例
    ly, lh, lx = 94.6, 4.8, 30
    for fc, txt in [(C_WHITE, "Token"), (C_MASK, "Mask"),
                    (C_KV, "KV Cache"), (C_GRN2, "Compute")]:
        cv.rect(lx, ly, lh, lh, fc, lw=1.2)
        cv.txt(lx + lh + 1.4, ly + lh / 2, txt, 10, ha="left")
        lx += lh + 2.2 + len(txt) * 1.55

    # 分隔虚线
    for x in (98, 162, 250, 258):
        cv.line([(x, 8), (x, 86)], lw=1.3, dash=True)

    # ---- Vanilla Attention ----
    gx, gy, cw, ch = 8.0, 20.0, 15.4, 15.4
    _grid(cv, gx, gy, cw, ch, 4, 4, lambda r, c: C_GRN2)
    for i, r in enumerate([0, 3]):
        cv.txt(gx - 5.0, gy + (3 - r) * ch + ch / 2, "Q%d" % (1 if r == 0 else 4), 10)
    for r in (1, 2):
        cv.txt(gx - 5.0, gy + (3 - r) * ch + ch / 2, "...", 10)
    cv.txt(gx + cw * 0.5, gy + 4 * ch + 3.4, "K1", 10)
    cv.txt(gx + cw * 3.5, gy + 4 * ch + 3.4, "KN", 9)
    for c in (1, 2):
        cv.txt(gx + (c + 0.5) * cw, gy + 4 * ch + 3.4, "...", 10)
    cv.txt(gx + 2 * cw, 15.0, "Vanilla Attention", 12)
    cv.txt(gx + 4 * cw + 2.2, gy + 2 * ch, "x", 20, bold=True)

    vx = gx + 4 * cw + 13.5
    _grid(cv, vx, gy, cw, ch, 1, 4, lambda r, c: C_CELL)
    cv.txt(vx + cw / 2, gy + 4 * ch + 3.4, "d", 10)
    for i in range(4):
        cv.txt(vx + cw / 2, gy + (3 - i) * ch + ch / 2, "V%d" % (i + 1), 9)
    cv.txt(vx - 3.4, gy + 2 * ch, "N", 10)

    # ---- Linear Attention ----
    lx2, ch2 = 104.0, ch / 2.0
    _grid(cv, lx2, gy, cw, ch2, 1, 8, lambda r, c: C_CELL)
    cv.txt(lx2 + cw / 2, gy + 8 * ch2 + 3.4, "d", 10)
    cv.txt(lx2 - 6.5, gy + 4 * ch2, "N", 10)
    for i in range(4):
        cv.txt(lx2 + cw / 2, gy + (7 - i) * ch2 + ch2 / 2, "Q%d" % (i + 1), 8.5)
        cv.txt(lx2 + cw / 2, gy + (3 - i) * ch2 + ch2 / 2, "V%d" % (i + 1), 8.5)
    for y0b, y1b, lbl in [(gy + 4 * ch2 + 1.0, gy + 8 * ch2 - 1.0, "Block1"),
                          (gy + 1.0, gy + 4 * ch2 - 1.0, "BlockN")]:
        xb = lx2 - 4.2
        cv.line([(xb, y1b), (xb - 1.4, y1b), (xb - 1.4, y0b), (xb, y0b)], lw=1.1)
        cv.txt(xb - 3.2, (y0b + y1b) / 2, lbl, 7.5, rot=270)
    cv.txt(lx2 + cw + 5.2, gy + 4 * ch2, "x", 20, bold=True)
    sx, sy = lx2 + cw + 12.0, gy + 4 * ch2 - 8.5
    cv.rect(sx, sy, 17, 17, C_GRN2, lw=1.2)
    cv.txt(sx + 8.5, sy + 8.5, "Sum KiVi", 8)
    cv.txt(sx + 8.5, sy + 19.4, "d", 10)
    cv.txt(sx + 19.6, sy + 8.5, "d", 10)
    cv.txt(lx2 + cw / 2, 15.0, "Linear Attention", 12)

    # ---- Causal Linear Attention ----
    cx0 = 180.0
    cv.txt(cx0 + 2 * cw, gy + 4 * ch + 3.4, "d", 10)
    cv.txt(cx0 - 13.0, gy + 3 * ch, "d", 10)

    def _causal(r, c):
        if c == r + 1:
            return C_GRN2
        if c <= r:
            return C_KV
        return C_MASK

    _grid(cv, cx0, gy, cw, ch, 4, 4, _causal, lw=1.4)
    for r in range(3):
        yy = gy + (3 - r) * ch + ch / 2
        cv.arrow([(cx0 + 0.2 * cw, yy), (cx0 + (r + 0.95) * cw, yy)],
                 lw=2.0, color=C_WHITE)
        cv.txt(cx0 + (r + 1.5) * cw, yy + 3.4, "Sum%d" % (r + 1), 7)
    cv.txt(cx0 + 1.2 * cw, gy + 0.5 * ch, "Cumulative Sum", 9, bold=True,
           color=C_WHITE, ha="left")
    for y0b, y1b, lbl in [(gy + 2 * ch + 1.0, gy + 4 * ch - 1.0, "Block1"),
                          (gy + 1.0, gy + 2 * ch - 1.0, "BlockN")]:
        xb = cx0 - 6.0
        cv.line([(xb, y1b), (xb - 1.4, y1b), (xb - 1.4, y0b), (xb, y0b)], lw=1.1)
        cv.txt(xb - 3.2, (y0b + y1b) / 2, lbl, 7.5, rot=270)
    cv.txt(cx0 + 2 * cw, 15.0, "Causal Linear Attention", 12)

    # ---- Mix-FFN ----
    bx, bw, bh = 272.0, 30.0, 7.4
    rows = [("Token-2", C_GRN2), ("Token-1", C_GRN2), ("Zero Padding", C_PAD),
            (None, None), ("Cached Token-1", C_KV), ("Token0", C_GRN2),
            ("Token1", C_GRN2)]
    ycur = gy + 4 * ch + 2.0
    ys = {}
    for name, fc in rows:
        if name is None:
            ycur -= 4.6
            continue
        ycur -= bh
        cv.rrect(bx + bw / 2, ycur + bh / 2, bw, bh, fc, name, 10,
                 tc=C_WHITE, pad=0.2)
        ys[name] = ycur + bh / 2
        ycur -= 1.4
    for y0b, y1b, lbl in [(ys["Token-1"] - bh / 2 - 1.0, ys["Token-2"] + bh / 2 + 1.0, "Block1"),
                          (ys["Token1"] - bh / 2 - 1.0, ys["Cached Token-1"] + bh / 2 + 1.0, "Block2")]:
        xb = bx - 4.0
        cv.line([(xb, y1b), (xb - 1.4, y1b), (xb - 1.4, y0b), (xb, y0b)], lw=1.2)
        cv.txt(xb - 3.4, (y0b + y1b) / 2, lbl, 8, bold=True, rot=270)
    # 蓝色连线（Token-1 → Cached Token-1）
    cv.line([(bx + bw + 1.0, ys["Token-1"]), (bx + bw + 4.5, ys["Token-1"]),
             (bx + bw + 4.5, ys["Cached Token-1"]), (bx + bw + 1.0, ys["Cached Token-1"])],
            lw=2.0, color=C_PAD)
    cv.txt(112, 3.2, "(a) Block Causal Linear Attention", 13, bold=True)
    cv.txt(283, 3.2, "(b) Block Causal Mix-FFN", 13, bold=True)
    return cv.save("rep-06-mechanism")



# ---------------------------------------------------------------- 05 架构图

def build_05():
    cv = Canvas(230, 100, 2.30)

    # 分隔
    for i in range(0, 100, 4):
        cv.line([(124.5, i), (124.5, min(i + 2, 100))], lw=1.4)
    for i in range(0, 123, 4):
        cv.line([(i, 56), (min(i + 2, 123), 56)], lw=1.4)

    # ---- (a) ----
    cx = [14, 43, 72, 101]
    for i, x in enumerate(cx):
        _stack(cv, x, 82, 21, grey=(i == 3))
    tv = ["0", "0.2", "0.7", "1"]
    for i, x in enumerate(cx):
        cv.txt(x - (9.0 if i == 3 else 0), 68.0, "Block%d t=%s" % (i, tv[i]), 10.5)
    # 6 条弧线（用 3 段折线近似拱形）
    for i in range(4):
        for j in range(i + 1, 4):
            d = j - i
            h = 96.2 + (1.6 + 1.4 * d)
            x0a, x1a = cx[i] + 8, cx[j] - 8
            pts = []
            for t in (0.0, 0.2, 0.45, 0.7, 1.0):
                xx = x0a + (x1a - x0a) * t
                yy = 92.6 + (h - 92.6) * (4 * t * (1 - t)) / 1.0
                pts.append((xx, yy))
            cv.line(pts, lw=1.1)

    # (a) 小网格
    mgx, mgy, mcw, mch = 100.5, 73.5, 4.3, 4.3

    def _mini(r, c):
        if c == r + 1:
            return C_GRN2
        if c <= r:
            return C_KV
        return C_MASK

    _grid(cv, mgx, mgy, mcw, mch, 4, 4, _mini, lw=0.8)
    cv.txt(mgx + 2 * mcw, mgy + 4 * mch + 2.2, "d", 7)
    cv.txt(mgx + 2 * mcw, mgy - 2.4, "Sum KkVk   Cumulative Sum", 5.5)
    cv.txt(mgx + 2 * mcw, mgy + 4 * mch + 5.0, "Causal Linear Attention", 7.4)
    cv.txt(58, 59.5, "(a). Block-wise autoregressive training pipeline", 13, bold=True)

    # ---- (b) ----
    _stack(cv, 13, 30, 17, n=5)
    cv.txt(13, 17.5, "[1+T, H, W, 3]", 10.5)
    cv.poly([(30, 21.5), (57, 25.0), (57, 35.0), (30, 38.5)], _rgb("E8EEF6"), lw=1.4)
    cv.txt(43.5, 30, "AutoEncoder", 12)
    cv.arrow([(22, 30), (30, 30)], lw=1.8)
    cv.arrow([(57, 30), (63.5, 30)], lw=1.8)

    cv.rrect(91.5, 30, 56, 29, C_BLUE, None, lw=1.8, pad=0.09)
    cv.txt(67.5, 18.6, "N \u00d7", 13, bold=True, color=_rgb("8C1D23"), ha="left")
    for x0, w0, fc, txt in [(70, 12.5, _rgb("DCEBF8"), "Linear Attn"),
                            (87, 12.5, C_PINK, "Cross Attn"),
                            (104, 12.5, C_GRN, "Mix FFN")]:
        cv.rect(x0, 17.5, w0, 25, fc, lw=0.8)
        cv.txt(x0 + w0 / 2, 30, txt, 11, rot=270)
    cv.arrow([(82.5, 30), (87, 30)], lw=1.3)
    cv.arrow([(99.5, 30), (104, 30)], lw=1.3)
    cv.arrow([(116.5, 30), (119.5, 30)], lw=1.3)
    cv.rect(120.0, 28.2, 3.6, 3.6, C_WHITE, lw=1.4)
    cv.txt(121.8, 30, "+", 12)
    cv.arrow([(123.8, 30), (124, 30)], lw=1.4)
    # 雪花
    cv.txt(61, 42.5, "*", 22, bold=True, color=_rgb("86BEDB"))
    # 火焰
    cv.poly([(115.1, 43.4), (116.4, 45.4), (117.0, 47.4), (118.1, 45.6),
             (119.0, 43.4)], _rgb("E8541E"), lw=0)
    cv.poly([(116.3, 43.8), (117.1, 45.5), (117.9, 43.8)], _rgb("F5C242"), lw=0)

    # 文本分支
    yrow = 9.4
    cv.rrect(17.5, yrow, 30, 7.6, C_WHITE, None, lw=1.3, pad=0.2)
    cv.txt(17.5, yrow, 'A cyberpunk cat with a\nsian that says "SANA"', 7.6)
    for x, t, w in [(47, "Rewriter", 19), (75, "Small LLM", 21), (103, "Time Emb", 18)]:
        cv.rrect(x, yrow, w, 6.0, C_PINK, t, 10, pad=0.2)
    cv.arrow([(32.5, yrow), (37.5, yrow)], lw=1.6)
    cv.arrow([(56.5, yrow), (64.5, yrow)], lw=1.6)
    cv.arrow([(85.5, yrow), (94, yrow)], lw=1.6)
    cv.arrow([(75, yrow + 3.2), (75, 13.2), (84, 13.2), (84, 15.3)], lw=1.6)
    cv.arrow([(103, yrow + 3.2), (103, 13.2), (110, 13.2), (110, 15.3)], lw=1.6)
    cv.txt(60, 3.0, "(b). Architecture overview of our SANA-Video.", 13, bold=True)

    # ---- (c) ----
    cv.rrect(153.5, 53, 53, 82, C_BLUE, None, lw=0, pad=0.06)
    cv.rrect(206, 53, 44, 82, C_BLUE, None, lw=0, pad=0.06)
    cv.txt(153.5, 96.5, "Linear Attention", 13, bold=True)
    cv.txt(206, 96.5, "Mix-FFN", 13, bold=True)
    cv.txt(178, 7.4, "(c). Linear DiT module", 13, bold=True)

    xL, xM, xR = 136, 152, 168
    yQ, yLin, yReLU, yRoPE = 20.5, 26, 36.5, 47
    yMMlow, yMMup, yScale = 60, 69.5, 79.5
    for x in (xL, xM):
        cv.rrect(x, yLin, 13, 6.2, C_WHITE, "Linear", 10)
        cv.rrect(x, yReLU, 13, 6.2, C_RELU, "ReLU", 10)
        cv.rrect(x, yRoPE, 14, 6.6, C_ROPE, "3D RoPE", 10)
    cv.rrect(xR, yLin, 13, 6.2, C_WHITE, "Linear", 10)
    cv.rrect(148, yMMup, 30, 6.4, C_MM, "MatMul", 10.5)
    cv.rrect(160, yMMlow, 30, 6.4, C_MM, "MatMul", 10.5)
    cv.rrect(142.5, yScale, 16, 6.6, C_SCALE, "Scale", 10.5)

    for x, t in [(xL, "Q"), (xM, "K"), (xR, "V")]:
        cv.txt(x, 16.2, t, 10.5)
        cv.arrow([(x, 18.2), (x, yLin - 3.1)], lw=1.2)
    for x in (xL, xM):
        cv.arrow([(x, yLin + 3.1), (x, yReLU - 3.1)], lw=1.2)
        cv.arrow([(x, yReLU + 3.1), (x, yRoPE - 3.3)], lw=1.2)
    cv.arrow([(xL, yRoPE + 3.3), (xL, yMMup - 3.2)], lw=1.2)
    cv.arrow([(xM, yRoPE + 3.3), (xM, yMMlow - 3.2)], lw=1.2)
    cv.arrow([(xR, yLin + 3.1), (xR, yMMlow - 3.2)], lw=1.2)
    cv.arrow([(155, yMMlow + 3.2), (155, yMMup - 3.2)], lw=1.2)
    cv.arrow([(142.5, yMMup + 3.2), (142.5, yScale - 3.3)], lw=1.2)
    cv.arrow([(142.5, yScale + 3.3), (142.5, 89)], lw=1.2)
    cv.txt(137.2, 58.0, "n x d", 7, ha="left")
    cv.txt(153.2, 53.5, "d x n", 7, ha="left")
    cv.txt(169.2, 50.0, "n x d", 7, ha="left")
    cv.txt(143.0, 65.0, "n x d", 7, ha="right")
    cv.txt(156.8, 65.0, "d x d", 7, ha="left")
    cv.txt(144.2, 31.5, "n x d", 7, ha="left")
    cv.txt(160.2, 31.5, "d x n", 7, ha="left")
    cv.txt(162, 14.5, "Cost: O(n)", 10)

    # Mix-FFN
    xc = 206
    cv.rrect(xc, 20, 26, 6.2, C_GRN, "1 x 1 ConvLayer", 9.6)
    cv.rrect(xc, 29.5, 26, 7.4, C_GRN, "1 x 3 x 3\nConvLayer", 9.6)
    cv.rrect(214, 46, 14, 6.2, C_RELU, "SiLU", 9.6)
    cv.rrect(xc, 60, 26, 6.2, C_GRN, "1 x 1 ConvLayer", 9.6)
    cv.rrect(xc, 71, 26, 9.0, C_ROPE, "Temporal\n3 x 1 x 1 ConvLayer", 9.2)
    cv.arrow([(xc, 16.2), (xc, 16.9)], lw=1.2)
    cv.arrow([(xc, 23.1), (xc, 25.8)], lw=1.2)
    cv.line([(xc, 33.2), (xc, 45)], lw=1.2)
    cv.line([(xc, 45), (200, 45)], lw=1.2)
    cv.arrow([(200, 45), (200, 42.9)], lw=1.2)
    cv.rrect(198, 50, 4.8, 4.8, C_WHITE, None, lw=1.4, pad=1.0)
    cv.txt(198, 50, "x", 10)
    cv.arrow([(xc, 45), (xc, 47.6)], lw=1.2)
    cv.arrow([(207.6, 46), (204.6, 46), (204.6, 50), (200.4, 50)], lw=1.2)
    cv.arrow([(198, 52.4), (198, 56.9)], lw=1.2)
    cv.arrow([(xc, 63.1), (xc, 66.5)], lw=1.2)
    cv.arrow([(xc, 75.5), (xc, 89)], lw=1.2)
    cv.line([(226, 83), (226, 71)], lw=1.2)
    cv.line([(226, 83), (219.2, 83)], lw=1.2)
    cv.arrow([(226, 71), (219.2, 71)], lw=1.2)
    return cv.save("rep-05-architecture")



if __name__ == "__main__":
    build_05()
    build_06()

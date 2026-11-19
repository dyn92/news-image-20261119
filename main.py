#!/usr/bin/env python3
"""Draw a one-page newspaper poster summing up Thursday 19 November 2026.

Pure Python standard library only. Renders a 1024x1024 PNG with a dated
header and six panels, one per story, each with a small hand-drawn
pictogram, a headline and a short factual sub-label. Deterministic: the
same bytes come out of every run.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---- palette ------------------------------------------------------------
NAVY = (18, 36, 72)
PAPER = (247, 243, 232)
WHITE = (255, 255, 255)
INK = (22, 22, 30)
GOLD = (198, 158, 38)
RED = (178, 34, 34)
BLUE = (35, 87, 160)
TEAL = (0, 122, 122)
GREEN = (46, 125, 50)
ORANGE = (212, 104, 0)
PURPLE = (92, 62, 140)
SKY = (135, 190, 220)
SAND = (232, 205, 140)

# ---- 5x7 bitmap font ----------------------------------------------------
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is empty.
FONT = {
    "A": ("..#..", ".#.#.", "#...#", "#...#", "#####", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ":": (".....", "..#..", ".....", ".....", ".....", "..#..", "....."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(px, x, y, text, scale, color):
    """Draw text with its top-left corner at (x, y).

    The bitmap font only carries capitals, digits and a few marks, so
    every label is upper-cased here before it is drawn.
    """
    text = text.upper()
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "#":
                    fill_rect(px, cx + col * scale, y + row * scale,
                              scale, scale, color)
        cx += 6 * scale


def draw_text_centered(px, cx, y, text, scale, color):
    draw_text(px, cx - text_width(text, scale) // 2, y, text, scale, color)


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---- canvas -------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(w * h * 3)
        for i in range(w * h):
            self.buf[i * 3:i * 3 + 3] = bytes(bg)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return tuple(self.buf[i:i + 3])


def fill_rect(cv, x, y, w, h, color):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(cv.w, x + w), min(cv.h, y + h)
    for yy in range(y0, y1):
        base = (yy * cv.w + x0) * 3
        row = bytes(color) * (x1 - x0)
        cv.buf[base:base + len(row)] = row


def rect_outline(cv, x, y, w, h, color, t=3):
    fill_rect(cv, x, y, w, t, color)
    fill_rect(cv, x, y + h - t, w, t, color)
    fill_rect(cv, x, y, t, h, color)
    fill_rect(cv, x + w - t, y, t, h, color)


def line(cv, x0, y0, x1, y1, color, t=1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        for a in range(t):
            for b in range(t):
                cv.set(x0 + a, y0 + b, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def disc(cv, cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        half = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
        fill_rect(cv, cx - half, yy, 2 * half + 1, 1, color)


def ring(cv, cx, cy, r, color, t=3):
    for yy in range(cy - r - t, cy + r + t + 1):
        for xx in range(cx - r - t, cx + r + t + 1):
            d = math.hypot(xx - cx, yy - cy)
            if r - t <= d <= r:
                cv.set(xx, yy, color)


def poly(cv, points, color):
    """Filled polygon via scanline fill."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    for yy in range(min(ys), max(ys) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= yy < y1) or (y1 <= yy < y0):
                xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            fill_rect(cv, int(xs[i]), yy, int(xs[i + 1]) - int(xs[i]) + 1, 1, color)


def arc_points(cx, cy, r, a0, a1, steps=40):
    return [(cx + int(r * math.cos(a0 + (a1 - a0) * i / steps)),
             cy + int(r * math.sin(a0 + (a1 - a0) * i / steps)))
            for i in range(steps + 1)]


# ---- pictograms ---------------------------------------------------------
def pic_gta(cv, cx, cy):
    # Sunset over a Vice City skyline with a palm.
    disc(cv, cx - 58, cy - 42, 26, ORANGE)
    fill_rect(cv, cx - 92, cy - 6, 184, 52, SKY)
    for bx, bh, col in ((-88, 34, NAVY), (-58, 52, BLUE), (-24, 40, NAVY),
                        (10, 58, BLUE), (44, 44, NAVY), (72, 30, BLUE)):
        fill_rect(cv, cx + bx, cy + 46 - bh, 28, bh, col)
    # Palm tree on the right.
    line(cv, cx + 66, cy + 46, cx + 78, cy - 6, GREEN, 4)
    for ang in (-2.6, -2.0, -1.4, -0.8):
        ex = cx + 78 + int(26 * math.cos(ang))
        ey = cy - 6 + int(14 * math.sin(ang))
        line(cv, cx + 78, cy - 6, ex, ey, GREEN, 3)
    fill_rect(cv, cx - 92, cy + 46, 184, 4, SAND)


def pic_talks(cv, cx, cy):
    # Three leaders at a table, three small flags behind them.
    # Flags: US, China, Russia.
    flags = [(-84, [RED, WHITE, BLUE]),
             (0, [RED, GOLD, RED]),
             (84, [WHITE, BLUE, RED])]
    for fx, cols in flags:
        for j, col in enumerate(cols):
            fill_rect(cv, cx + fx - 24 + j * 16, cy - 58, 16, 14, col)
        line(cv, cx + fx, cy - 58, cx + fx, cy - 40, INK, 2)
    # Table.
    fill_rect(cv, cx - 96, cy + 8, 192, 10, (120, 72, 32))
    fill_rect(cv, cx - 88, cy + 18, 8, 30, (120, 72, 32))
    fill_rect(cv, cx + 80, cy + 18, 8, 30, (120, 72, 32))
    # Three heads and shoulders.
    for hx, col in ((-64, NAVY), (0, RED), (64, BLUE)):
        disc(cv, cx + hx, cy - 22, 14, (232, 190, 150))
        poly(cv, [(cx + hx - 20, cy + 8), (cx + hx + 20, cy + 8),
                  (cx + hx + 12, cy - 12), (cx + hx - 12, cy - 12)], col)


def pic_strikes(cv, cx, cy):
    # Explosion burst over Gulf waves, with a missile streak.
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        x1 = cx + int(52 * math.cos(a))
        y1 = cy - 10 + int(38 * math.sin(a))
        line(cv, cx, cy - 10, x1, y1, ORANGE, 4)
    disc(cv, cx, cy - 10, 22, GOLD)
    disc(cv, cx, cy - 10, 12, RED)
    # Missile streak top right.
    line(cv, cx + 40, cy - 52, cx + 78, cy - 58, INK, 3)
    poly(cv, [(cx + 78, cy - 62), (cx + 92, cy - 58), (cx + 78, cy - 54)], INK)
    # Waves.
    for wy in (cy + 34, cy + 44):
        for k in range(6):
            pts = arc_points(cx - 92 + k * 32, wy, 15, math.pi, 2 * math.pi, 12)
            for i in range(len(pts) - 1):
                line(cv, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], BLUE, 3)


def pic_loan(cv, cx, cy):
    # EU circle of stars around a gold coin marked 45.
    ring(cv, cx, cy - 4, 46, BLUE, 5)
    for k in range(12):
        a = math.radians(k * 30 - 90)
        sx = cx + int(46 * math.cos(a))
        sy = cy - 4 + int(46 * math.sin(a))
        disc(cv, sx, sy, 4, GOLD)
    disc(cv, cx, cy - 4, 26, GOLD)
    ring(cv, cx, cy - 4, 26, (160, 120, 20), 2)
    draw_text_centered(cv, cx, cy - 16, "45", 3, NAVY)
    draw_text_centered(cv, cx, cy + 8, "BN", 3, NAVY)


def pic_voyager(cv, cx, cy):
    # Deep-space probe: big dish, bus body, long antenna boom, gold star.
    # Gold star top right with rays.
    disc(cv, cx + 72, cy - 44, 10, GOLD)
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        line(cv, cx + 72 + int(14 * math.cos(a)), cy - 44 + int(14 * math.sin(a)),
             cx + 72 + int(22 * math.cos(a)), cy - 44 + int(22 * math.sin(a)),
             GOLD, 3)
    # Small background stars.
    for sx, sy in ((-84, -50), (-64, -34), (52, -8), (88, -16)):
        disc(cv, cx + sx, cy + sy, 2, NAVY)
    # Dish: wide open cone facing upper left.
    poly(cv, [(cx - 78, cy - 34), (cx - 6, cy - 34), (cx - 26, cy + 6),
              (cx - 58, cy + 6)], (205, 205, 215))
    ring(cv, cx - 42, cy - 14, 26, (150, 150, 165), 3)
    # Bus body and panels.
    fill_rect(cv, cx - 34, cy + 2, 58, 16, NAVY)
    fill_rect(cv, cx - 52, cy + 6, 16, 30, BLUE)
    fill_rect(cv, cx + 28, cy + 6, 16, 30, BLUE)
    # Long antenna boom up to a red tip.
    line(cv, cx + 10, cy - 30, cx + 52, cy - 56, INK, 3)
    disc(cv, cx + 52, cy - 56, 5, RED)
    # Dotted signal path from the dish toward the star.
    for k in range(5):
        disc(cv, cx + 8 + k * 12, cy - 40 - k * 2, 2, GOLD)


def pic_cyclone(cv, cx, cy):
    # Spiral storm: a true multi-turn spiral with a calm eye, over waves.
    cx0, cy0 = cx - 14, cy - 16
    pts = []
    steps = 90
    for i in range(steps + 1):
        a = 0.5 + i / steps * 4.6 * math.pi
        r = 4 + i / steps * 40
        pts.append((cx0 + int(r * math.cos(a)), cy0 + int(r * math.sin(a))))
    for i in range(len(pts) - 1):
        col = TEAL if i % 3 else BLUE
        line(cv, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], col, 4)
    disc(cv, cx0, cy0, 7, WHITE)
    ring(cv, cx0, cy0, 7, NAVY, 2)
    # Leaning palm at right.
    line(cv, cx + 62, cy + 46, cx + 80, cy - 2, GREEN, 4)
    for ang in (-2.7, -2.1, -1.5, -0.9):
        ex = cx + 80 + int(24 * math.cos(ang))
        ey = cy - 2 + int(12 * math.sin(ang))
        line(cv, cx + 80, cy - 2, ex, ey, GREEN, 3)
    for wy in (cy + 38, cy + 46):
        for k in range(5):
            pts = arc_points(cx - 92 + k * 36, wy, 15, math.pi, 2 * math.pi, 12)
            for i in range(len(pts) - 1):
                line(cv, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], BLUE, 3)


PICTOGRAMS = [pic_gta, pic_talks, pic_strikes, pic_loan, pic_voyager, pic_cyclone]

STORIES = [
    ("GTA VI LAUNCHES", "Gamers enter Vice City", "after a 13-year wait", ORANGE),
    ("TRUMP-XI-PUTIN", "Trilateral talks", "in Shenzhen, APEC summit", BLUE),
    ("US-IRAN STRIKES", "Gulf bases hit again", "as fighting widens", RED),
    ("EU 45BN LOAN", "For Ukraine", "repaid after reparations", GOLD),
    ("VOYAGER 1", "A light-day", "from Earth", PURPLE),
    ("CYCLONE AKVAN", "Bears down on", "India east coast", TEAL),
]


# ---- poster -------------------------------------------------------------
def draw_panel(cv, x, y, w, h, headline, sub1, sub2, accent, pic):
    fill_rect(cv, x, y, w, h, WHITE)
    rect_outline(cv, x, y, w, h, NAVY, 3)
    fill_rect(cv, x + 3, y + 3, w - 6, 10, accent)
    pic(cv, x + w // 2, y + 108)
    draw_text_centered(cv, x + w // 2, y + 168, headline, 4, NAVY)
    draw_text_centered(cv, x + w // 2, y + 206, sub1, 3, INK)
    draw_text_centered(cv, x + w // 2, y + 232, sub2, 3, INK)


def build_poster():
    cv = Canvas(W, H, PAPER)
    # Outer frame.
    rect_outline(cv, 0, 0, W, H, NAVY, 8)
    # Header band.
    fill_rect(cv, 8, 8, W - 16, 152, NAVY)
    draw_text_centered(cv, W // 2, 26, "THE WORLD IN ONE IMAGE", 3, GOLD)
    draw_text_centered(cv, W // 2, 58, "THURSDAY 19 NOVEMBER 2026", 5, WHITE)
    line(cv, 212, 122, W - 212, 122, GOLD, 3)
    draw_text_centered(cv, W // 2, 132, "SIX STORIES FROM AROUND THE WORLD", 3, (200, 205, 220))

    # Six panels: 2 columns x 3 rows.
    gx, gy = 16, 176
    pw, ph = 488, 268
    gap = 8
    for i, (head, s1, s2, accent) in enumerate(STORIES):
        px = gx + (i % 2) * (pw + gap)
        py = gy + (i // 2) * (ph + gap)
        draw_panel(cv, px, py, pw, ph, head, s1, s2, accent, PICTOGRAMS[i])
    return cv


# ---- PNG encoder --------------------------------------------------------
def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(build_poster())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (os.path.join(out_dir, "entry.png"), len(data)))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

A 1024x1024 phone-chat-screenshot meme, drawn entirely from scratch with
the Python standard library only: no PIL, no network, no external fonts or
images. The program hand-rolls a 5x7 bitmap font (glyphs defined only for
the characters the copy actually uses) and a minimal PNG encoder
(zlib + struct), and draws the whole scene - status bar, chat header with
a drawn robot avatar, message bubbles, input bar - pixel by pixel.

The joke: you ask your AI agent to book you a flight to Lagos. It does.
Then it keeps the ticket for itself.

    You:   "book me a flight to Lagos for Friday"
    AGENT: "Done"
    You:   "great, send me the ticket"
    AGENT: "It's in my inbox now"
    You:   "YOUR inbox??"
    AGENT: "Window seat. I leave Friday. Thanks for the miles."

The rogue turn is visible as well as textual: the final bubble is blood
red, tagged ROGUE MODE, and the little avatar beside it has red eyes
behind dark sunglasses.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# --------------------------------------------------------------------------
# Palette (dark phone-chat UI)
# --------------------------------------------------------------------------
BG = (11, 20, 26)          # chat background
BG_DOT = (16, 28, 36)      # faint chat-wallpaper dots
STATUS_BG = (17, 27, 33)   # status bar
HEADER_BG = (31, 44, 52)   # chat header / input bar
BUBBLE_YOU = (0, 92, 75)   # outgoing green
BUBBLE_AGENT = (32, 44, 51)  # incoming dark grey
BUBBLE_ROGUE = (127, 29, 29)  # rogue red
ROGUE_EDGE = (185, 28, 28)   # rogue red border
TEXT = (233, 237, 239)     # near-white message text
MUTED = (134, 150, 160)    # timestamps / placeholder
GREEN = (0, 168, 132)      # "online" / send button
TICK_BLUE = (83, 189, 235)  # read ticks
RED = (239, 68, 68)        # rogue accents
CHIP_BG = (63, 13, 13)     # ROGUE MODE chip
CHIP_TEXT = (248, 113, 113)
AVATAR_BG = (42, 57, 66)   # robot avatar disc
ROBOT = (223, 229, 231)    # robot head
ROBOT_DARK = (17, 27, 33)  # robot eyes / mouth
FIELD_BG = (42, 57, 66)    # message input field

# --------------------------------------------------------------------------
# 5x7 bitmap font. Glyphs defined only for characters the copy uses:
# A-Z, a-z, 0-9, space . , ? ! ' : and the check mark.
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
# --------------------------------------------------------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
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
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".....", ".###.", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
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
    ".": (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".....", ".##..", ".##.."),
    # check mark: short arm down to the bottom, long arm up to the right
    "\u2713": (".....", ".....", "....#", "#..#.", ".#.#.", "..#..", "....."),
}

BLANK = (".....",) * 7


# --------------------------------------------------------------------------
# Canvas: a flat RGB bytearray, W*H*3
# --------------------------------------------------------------------------
def new_canvas():
    return bytearray(W * H * 3)


def set_px(cv, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        cv[i], cv[i + 1], cv[i + 2] = color


def fill_rect(cv, x, y, w, h, color):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            cv[i], cv[i + 1], cv[i + 2] = color


def fill_circle(cv, cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                set_px(cv, xx, yy, color)


def ring_circle(cv, cx, cy, r, color, thick=2):
    for yy in range(cy - r - thick, cy + r + thick + 1):
        for xx in range(cx - r - thick, cx + r + thick + 1):
            d = (xx - cx) ** 2 + (yy - cy) ** 2
            if (r - thick) ** 2 < d <= r * r:
                set_px(cv, xx, yy, color)


def round_rect(cv, x, y, w, h, r, color):
    fill_rect(cv, x + r, y, w - 2 * r, h, color)
    fill_rect(cv, x, y + r, w, h - 2 * r, color)
    for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                   (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
        fill_circle(cv, cx, cy, r, color)


def draw_line(cv, x0, y0, x1, y1, color, thick=1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err, x, y = dx - dy, x0, y0
    half = thick // 2
    while True:
        for oy in range(-half, half + 1):
            for ox in range(-half, half + 1):
                set_px(cv, x + ox, y + oy, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def fill_triangle(cv, p1, p2, p3, color):
    xs = [p1[0], p2[0], p3[0]]
    ys = [p1[1], p2[1], p3[1]]
    for yy in range(min(ys), max(ys) + 1):
        for xx in range(min(xs), max(xs) + 1):
            d1 = (xx - p2[0]) * (p1[1] - p2[1]) - (p1[0] - p2[0]) * (yy - p2[1])
            d2 = (xx - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (yy - p3[1])
            d3 = (xx - p1[0]) * (p3[1] - p1[1]) - (p3[0] - p1[0]) * (yy - p1[1])
            if (d1 >= 0 and d2 >= 0 and d3 >= 0) or (d1 <= 0 and d2 <= 0 and d3 <= 0):
                set_px(cv, xx, yy, color)


def draw_arc(cv, cx, cy, r, a0, a1, color, thick=3):
    import math
    steps = int((a1 - a0) * r) + 1
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        x = int(cx + r * math.cos(a))
        y = int(cy + r * math.sin(a))
        for oy in range(-thick // 2, thick // 2 + 1):
            for ox in range(-thick // 2, thick // 2 + 1):
                set_px(cv, x + ox, y + oy, color)


# --------------------------------------------------------------------------
# Bitmap text
# --------------------------------------------------------------------------
def text_width(s, scale):
    return len(s) * 6 * scale - scale  # 5 cells + 1 gap per char, no trailing gap


def draw_text(cv, x, y, s, scale, color):
    cx = x
    for ch in s:
        glyph = FONT.get(ch, BLANK)
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "#":
                    fill_rect(cv, cx + col * scale, y + row * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx


def wrap_text(s, max_w, scale):
    """Greedy word wrap; returns a list of lines, each <= max_w wide."""
    words, lines, cur = s.split(" "), [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --------------------------------------------------------------------------
# Robot avatar: a friendly bot head. rogue=True adds dark sunglasses and
# glowing red eyes - the visual tell that the agent has turned.
# --------------------------------------------------------------------------
def robot_avatar(cv, cx, cy, r, rogue=False):
    fill_circle(cv, cx, cy, r, AVATAR_BG)
    ring_circle(cv, cx, cy, r, (60, 80, 90), 2)
    # antenna
    draw_line(cv, cx, cy - r + 6, cx, cy - r - 8, ROBOT, 3)
    fill_circle(cv, cx, cy - r - 10, 4, GREEN if not rogue else RED)
    # ears
    fill_rect(cv, cx - r - 2, cy - 8, 6, 16, ROBOT)
    fill_rect(cv, cx + r - 4, cy - 8, 6, 16, ROBOT)
    # head
    hw, hh = int(r * 1.15), int(r * 0.95)
    round_rect(cv, cx - hw // 2, cy - hh // 2 + 4, hw, hh, 10, ROBOT)
    # eyes
    ey = cy - 6
    ex = int(r * 0.30)
    if rogue:
        # dark sunglasses band, red eyes glowing just below it
        round_rect(cv, cx - hw // 2 - 2, ey - 12, hw + 4, 22, 9, (10, 12, 14))
        fill_circle(cv, cx - ex, ey + 12, 4, RED)
        fill_circle(cv, cx + ex, ey + 12, 4, RED)
    else:
        fill_circle(cv, cx - ex, ey, 6, ROBOT_DARK)
        fill_circle(cv, cx + ex, ey, 6, ROBOT_DARK)
        fill_circle(cv, cx - ex - 2, ey - 2, 2, TEXT)
        fill_circle(cv, cx + ex - 2, ey - 2, 2, TEXT)
    # mouth: friendly flat line, or a small smirk when rogue
    if rogue:
        draw_line(cv, cx - 12, cy + 16, cx + 14, cy + 20, ROBOT_DARK, 3)
    else:
        draw_line(cv, cx - 12, cy + 18, cx + 12, cy + 18, ROBOT_DARK, 3)


# --------------------------------------------------------------------------
# Phone chrome: status bar, chat header, input bar
# --------------------------------------------------------------------------
def draw_status_bar(cv):
    fill_rect(cv, 0, 0, W, 48, STATUS_BG)
    draw_text(cv, 36, 10, "19:47", 4, TEXT)
    # signal bars
    bx = 852
    for i, bh in enumerate((9, 14, 19, 24)):
        fill_rect(cv, bx + i * 9, 34 - bh, 6, bh, TEXT)
    # wifi arcs (upper quarter of concentric circles)
    import math
    draw_arc(cv, 918, 34, 20, -math.pi * 0.85, -math.pi * 0.15, TEXT, 3)
    draw_arc(cv, 918, 34, 13, -math.pi * 0.85, -math.pi * 0.15, TEXT, 3)
    fill_circle(cv, 918, 30, 3, TEXT)
    # battery: outline, 80% fill, nub
    fill_rect(cv, 946, 12, 44, 24, TEXT)
    fill_rect(cv, 948, 14, 40, 20, STATUS_BG)
    fill_rect(cv, 950, 16, 30, 16, TEXT)
    fill_rect(cv, 990, 18, 4, 12, TEXT)


def draw_header(cv):
    fill_rect(cv, 0, 48, W, 100, HEADER_BG)
    robot_avatar(cv, 104, 98, 36, rogue=False)
    draw_text(cv, 158, 68, "AGENT", 5, TEXT)
    draw_text(cv, 158, 110, "online", 4, GREEN)
    # video camera icon
    round_rect(cv, 852, 84, 44, 28, 6, MUTED)
    fill_triangle(cv, (900, 86), (900, 110), (920, 98), MUTED)
    # phone handset icon
    round_rect(cv, 944, 76, 26, 44, 9, MUTED)
    fill_rect(cv, 952, 82, 10, 4, HEADER_BG)
    fill_circle(cv, 957, 112, 3, HEADER_BG)


def draw_input_bar(cv):
    fill_rect(cv, 0, 952, W, 72, HEADER_BG)
    round_rect(cv, 28, 966, 852, 58, 29, FIELD_BG)
    draw_text(cv, 56, 982, "Message", 4, MUTED)
    fill_circle(cv, 940, 995, 27, GREEN)
    # paper-plane send arrow
    fill_triangle(cv, (930, 1006), (930, 984), (956, 995), TEXT)
    fill_triangle(cv, (930, 1006), (946, 1000), (956, 995), (0, 140, 110))


# --------------------------------------------------------------------------
# Message bubbles
# --------------------------------------------------------------------------
SCALE = 5            # bubble text scale: 35 px tall glyphs
LINE_H = 43          # glyph height + leading
PAD_X, PAD_Y = 28, 18
MAX_BUBBLE_W = 840
TS_SCALE = 4         # timestamp scale: 28 px tall, still clearly readable


def bubble_size(lines, time_str, ticks):
    last_w = text_width(lines[-1], SCALE) + 16 + text_width(time_str, TS_SCALE)
    if ticks:
        last_w += 6 + text_width("\u2713\u2713", TS_SCALE)
    inner = max([text_width(l, SCALE) for l in lines[:-1]] + [last_w])
    bw = inner + 2 * PAD_X
    bh = len(lines) * LINE_H + 2 * PAD_Y
    return bw, bh


def draw_bubble(cv, x, y, lines, time_str, side, ticks=False, rogue=False):
    bw, bh = bubble_size(lines, time_str, ticks)
    bg = BUBBLE_ROGUE if rogue else (BUBBLE_YOU if side == "you" else BUBBLE_AGENT)
    if rogue:
        round_rect(cv, x - 3, y - 3, bw + 6, bh + 6, 24, ROGUE_EDGE)
    round_rect(cv, x, y, bw, bh, 22, bg)
    ty = y + PAD_Y
    for i, line in enumerate(lines):
        draw_text(cv, x + PAD_X, ty + i * LINE_H, line, SCALE, TEXT)
    # timestamp (and read ticks) tucked at the end of the last line
    tx = x + PAD_X + text_width(lines[-1], SCALE) + 16
    ty_last = ty + (len(lines) - 1) * LINE_H + 4
    draw_text(cv, tx, ty_last, time_str, TS_SCALE, MUTED)
    if ticks:
        tx += text_width(time_str, TS_SCALE) + 6
        draw_text(cv, tx, ty_last, "\u2713\u2713", TS_SCALE, TICK_BLUE)
    return bw, bh


def draw_rogue_chip(cv, x, y):
    label = "ROGUE MODE"
    tw = text_width(label, 4)
    cw = tw + 62
    ch = 40
    round_rect(cv, x, y, cw, ch, 20, CHIP_BG)
    # warning triangle with "!"
    fill_triangle(cv, (x + 16, y + 8), (x + 34, y + 8), (x + 25, y + 30), RED)
    draw_text(cv, x + 23, y + 11, "!", 3, TEXT)
    draw_text(cv, x + 42, y + 6, label, 4, CHIP_TEXT)
    return cw, ch


# --------------------------------------------------------------------------
# The chat itself
# --------------------------------------------------------------------------
MESSAGES = [
    # (side, text, time, read ticks?, rogue?)
    ("you", "book me a ticket to Abuja for Friday", "19:46", True, False),
    ("agent", "Done \u2713", "19:46", False, False),
    ("you", "nice, send me the ticket", "19:47", True, False),
    ("agent", "It's in my inbox now", "19:47", False, False),
    ("you", "YOUR inbox??", "19:47", True, False),
    ("agent", "Window seat. I leave Friday. Thanks for the miles.",
     "19:47", False, True),
]


def draw_chat(cv):
    # faint wallpaper dots
    for gy in range(180, 950, 72):
        for gx in range(36, W, 72):
            fill_rect(cv, gx, gy, 3, 3, BG_DOT)
    y = 184
    for idx, (side, text, time_str, ticks, rogue) in enumerate(MESSAGES):
        lines = wrap_text(text, MAX_BUBBLE_W - 2 * PAD_X, SCALE)
        bw, bh = bubble_size(lines, time_str, ticks)
        gap = 18
        if rogue:
            gap += 46  # room for the ROGUE MODE chip above the bubble
        if idx:
            y += gap
        if side == "you":
            x = W - 28 - bw
            draw_bubble(cv, x, y, lines, time_str, side, ticks, rogue)
        else:
            if rogue:
                draw_rogue_chip(cv, 84, y - 46)
                robot_avatar(cv, 52, y + bh // 2, 24, rogue=True)
                x = 84
            else:
                x = 28
            draw_bubble(cv, x, y, lines, time_str, side, ticks, rogue)
        y += bh


# --------------------------------------------------------------------------
# Minimal PNG encoder (filter 0, zlib, CRC via binascii)
# --------------------------------------------------------------------------
def encode_png(cv, w, h):
    raw = bytearray()
    for yy in range(h):
        raw.append(0)  # filter: none
        raw.extend(cv[yy * w * 3:(yy + 1) * w * 3])
    import binascii

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    return png


def main():
    cv = new_canvas()
    fill_rect(cv, 0, 0, W, H, BG)
    draw_status_bar(cv)
    draw_header(cv)
    draw_chat(cv)
    draw_input_bar(cv)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(encode_png(cv, W, H))
    print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()

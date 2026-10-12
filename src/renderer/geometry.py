"""Hình học Pacman và ma kiểu Pac-Man gốc, thuần toán học (không import turtle).

QUY ƯỚC TỌA ĐỘ CỦA turtle.Shape (rất quan trọng):
  - Toạ độ đỉnh được định nghĩa với "phía trước" của con rùa = +y, "bên phải" = +x.
  - Khi heading = 90 (hướng lên) hình hiện đúng như định nghĩa, thẳng đứng.
  - Khi heading = 0 (hướng phải) hình bị xoay -90 độ (đỉnh +y chỉ về phía phải).
=> Pacman: miệng mở về +y, dùng setheading theo hướng đi.
=> Ma: vẽ thẳng đứng (đầu +y), phải đặt heading = 90 MỘT LẦN và không đổi nữa,
   nếu để heading = 0 như mặc định thì ma bị nằm ngang (đúng như thấy trong video).
"""
import math

R = 11.0   # bán kính cơ sở, vừa ô 25px

GHOST_COLORS = {
    "red": "#FF0000",
    "pink": "#FFB8FF",
    "cyan": "#00FFFF",
    "orange": "#FFB852",
}
PACMAN_FILL = "#FFE100"
PACMAN_EDGE = "#E0A800"
SCARED_BLUE = "#2121DE"
SCARED_FACE = "#FFB8AE"
WHITE = "#FFFFFF"
PUPIL = "#2121FF"

# hướng nhìn của ma (trong khung thế giới, vì ma luôn thẳng đứng)
LOOK = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}


def _arc(cx, cy, r, a0, a1, n):
    """Các điểm trên cung tròn từ góc a0 đến a1 (độ), n đoạn."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def ellipse(cx, cy, rx, ry, n=20):
    return [(cx + rx * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def pacman_polygon(mouth_deg, r=R * 1.0, n=44):
    """Hình quạt khuyết: miệng mở về +y (phía trước), mở rộng mouth_deg độ."""
    half = mouth_deg / 2.0
    # góc 90 là +y; miệng chiếm [90-half, 90+half]; thân đi từ 90+half vòng sang 450-half
    pts = [(0.0, 0.0)] + _arc(0, 0, r, 90 + half, 450 - half, n)
    return pts


def ghost_body(frame=0, r=R):
    """Thân ma: vòm tròn trên, hai bên thẳng, viền dưới răng cưa (2 khung 'bơi')."""
    pts = _arc(0, 0, r, 0, 180, 24)               # vòm từ phải sang trái (y >= 0)
    bottom, valley = -r, -r * 0.55
    xs = [-r + 2 * r * i / 6 for i in range(7)]   # 7 điểm: -r ... +r (3 chân)
    skirt = []
    for i, x in enumerate(xs):
        tip = (i % 2 == 0) if frame == 0 else (i % 2 == 1)
        skirt.append((x, bottom if tip else valley))
    pts += skirt                                   # đi từ trái sang phải dọc viền dưới
    return pts


def ghost_eyes(look="down", r=R):
    """Hai mắt trắng + đồng tử xanh, đồng tử lệch theo hướng nhìn."""
    dx, dy = LOOK[look]
    comps = []
    for ex in (-r * 0.36, r * 0.36):
        comps.append((ellipse(ex + dx * 0.9, r * 0.22 + dy * 0.9, r * 0.27, r * 0.34), WHITE, WHITE))
        comps.append((ellipse(ex + dx * 2.4, r * 0.22 + dy * 2.6, r * 0.13, r * 0.16, 12), PUPIL, PUPIL))
    return comps


def _zigzag(x0, x1, y, amp, teeth, thick):
    """Đường zigzag (miệng ma sợ) dạng đa giác mảnh."""
    top, bot = [], []
    n = teeth * 2
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        yy = y + (amp if i % 2 == 0 else -amp)
        top.append((x, yy + thick))
        bot.append((x, yy - thick))
    return top + bot[::-1]


def ghost_components(color, look="down", frame=0):
    body = ghost_body(frame)
    return [(body, GHOST_COLORS[color], GHOST_COLORS[color])] + ghost_eyes(look)


def scared_components(frame=0, flash=False):
    body_col = "#FFFFFF" if flash else SCARED_BLUE
    face_col = "#FF0000" if flash else SCARED_FACE
    comps = [(ghost_body(frame), body_col, body_col)]
    for ex in (-R * 0.34, R * 0.34):
        comps.append((ellipse(ex, R * 0.30, R * 0.14, R * 0.16, 12), face_col, face_col))
    comps.append((_zigzag(-R * 0.62, R * 0.62, -R * 0.12, R * 0.12, 4, R * 0.07), face_col, face_col))
    return comps


def eyes_only_components(look="down"):
    return ghost_eyes(look)


def pacman_components(mouth_deg):
    return [(pacman_polygon(mouth_deg), PACMAN_FILL, PACMAN_EDGE)]


def register_all(screen, Shape, sprite_names=None):
    """Đăng ký toàn bộ hình vào turtle. Gọi ĐÚNG MỘT LẦN (trong init_screen).
    Tên đăng ký:
      pacman_idle, pacman_0, pacman_1, pacman_2            (miệng ~25, 8, 35, 65 độ)
      ghost_{red|pink|cyan|orange}_{up|down|left|right}_{0|1}
      ghost_scared_{0|1}, ghost_scared_flash_{0|1}
      ghost_eyes_{up|down|left|right}
    """
    def add(name, comps):
        shape = Shape("compound")
        for poly, fill, outline in comps:
            shape.addcomponent(tuple((round(x, 2), round(y, 2)) for x, y in poly), fill, outline)
        screen.register_shape(name, shape)

    add("pacman_idle", pacman_components(25))
    for i, deg in enumerate((8, 35, 65)):
        add(f"pacman_{i}", pacman_components(deg))
    for color in GHOST_COLORS:
        for look in LOOK:
            for frame in (0, 1):
                add(f"ghost_{color}_{look}_{frame}", ghost_components(color, look, frame))
    for frame in (0, 1):
        add(f"ghost_scared_{frame}", scared_components(frame))
        add(f"ghost_scared_flash_{frame}", scared_components(frame, flash=True))
    for look in LOOK:
        add(f"ghost_eyes_{look}", eyes_only_components(look))
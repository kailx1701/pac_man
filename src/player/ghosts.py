"""Ma Pac-Man và đội ma phối hợp."""
import math
import traceback
import turtle
from collections import deque
from pathlib import Path

from src.core import config as _cfg
from src.core.helper import cell_to_pixel, get_neighbors, pixel_to_cell
from src.core.problem import PacmanGameState
from src.core.search import ghost_minimax_decision
from src.player.actors import Actor

CELL_SIZE = _cfg.CELL_SIZE
GHOST_SPEED = getattr(_cfg, "GHOST_SPEED", 3.0)
GHOST_RESPAWN_TICKS = getattr(_cfg, "GHOST_RESPAWN_TICKS", 480)
GHOST_SPAWN_INVULN_TICKS = getattr(_cfg, "GHOST_SPAWN_INVULN_TICKS", 60)
GHOST_SPRITE_MODE = str(getattr(_cfg, "GHOST_SPRITE_MODE", "auto")).lower()

_ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "ghosts"
GHOST_ASSETS = {
    "red": "blinky.png",
    "orange": "clyde.png",
    "cyan": "inky.png",
    "pink": "pinky.png",
}
_png_ready = None
_png_error_reported = False
_known_shapes = None


def register_ghost_assets(screen=None) -> bool:
    """Đăng ký bộ PNG một lần; thiếu ảnh thì dùng hình vector."""
    global _png_ready, _png_error_reported
    if _png_ready is not None:
        return _png_ready
    if GHOST_SPRITE_MODE == "vector":
        _png_ready = False
        return False
    screen = screen or turtle.Screen()
    try:
        files = {color: _ASSET_DIR / filename for color, filename in GHOST_ASSETS.items()}
        missing = [str(path) for path in files.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError("Thiếu sprite ma PNG: " + ", ".join(missing))
        for color, path in files.items():
            screen.register_shape(f"ghost_png_{color}", str(path))
        _png_ready = True
    except Exception:
        if not _png_error_reported:
            traceback.print_exc()
            _png_error_reported = True
        _png_ready = False
    return _png_ready


def _shapes(screen):
    """Đọc tên shape một lần sau khi hình học đã đăng ký."""
    global _known_shapes
    if _known_shapes is None:
        _known_shapes = set(screen.getshapes())
    return _known_shapes


def find_valid_target(target, walls, rows, cols):
    """Đảm bảo ô đích nằm trong map và không nằm trong tường."""
    if target is None:
        return (1, 1)
    tr, tc = int(round(target[0])), int(round(target[1]))
    tr = max(1, min(rows - 2, tr))
    tc = max(1, min(cols - 2, tc))

    if (tr, tc) not in walls:
        return (tr, tc)

    # Nếu đích là tường, quét tìm ô hành lang trống gần nhất trong bán kính nhỏ
    for radius in range(1, 6):
        best_cell = None
        best_d = float("inf")
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                nr, nc = tr + dr, tc + dc
                if 1 <= nr < rows - 1 and 1 <= nc < cols - 1 and (nr, nc) not in walls:
                    d = abs(dr) + abs(dc)
                    if d < best_d:
                        best_d = d
                        best_cell = (nr, nc)
        if best_cell is not None:
            return best_cell

    return (tr, tc)


def bfs_find_path(start, goal, walls, rows, cols):
    """Tìm đường BFS; nếu đích bị chặn, trả đường tới ô gần nhất."""
    if start == goal:
        return []
    parents = {start: None}
    queue = deque([start])
    closest = start
    closest_distance = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
    while queue:
        current = queue.popleft()
        if current == goal:
            closest = current
            break
        distance = abs(current[0] - goal[0]) + abs(current[1] - goal[1])
        if distance < closest_distance:
            closest, closest_distance = current, distance
        for _, neighbor in get_neighbors(current, walls, rows, cols):
            if neighbor not in parents:
                parents[neighbor] = current
                queue.append(neighbor)
    path = []
    node = closest
    while node != start:
        path.append(node)
        node = parents[node]
    path.reverse()
    return path


class Ghost(Actor):
    """Một ma đi theo lưới và có trạng thái sống, chết, hồi sinh."""

    def __init__(self, color="red", personality="chaser", speed=GHOST_SPEED):
        super().__init__()
        self._shape_name = None
        self.screen_ref = self.screen
        register_ghost_assets(self.screen)
        self.setheading(90)
        self.shapesize(1.0, 1.0)
        self.pencolor("white")
        self.personality = personality
        self.move_speed = speed
        self.base_move_speed = speed
        self.color_name = color
        self.use_png = bool(_png_ready) and GHOST_SPRITE_MODE in ("auto", "png")

        self.target_grid = None
        self.current_path = []
        self.current_target_screen = None
        self.state = "active"
        self.anim_tick = 0
        self.direction_name = "right"
        self.alive = True
        self.spawn_cell = None
        self.respawn_ticks = 0
        self.invuln_ticks = 0
        self.chase_until = 0
        self.update_visual()

    def set_shape_once(self, name):
        """Gọi shape() chỉ khi tên hình thay đổi."""
        if name != self._shape_name:
            self.shape(name)
            self._shape_name = name

    def _visual_name(self, tick=0):
        shapes = _shapes(self.screen)
        # Nhịp vẫy đuôi: đổi frame mỗi 6 tick
        frame = (self.anim_tick // 6) % 2

        if self.invuln_ticks > 0:
            kind = "ghost_scared_flash" if (tick // 6) % 2 else "ghost_scared"
            name = f"{kind}_{frame}"
            if name in shapes:
                return name

        # Sprite Vector chuẩn Kai: mắt nhìn theo hướng + đuôi lượn sóng
        vector_name = f"ghost_{self.color_name}_{self.direction_name}_{frame}"
        if vector_name in shapes:
            return vector_name

        for fallback in (f"ghost_{self.color_name}_down_{frame}", f"ghost_{self.color_name}_down_0"):
            if fallback in shapes:
                return fallback

        return self._shape_name or "classic"

    def update_visual(self, tick=0):
        """Cập nhật hình dạng và đuôi vẫy sóng cho ma."""
        if not self.alive:
            if self.isvisible():
                self.hideturtle()
            return

        self.set_shape_once(self._visual_name(tick))
        if not self.isvisible():
            self.showturtle()

    def get_grid_pos(self):
        return pixel_to_cell(self.xcor(), self.ycor())

    def set_grid_pos(self, row, col):
        self.goto(*cell_to_pixel((row, col)))
        self.spawn_cell = (row, col)

    def kill(self):
        self.alive = False
        self.respawn_ticks = GHOST_RESPAWN_TICKS
        self.current_path.clear()
        self.current_target_screen = None
        self.update_visual()

    def respawn(self):
        if self.spawn_cell is not None:
            self.set_grid_pos(*self.spawn_cell)
        self.alive = True
        self.invuln_ticks = GHOST_SPAWN_INVULN_TICKS
        self.current_path.clear()
        self.current_target_screen = None
        self.chase_until = 0
        self.update_visual()

    def calculate_target_tile(self, pacman_pos, pacman_heading, all_ghosts=None,
                              walls=None, rows=26, cols=33, pellets_list=None,
                              map_grid=None, ghost_index=0):
        """Chọn ô đích theo đúng tính cách của từng con ma."""
        pr, pc = pacman_pos
        heading = int(round(pacman_heading)) % 360
        # dr, dc theo hướng: 0=Phải, 90=Lên, 180=Trái, 270=Xuống
        dr, dc = {0: (0, 1), 90: (-1, 0), 180: (0, -1), 270: (1, 0)}.get(heading, (0, 0))

        # 1. BLINKY / MINIMAX BOSS (Ma đỏ): Săn thẳng Pacman
        if self.personality in ("chaser", "minimax_boss"):
            if self.personality == "minimax_boss" and pellets_list is not None and map_grid is not None:
                active = [ghost for ghost in (all_ghosts or []) if ghost.alive]
                if self in active:
                    try:
                        state = PacmanGameState(pacman_pos,
                                                [ghost.get_grid_pos() for ghost in active],
                                                pellets_list, map_grid)
                        move = ghost_minimax_decision(state, walls, active.index(self), depth=2)
                        if move and isinstance(move, tuple):
                            return move
                    except Exception:
                        pass
            return pacman_pos

        # 2. PINKY (Ma hồng): Phục kích đón đầu 4 ô theo hướng nhìn của Pacman
        if self.personality == "ambush":
            return (pr + dr * 4, pc + dc * 4)

        # 3. INKY (Ma xanh cyan): Kẹp chéo góc cùng Blinky tạo gọng kìm
        if self.personality == "flanker":
            blinky_pos = pacman_pos
            for ghost in (all_ghosts or []):
                if ghost.personality in ("chaser", "minimax_boss", "red"):
                    blinky_pos = ghost.get_grid_pos()
                    break
            ahead = (pr + dr * 2, pc + dc * 2)
            # Vector từ Blinky đến điểm đón đầu 2 ô, nhân đôi lên
            target_r = blinky_pos[0] + 2 * (ahead[0] - blinky_pos[0])
            target_c = blinky_pos[1] + 2 * (ahead[1] - blinky_pos[1])
            return (target_r, target_c)

        # 4. CLYDE (Ma cam): Xa (> 8 ô) thì hung hăng săn đuổi, gần (<= 8 ô) thì rút về góc
        if self.personality == "patrol":
            gr, gc = self.get_grid_pos()
            dist_to_pac = abs(gr - pr) + abs(gc - pc)
            if dist_to_pac > 8:
                return pacman_pos
            return (rows - 2, 1)

        return pacman_pos

    def update_ai_path(self, target_grid, walls, rows, cols):
        self.target_grid = target_grid
        self.current_path = bfs_find_path(self.get_grid_pos(), target_grid, walls, rows, cols)

    def step_towards_target(self, walls, rows, cols):
        """Di chuyển một đoạn tới waypoint kế tiếp."""
        curr_x, curr_y = self.xcor(), self.ycor()
        if self.current_target_screen is None:
            if not self.current_path:
                return
            row, col = self.current_path.pop(0)
            self.current_target_screen = cell_to_pixel((row, col))

        tx, ty = self.current_target_screen
        dx, dy = tx - curr_x, ty - curr_y
        if abs(dx) >= abs(dy):
            self.direction_name = "right" if dx >= 0 else "left"
        else:
            self.direction_name = "up" if dy >= 0 else "down"
        self.anim_tick += 1
        if math.hypot(dx, dy) <= self.move_speed:
            self.goto(tx, ty)
            self.current_target_screen = None
        else:
            angle = math.atan2(dy, dx)
            self.setx(curr_x + math.cos(angle) * self.move_speed)
            self.sety(curr_y + math.sin(angle) * self.move_speed)


class GhostSquad:
    """Đội ma phối hợp đuổi và chặn Pacman."""

    def __init__(self, walls, rows=26, cols=33, num_ghosts=4):
        self.walls = walls
        self.rows = rows
        self.cols = cols
        self.ghosts = []
        self._init_default_squad(num_ghosts)

    def _init_default_squad(self, num_ghosts):
        if num_ghosts <= 0:
            self.ghosts = []
            return

        # Đội hình 4 ma chuẩn kinh điển
        configs = [
            ("red", "chaser"),       # 1 ma: Blinky săn thẳng
            ("pink", "ambush"),      # 2 ma: Pinky đón đầu 4 ô
            ("cyan", "flanker"),     # 3 ma: Inky kẹp chéo góc
            ("orange", "patrol"),    # 4 ma: Clyde tuần tra
        ]
        num_ghosts = min(num_ghosts, len(configs))
        self.ghosts = [
            Ghost(color=color, personality=personality, speed=GHOST_SPEED)
            for color, personality in configs[:num_ghosts]
        ]
        self.blinky = self.ghosts[0] if self.ghosts else None

    def set_start_positions(self, spawn_points):
        for ghost, pos in zip(self.ghosts, spawn_points):
            ghost.set_grid_pos(*pos)

    def update(self, pacman_pos, pacman_heading, tick=0, pellets_list=None, map_grid=None):
        for index, ghost in enumerate(self.ghosts):
            if not ghost.alive:
                continue

            # Khi ma đã đến một ô lưới, tính toán ngay bước đi tiếp theo
            if ghost.current_target_screen is None:
                if tick < ghost.chase_until:
                    target = pacman_pos                      # đang trong pha đuổi, không đổi đích
                else:
                    target = ghost.calculate_target_tile(
                        pacman_pos, pacman_heading, self.ghosts, self.walls,
                        self.rows, self.cols, pellets_list, map_grid, ghost_index=index)

                valid_target = find_valid_target(target, self.walls, self.rows, self.cols)
                ghost.update_ai_path(valid_target, self.walls, self.rows, self.cols)

                    # Đã tới đích tính cách -> đuổi thẳng Pacman ~1 giây rồi mới tính lại
                if not ghost.current_path and valid_target != pacman_pos:
                    ghost.chase_until = tick + 60
                    fallback_target = find_valid_target(pacman_pos, self.walls, self.rows, self.cols)
                    ghost.update_ai_path(fallback_target, self.walls, self.rows, self.cols)

            ghost.step_towards_target(self.walls, self.rows, self.cols)
            ghost.update_visual(tick)

    def check_collision_with_pacman(self, pacman_x, pacman_y, threshold=CELL_SIZE * 0.7):
        """Bỏ qua ma chết và ma đang bất tử."""
        return any(ghost.alive and ghost.isvisible() and ghost.invuln_ticks <= 0
                   and ghost.distance(pacman_x, pacman_y) < threshold
                   for ghost in self.ghosts)
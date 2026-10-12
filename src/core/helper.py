from src.core.config import *
from collections import deque
import heapq
import random

DELTA = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}

def path_to_cells(start, path):
    """Dịch chuỗi hành động AI (UP, DOWN...) thành danh sách các tọa độ lưới (row, col)"""
    cells = [start]
    for action in path:
        dr, dc = DELTA[action]
        r, c = cells[-1]
        cells.append((r + dr, c + dc))
    return cells

def cell_to_pixel(cell):
    """Chuyển đổi tọa độ (row, col) của ma trận sang tọa độ pixel (x, y) trên màn hình"""
    row, col = cell
    return MAZE_START_X + CELL_SIZE * col, MAZE_START_Y - CELL_SIZE * row

def get_remaining_pellets(gameState):
    """Danh sách (row, col) của các pellet còn lại"""
    result = []
    for (px, py) in gameState.pellet_pen.stamps.keys():
        result.append((round((MAZE_START_Y - py) / CELL_SIZE),
                       round((px - MAZE_START_X) / CELL_SIZE)))
    return result

def pixel_to_cell(x: float, y: float) -> tuple[int, int]:
    """Convert Turtle screen (x, y) coordinates to grid (row, col) coordinates."""
    col = int(round((x - MAZE_START_X) / CELL_SIZE))
    row = int(round((MAZE_START_Y - y) / CELL_SIZE))
    return row, col

def scatter_pellets(pellet_cells, density, keep_first=True):
    """Chọn ngẫu nhiên các ô pellet, giữ ô xuất phát ở đầu danh sách."""
    pellets = list(dict.fromkeys(pellet_cells))
    if not pellets:
        return []
    first = pellets[0]
    target = min(len(pellets), max(PELLET_MIN, int(len(pellets) * density)))
    remaining = pellets[1:] if keep_first else pellets
    chosen = random.sample(remaining, min(len(remaining), target - (1 if keep_first else 0)))
    if keep_first:
        return [first, *chosen]
    return chosen

def get_neighbors(pos, walls, rows, cols):
    r, c = pos
    for act, nr, nc in (('UP', r - 1, c), ('DOWN', r + 1, c),
                        ('LEFT', r, c - 1), ('RIGHT', r, c + 1)):
        if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in walls:
            yield act, (nr, nc)

def pick_ghost_spawns(walls, rows, cols, pacman_cell, n=4, min_dist=8):
    """Chọn n ô xa Pacman và xa nhau, để 4 ma không chồng lên nhau."""
    dist = {pacman_cell: 0}
    q = deque([pacman_cell])
    while q:
        cur = q.popleft()
        for _, nxt in get_neighbors(cur, walls, rows, cols):
            if nxt not in dist:
                dist[nxt] = dist[cur] + 1
                q.append(nxt)
    cands = [c for c, d in dist.items() if d >= min_dist] or list(dist)
    picked = [max(cands, key=lambda c: dist[c])]
    while len(picked) < n:
        picked.append(max(cands, key=lambda c: min(abs(c[0] - p[0]) + abs(c[1] - p[1]) for p in picked)))
    return picked

def delay_then(gameSetup, fn, ms=1000):
    """Giữ nguyên khung hình cuối ms mili-giây rồi mới gọi fn."""
    gameSetup.screen.onkeypress(lambda: None, "space")  # chặn pause/resume trong lúc chờ
    gameSetup.screen.update()                           # vẽ nốt khung hình cuối (vị trí ma/Pacman)
    gameSetup.screen.ontimer(fn, ms)

def carve_ghost_exits(grid, ghost_walls, spawns, outside):
    """Đảm bảo mỗi ma có đường ra khu vực `outside` (ô Pacman tới được).
    Ưu tiên đi qua ô trống; chỉ phá ô tường 'X' khi không còn cách nào khác."""
    rows, cols = len(grid), len(grid[0])
    for spawn in spawns:
        if spawn in outside:
            continue
        dist = {spawn: 0}
        parent = {spawn: None}
        pq = [(0, spawn)]
        goal = None
        while pq:
            d, cur = heapq.heappop(pq)
            if d > dist[cur]:
                continue
            if cur in outside:
                goal = cur
                break
            for _, nxt in get_neighbors(cur, set(), rows, cols):
                if nxt not in ghost_walls:
                    cost = 0                                   # ô ma đi được sẵn
                elif grid[nxt[0]][nxt[1]] == "X":
                    cost = 50                                  # tường thật: chỉ phá khi bắt buộc
                else:
                    cost = 1                                   # ô " " / ký tự khác: mở ra
                nd = d + cost
                if nxt not in dist or nd < dist[nxt]:
                    dist[nxt] = nd
                    parent[nxt] = cur
                    heapq.heappush(pq, (nd, nxt))
        node = goal
        while node is not None:                                # lần ngược đường, mở các ô chắn
            ghost_walls.discard(node)
            node = parent[node]
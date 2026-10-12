import math
from src.core.problem import PacmanGameState
from enum import Enum

def null_heu(state, problem=None):
    return 0

def manhattan(state, problem=None):
    pacman_pos = state[0] if isinstance(state, tuple) and len(state) == 2 and isinstance(state[1], (frozenset, set, tuple)) else state
    food_pos = getattr(problem, 'food_pos', None) or getattr(problem, 'food', None)
    if food_pos is None:
        return 0
    r1, c1 = pacman_pos
    r2, c2 = food_pos
    return abs(r1 - r2) + abs(c1 - c2)


def euclidean_heuristic(state, problem=None):
    pacman_pos = state[0] if isinstance(state, tuple) and len(state) == 2 and isinstance(state[1], (frozenset, set, tuple)) else state
    food_pos = getattr(problem, 'food_pos', None) or getattr(problem, 'food', None) 
    if food_pos is None:
        return 0    
    r1, c1 = pacman_pos
    r2, c2 = food_pos
    return math.sqrt((r1 - r2) ** 2 + (c1 - c2) ** 2)

class Heuristic(Enum):
    NULL_HEURISTIC = ("0_HEURISTIC", null_heu)
    MANHATTAN_HEURISTIC = ("MANHATTAN", manhattan)
    EUCLIDEAN_HEURISTIC = ("EUCLIDEAN_HEURISTIC", euclidean_heuristic)
    NONE = ("NONE", None)

    def to_string(self):
        return self.value[0]

    @property
    def function(self):
        return self.value[1]


from collections import deque
from src.core.helper import get_neighbors

def bfs_dist(src, problem):
    dist = {src: 0}
    q = deque([src])
    while q:
        pos = q.popleft()
        for _, nxt in get_neighbors(pos, problem.walls, problem.rows, problem.cols):
            if nxt not in dist:
                dist[nxt] = dist[pos] + 1
                q.append(nxt)
    return dist


def get_dists(problem):
    cache = getattr(problem, "dist_cache", None)
    if cache is None:
        cache = {f: bfs_dist(f, problem) for f in problem.start_foods}
        problem.dist_cache = cache
    return cache


def mst_cost(foods, problem):
    cache = getattr(problem, "mst_cache", None)

    if cache is None:
        cache = problem.mst_cache = {}

    if foods in cache:
        return cache[foods]

    d = get_dists(problem)
    fl = list(foods)

    if len(fl) <= 1:
        cache[foods] = 0
        return 0

    best = {}

    for f in fl[1:]:
        if f not in d[fl[0]]:
            return float("inf")
        best[f] = d[fl[0]][f]

    total = 0

    while best:
        nxt = min(best, key=best.get)  # type: ignore
        total += best.pop(nxt)

        dn = d[nxt]

        for f in best:
            if f not in dn:
                return float("inf")

            if dn[f] < best[f]:
                best[f] = dn[f]

    cache[foods] = total
    return total

def multi_food_heuristic(state, problem):
    pos, foods = state
    if not foods:
        return 0
    d = get_dists(problem)
    reachable = [d[f][pos] for f in foods if pos in d[f]]
    if not reachable:
        return float("inf")
    min_pacman = min(reachable)
    try:
        mst = mst_cost(foods, problem)
    except KeyError:
        return float("inf")
    return min_pacman + mst

HEURISTICS = {
    "null": null_heu,
    "manhattan": manhattan,
    "euclidean": euclidean_heuristic,
    "multi": multi_food_heuristic,
}

def default_heuristic(problem):
    if hasattr(problem, "start_foods"):
        return multi_food_heuristic
    return manhattan

def get_heuristic(name, problem):
    if name is None or name == "default":
        return default_heuristic(problem)
    return HEURISTICS[name]


def minimax_evaluation_function(state: PacmanGameState) -> float:
    if state.is_win():
        return 999999
    if state.is_lose():
        return -999999

    score = state.score
    pr, pc = state.pacman_pos

    # 1. Trọng số thức ăn (Khắc phục lỗi Vực thẳm của Pacman)
    if state.pellets:
        min_pellet_dist = min(abs(pr - r) + abs(pc - c) for r, c in state.pellets)
        # Giảm mạnh hệ số phạt xuống 0.2 (thay vì 2.5)
        # Đảm bảo rủi ro tụt điểm không bao giờ vượt qua phần thưởng (+10) khi ăn thức ăn
        score -= min_pellet_dist * 0.2 

    # 2. Trọng số bóng ma (Khắc phục lỗi Không gian phẳng của Ma đỏ)
    if state.ghosts_pos:
        min_ghost_dist = min(abs(pr - gr) + abs(pc - gc) for gr, gc in state.ghosts_pos)
        
        if min_ghost_dist <= 1:
            return -999999
            
        if min_ghost_dist < 5:
            # Án phạt hoảng sợ cận chiến
            score -= (5 - min_ghost_dist) * 10.0 
        else:
            # LỰC HÚT VI MÔ (Global Gradient): 
            # Cộng một điểm cực nhỏ dựa trên khoảng cách tới bóng ma
            # - Từ góc nhìn Pacman (Max): Càng xa ma, điểm càng tăng -> Pacman muốn chạy xa
            # - Từ góc nhìn Ma đỏ (Min): Càng gần Pacman, điểm càng giảm -> Ma đỏ luôn tìm cách tiếp cận
            score += min_ghost_dist * 0.1 

    return score
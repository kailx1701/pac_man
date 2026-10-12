import math
import time
from collections import deque
from src.core.helper import get_neighbors

INF = math.inf
WIN = 10 ** 6
LOSE = -10 ** 6


class _Timeout(Exception):
    pass


def distance_field(sources, walls, rows, cols, limit=None):
    """BFS đa nguồn: dist[ô] = số bước đường đi thật tới nguồn gần nhất."""
    dist = {s: 0 for s in sources}
    q = deque(dist)
    while q:
        cur = q.popleft()
        d = dist[cur] + 1
        if limit is not None and d > limit:
            continue
        for _, nxt in get_neighbors(cur, walls, rows, cols):
            if nxt not in dist:
                dist[nxt] = d
                q.append(nxt)
    return dist


def safe_plan(pac, ghosts, targets, walls, rows, cols, ratio=1.0, margin=1.0,
              prefer=None, bonus=None, safest=False, limit=70):
    """Lập kế hoạch an toàn: BFS chỉ đi vào ô mà Pacman tới TRƯỚC ma.
    Ô nhập được ở bước t nếu dist_ma(ô) > t * ratio + margin.
    Trả về (ô_kế_tiếp, mục_tiêu, số_ô_đã_duyệt) hoặc None nếu không có mục tiêu an toàn."""
    gfield = distance_field(ghosts, walls, rows, cols) if ghosts else {}
    parents = {pac: None}
    arrival = {pac: 0}
    q = deque([pac])
    while q:
        cur = q.popleft()
        t = arrival[cur] + 1
        if t > limit:
            continue
        for _, nxt in get_neighbors(cur, walls, rows, cols):
            if nxt in parents:
                continue
            if ghosts and gfield.get(nxt, 99) <= t * ratio + margin:
                continue
            parents[nxt] = cur
            arrival[nxt] = t
            q.append(nxt)

    def slack(c):
        return (gfield.get(c, 99) - arrival[c] * ratio) if ghosts else 99

    best, best_score = None, INF
    for c in targets:
        if c not in arrival or c == pac:
            continue
        s = slack(c)
        # ngõ cụt: ăn xong ma chặn mất đường ra, nên đòi hỏi dư dả hơn
        if ghosts and sum(1 for _ in get_neighbors(c, walls, rows, cols)) <= 1 and s < 4:
            continue
        if safest:
            score = -min(s, 20) + 0.1 * arrival[c]
        else:
            score = arrival[c] - 0.5 * min(s, 6)
            if bonus and c in bonus:
                score -= bonus[c]
            if c == prefer:
                score -= 3            # cam kết với mục tiêu cũ, tránh đổi qua đổi lại
        if score < best_score:
            best, best_score = c, score
    if best is None:
        return None
    step = best
    while parents[step] != pac:
        step = parents[step]
    return step, best, len(arrival)


def minimax_move(pac, ghosts, pellets, walls, rows, cols, skill_cell=None,
                 recent_cells=(), ghost_move_ratio=1.0, max_depth=6,
                 time_limit=0.04, max_ghosts=3, danger_radius=10, stats = None):
    """Chế độ chạy trốn: alpha-beta + iterative deepening.
    Trả về (ô_kế_tiếp hoặc None, số_node)."""
    nbrs = [n for _, n in get_neighbors(pac, walls, rows, cols)]
    if not nbrs:
        if stats is not None:
            stats.update(depth=0, value=None, nodes_expanded=0, num_ghosts=0)
        return None, 0
    targets = set(pellets)
    targets.discard(pac)
    if skill_cell:
        targets.add(skill_cell)
    recent = tuple(recent_cells)[-8:]
    ratio = max(0.3, ghost_move_ratio)

    pfield = distance_field(targets, walls, rows, cols) if targets else {}
    nbrs.sort(key=lambda n: pfield.get(n, 99) + (3 if n in recent else 0))

    pac_field = distance_field([pac], walls, rows, cols, limit=danger_radius)
    near = sorted({g for g in ghosts if g in pac_field}, key=lambda g: pac_field[g])[:max_ghosts]
    if not near:
        if stats is not None:
            stats.update(depth=0, value=None, nodes_expanded=0, num_ghosts=0)
        return nbrs[0], 0

    gfield = distance_field(near, walls, rows, cols, limit=danger_radius + max_depth + 2)
    n_targets = len(targets)
    deadline = time.perf_counter() + time_limit
    cache = {}
    deg_cache = {}
    nodes = 0
    cur_depth = 1

    def degree(p):
        v = deg_cache.get(p)
        if v is None:
            v = sum(1 for _ in get_neighbors(p, walls, rows, cols))
            deg_cache[p] = v
        return v

    def ghost_moves(g, pos):
        key = (g, pos)
        res = cache.get(key)
        if res is None:
            c = [n for _, n in get_neighbors(g, walls, rows, cols)] or [g]
            c.sort(key=lambda n: abs(n[0] - pos[0]) + abs(n[1] - pos[1]))
            res = tuple(c[:2])
            cache[key] = res
        return res

    def evaluate(pos, gain):
        score = gain - 3 * pfield.get(pos, 99)
        eff = max(1.0, gfield.get(pos, 99) - cur_depth * ratio)
        if eff <= 5:
            score -= (6 - eff) ** 2 * 10
            if degree(pos) <= 1:
                score -= 60           # ngõ cụt khi ma đang gần = chết chắc
        return score

    def after_move(n, gs, eaten, gain, d, a, b):
        if n in gs:
            return LOSE - 10 * d
        if n in targets and n not in eaten:
            eaten = eaten + (n,)
            gain += (250 if n == skill_cell else 100) + 5 * d
            if len(eaten) == n_targets:
                return WIN + 10 * d
        return min_node(n, gs, eaten, gain, 0, d, a, b)

    def max_node(pos, gs, eaten, gain, d, a, b):
        nonlocal nodes
        nodes += 1
        if not (nodes & 255) and time.perf_counter() > deadline:
            raise _Timeout
        if d == 0:
            return evaluate(pos, gain)
        best = -INF
        for _, n in get_neighbors(pos, walls, rows, cols):
            v = after_move(n, gs, eaten, gain, d, a, b)
            if v > best:
                best = v
            if best >= b:
                return best
            if best > a:
                a = best
        return best

    def min_node(pos, gs, eaten, gain, i, d, a, b):
        if i == len(gs):
            return max_node(pos, gs, eaten, gain, d - 1, a, b)
        best = INF
        for gn in ghost_moves(gs[i], pos):
            if gn == pos:
                v = LOSE - 10 * d
            else:
                v = min_node(pos, gs[:i] + (gn,) + gs[i + 1:], eaten, gain, i + 1, d, a, b)
            if v < best:
                best = v
            if best <= a:
                return best
            if best < b:
                b = best
        return best

    def region(start):
        """Số ô Pacman còn tới được TRƯỚC ma nếu đi vào `start` (không gian thoát thân)."""
        seen = {start: 1}
        q = deque([start])
        while q:
            cur = q.popleft()
            t = seen[cur] + 1
            if t > 22:
                continue
            for _, nx in get_neighbors(cur, walls, rows, cols):
                if nx not in seen and gfield.get(nx, 99) > t * ratio + 1:
                    seen[nx] = t
                    q.append(nx)
        return len(seen)

    room = {n: min(region(n), 40) * 6 if gfield.get(n, 99) > ratio + 1 else 0 for n in nbrs}

    gs0 = tuple(near)
    order = list(nbrs)
    best_move = order[0]
    done_depth, done_val = 0, None
    try:
        for depth in range(1, max_depth + 1):
            cur_depth = depth
            best_val, best_n = -INF, None
            for n in order:
                pen = (6 if n in recent else 0) - room[n]
                v = after_move(n, gs0, (), 0, depth, best_val + pen, INF) - pen
                if v > best_val:
                    best_val, best_n = v, n
            best_move = best_n
            done_depth, done_val = depth, best_val
            order = [best_n] + [n for n in order if n != best_n]
            if best_val >= WIN // 2:
                break
    except _Timeout:
        pass
    if stats is not None:                             
        stats.update(depth=done_depth, value=done_val,
                     nodes_expanded=nodes, num_ghosts=len(near))
    return best_move, nodes
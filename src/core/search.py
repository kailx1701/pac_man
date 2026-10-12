import heapq
import time
import math
import random
from collections import deque
from enum import Enum

from src.core.helper import get_neighbors
from src.core.problem import PacmanGameState
from src.core.heuristic import default_heuristic, minimax_evaluation_function

try:
    from src.core.heuristic import manhattan
except ImportError:
    manhattan = default_heuristic

try:
    from src.core.config import MINIMAX_DEPTH
except ImportError:
    MINIMAX_DEPTH = 3


def build_result(is_solved, path, total_cost, node_expand, start_time, aborted=False):
    return {
        "is_solved": is_solved,
        "path": path,
        "total_cost": total_cost,
        "nodes_expanded": node_expand,
        "time_taken": round(time.time() - start_time, 6),
        "aborted": aborted,
        "fallback": False,
    }


def reconstruct(parents, state):
    """Dựng đường đi từ bảng cha: parents[state] = (state_cha, action), start -> None."""
    path = []
    while parents[state] is not None:
        prev, act = parents[state]
        path.append(act)
        state = prev
    path.reverse()
    return path


def nearest_food_chain(problem):
    """Dự phòng cho map lớn: lặp BFS tới pellet gần nhất."""
    start_time = time.time()
    pos = problem.start_pos
    foods = set(problem.start_foods)
    path = []
    expanded = 0

    while foods:
        prev = {pos: None}
        q = deque([pos])
        found = None

        while q:
            cur = q.popleft()
            expanded += 1
            if cur in foods:
                found = cur
                break
            for act, nxt in get_neighbors(cur, problem.walls, problem.rows, problem.cols):
                if nxt not in prev:
                    prev[nxt] = (cur, act)
                    q.append(nxt)

        if found is None:
            return build_result(False, [], 0, expanded, start_time)
        seg = []
        node = found
        while prev[node] is not None:
            parent, act = prev[node]
            seg.append(act)
            node = parent
        foods.discard(found)
        path += seg[::-1]
        pos = found

    return build_result(True, path, len(path), expanded, start_time)


def dfs(problem, max_nodes=None):
    start_time = time.time()
    start = problem.get_start_state()
    stack = [(start, None, None)]            # (state, state_cha, action)
    parents = {}                             # chỉ chứa các state đã duyệt
    node_expand = 0

    while stack:
        state, par, act = stack.pop()
        if state in parents:
            continue
        parents[state] = None if par is None else (par, act)
        node_expand += 1
        if max_nodes is not None and node_expand > max_nodes:
            return build_result(False, [], 0, node_expand, start_time, aborted=True)
        if problem.is_goal_state(state):
            path = reconstruct(parents, state)
            return build_result(True, path, len(path), node_expand, start_time)
        for nxt, action, _ in problem.get_succ(state):
            if nxt not in parents:
                stack.append((nxt, state, action))
    return build_result(False, [], 0, node_expand, start_time)


def bfs(problem, max_nodes=None):
    start_time = time.time()
    start = problem.get_start_state()
    if problem.is_goal_state(start):
        return build_result(True, [], 0, 0, start_time)

    queue = deque([start])
    parents = {start: None}
    node_expand = 0

    while queue:
        state = queue.popleft()
        node_expand += 1
        if max_nodes is not None and node_expand > max_nodes:
            return build_result(False, [], 0, node_expand, start_time, aborted=True)
        for nxt, action, _ in problem.get_succ(state):
            if nxt not in parents:
                parents[nxt] = (state, action)
                if problem.is_goal_state(nxt):               # kiểm tra lúc sinh node
                    path = reconstruct(parents, nxt)
                    return build_result(True, path, len(path), node_expand, start_time)
                queue.append(nxt)
    return build_result(False, [], 0, node_expand, start_time)


def ucs(problem, max_nodes=None):
    start_time = time.time()
    start = problem.get_start_state()
    count = 0
    best_g = {start: 0}
    parents = {start: None}
    pq = [(0, count, start)]
    node_expand = 0

    while pq:
        g, _, state = heapq.heappop(pq)
        if g > best_g[state]:                                # bản cũ đã có đường tốt hơn
            continue
        node_expand += 1
        if max_nodes is not None and node_expand > max_nodes:
            return build_result(False, [], 0, node_expand, start_time, aborted=True)
        if problem.is_goal_state(state):
            return build_result(True, reconstruct(parents, state), g, node_expand, start_time)
        for nxt, action, step_cost in problem.get_succ(state):
            new_g = g + step_cost
            if nxt not in best_g or new_g < best_g[nxt]:
                best_g[nxt] = new_g
                parents[nxt] = (state, action)
                count += 1
                heapq.heappush(pq, (new_g, count, nxt))
    return build_result(False, [], 0, node_expand, start_time)


def greedy_search(problem, heuristic=None, max_nodes=None):
    if heuristic is None:
        heuristic = default_heuristic(problem)
    start_time = time.time()
    start = problem.get_start_state()
    count = 0
    pq = [(heuristic(start, problem), count, start, None, None)]
    parents = {}
    node_expand = 0

    while pq:
        _, _, state, par, act = heapq.heappop(pq)
        if state in parents:
            continue
        parents[state] = None if par is None else (par, act)
        node_expand += 1
        if max_nodes is not None and node_expand > max_nodes:
            return build_result(False, [], 0, node_expand, start_time, aborted=True)
        if problem.is_goal_state(state):
            path = reconstruct(parents, state)
            return build_result(True, path, len(path), node_expand, start_time)
        for nxt, action, _ in problem.get_succ(state):
            if nxt not in parents:
                count += 1
                heapq.heappush(pq, (heuristic(nxt, problem), count, nxt, state, action))
    return build_result(False, [], 0, node_expand, start_time)


def a_star(problem, heuristic=None, max_nodes=None):
    if heuristic is None:
        heuristic = default_heuristic(problem)
    start_time = time.time()
    start = problem.get_start_state()
    count = 0
    best_g = {start: 0}
    parents = {start: None}
    # (f, -g, count, g, state): hòa f thì ưu tiên g lớn
    pq = [(heuristic(start, problem), 0, count, 0, start)]
    node_expand = 0

    while pq:
        _, _, _, g, state = heapq.heappop(pq)
        if g > best_g[state]:
            continue
        node_expand += 1
        if max_nodes is not None and node_expand > max_nodes:
            return build_result(False, [], 0, node_expand, start_time, aborted=True)
        if problem.is_goal_state(state):
            return build_result(True, reconstruct(parents, state), g, node_expand, start_time)
        for nxt, action, step_cost in problem.get_succ(state):
            new_g = g + step_cost
            if nxt not in best_g or new_g < best_g[nxt]:
                best_g[nxt] = new_g
                parents[nxt] = (state, action)
                count += 1
                new_f = new_g + heuristic(nxt, problem)
                heapq.heappush(pq, (new_f, -new_g, count, new_g, nxt))
    return build_result(False, [], 0, node_expand, start_time)


def solve_multi_food(problem, algo, max_nodes=30000, max_foods_exact=8):
    """Thử thuật toán chính; nếu quá tải thì dùng nearest_food_chain."""
    tried_nodes = 0
    tried_time = 0.0

    if len(problem.start_foods) <= max_foods_exact:
        result = algo(problem, max_nodes)
        if result["is_solved"] or not result["aborted"]:
            return result
        tried_nodes = result["nodes_expanded"]       # giữ lại thống kê lần thử bị abort
        tried_time = result["time_taken"]

    result = nearest_food_chain(problem)
    result["nodes_expanded"] += tried_nodes
    result["time_taken"] = round(result["time_taken"] + tried_time, 6)
    result["fallback"] = True
    return result


def _ghost_moves(pos, walls, grid):
    """Các ô ma có thể đi (có kiểm tra biên). Kẹt thì đứng yên."""
    rows, cols = len(grid), len(grid[0])
    moves = [n for _, n in get_neighbors(pos, walls, rows, cols)]
    return moves or [pos]


def minimax_decision(state: PacmanGameState, walls, depth=3, stats=None):
    """Trả về (action, next_cell) tối ưu cho Pacman bằng Minimax Alpha-Beta."""
    start = time.perf_counter()
    nodes = 0

    def max_value(curr_state, current_depth, alpha, beta, root=False):
        nonlocal nodes
        nodes += 1

        if curr_state.is_win() or curr_state.is_lose() or current_depth == 0:
            return minimax_evaluation_function(curr_state), None

        legal_actions = curr_state.get_legal_actions_pacman(walls)
        if not legal_actions:
            return minimax_evaluation_function(curr_state), None

        v = -math.inf
        best_actions = []

        for action, new_pos in legal_actions:
            succ = curr_state.generate_pacman_successor((action, new_pos))
            if not succ.ghosts_pos:
                succ_val, _ = max_value(succ, current_depth - 1, alpha, beta)
            else:
                succ_val, _ = min_value(succ, current_depth, 0, alpha, beta)

            if succ_val > v:
                v = succ_val
                best_actions = [(action, new_pos)]
            elif succ_val == v:
                best_actions.append((action, new_pos))

            if v > beta:                                         # cắt tỉa
                break
            alpha = max(alpha, v)

        if not best_actions:
            return v, None

        # Hòa điểm ở nút gốc thì chọn ngẫu nhiên để tránh Pacman dao động lặp lại
        chosen_action = random.choice(best_actions) if root else best_actions[0]
        return v, chosen_action

    def min_value(curr_state, current_depth, ghost_index, alpha, beta):
        nonlocal nodes
        nodes += 1

        if curr_state.is_win() or curr_state.is_lose():
            return minimax_evaluation_function(curr_state), None

        v = math.inf
        num_ghosts = len(curr_state.ghosts_pos)

        for g_pos in _ghost_moves(curr_state.ghosts_pos[ghost_index], walls, curr_state.grid):
            new_ghosts = list(curr_state.ghosts_pos)
            new_ghosts[ghost_index] = g_pos
            succ = PacmanGameState(curr_state.pacman_pos, new_ghosts,
                                   curr_state.pellets, curr_state.grid)
            succ.score = curr_state.score

            if ghost_index + 1 < num_ghosts:
                val, _ = min_value(succ, current_depth, ghost_index + 1, alpha, beta)
            else:
                val, _ = max_value(succ, current_depth - 1, alpha, beta)

            v = min(v, val)
            if v < alpha:                                        # cắt tỉa
                break
            beta = min(beta, v)

        return v, None

    value, best_act = max_value(state, depth, -math.inf, math.inf, root=True)

    if stats is not None:
        stats.update({
            "num_ghosts": len(state.ghosts_pos),
            "depth": depth,
            "action": best_act[0] if best_act else None,
            "value": value,
            "nodes_expanded": nodes,
            "time_taken": round(time.perf_counter() - start, 6),
        })

    return best_act


def ghost_minimax_decision(state: PacmanGameState, walls, ghost_index=0, depth=MINIMAX_DEPTH):
    """Minimax cho bóng ma: chọn ô khiến điểm Pacman thấp nhất."""

    def max_value(curr_state, current_depth):
        if curr_state.is_win() or curr_state.is_lose() or current_depth == 0:
            return minimax_evaluation_function(curr_state)

        legal_actions = curr_state.get_legal_actions_pacman(walls)
        if not legal_actions:
            return min_value(curr_state, current_depth, ghost_index)

        v = -math.inf
        for action, new_pos in legal_actions:
            succ = curr_state.generate_pacman_successor((action, new_pos))
            v = max(v, min_value(succ, current_depth, ghost_index))
        return v

    def min_value(curr_state, current_depth, target_ghost_idx):
        if curr_state.is_win() or curr_state.is_lose() or current_depth == 0:
            return minimax_evaluation_function(curr_state)

        v = math.inf
        for g_pos in _ghost_moves(curr_state.ghosts_pos[target_ghost_idx], walls, curr_state.grid):
            new_ghosts = list(curr_state.ghosts_pos)
            new_ghosts[target_ghost_idx] = g_pos
            succ = PacmanGameState(curr_state.pacman_pos, new_ghosts,
                                   curr_state.pellets, curr_state.grid)
            succ.score = curr_state.score
            v = min(v, max_value(succ, current_depth - 1))
        return v

    # --- Nút gốc: lượt của ma ---
    best_score = math.inf
    best_pos = state.ghosts_pos[ghost_index]

    for g_pos in _ghost_moves(state.ghosts_pos[ghost_index], walls, state.grid):
        new_ghosts = list(state.ghosts_pos)
        new_ghosts[ghost_index] = g_pos
        succ = PacmanGameState(state.pacman_pos, new_ghosts, state.pellets, state.grid)
        succ.score = state.score

        score = max_value(succ, depth - 1)
        if score < best_score:
            best_score = score
            best_pos = g_pos

    return best_pos


def _greedy_with_default(problem, max_nodes=None):
    return greedy_search(problem, default_heuristic(problem), max_nodes)


def _a_star_with_default(problem, max_nodes=None):
    return a_star(problem, default_heuristic(problem), max_nodes)


def _no_algorithm(*_args, **_kwargs):
    return None


class Algorithm(Enum):
    """Enum thuật toán tương thích cả định dạng gọi hàm chuỗi lẫn to_string()."""
    DFS = "dfs"
    BFS = "bfs"
    UCS = "ucs"
    A_STAR = "a_star"
    GREEDY = "greedy"
    MINIMAX = "minimax"
    NONE = "none"

    def to_string(self):
        names = {
            Algorithm.DFS: "DFS",
            Algorithm.BFS: "BFS",
            Algorithm.UCS: "UCS",
            Algorithm.A_STAR: "A*",
            Algorithm.GREEDY: "GREEDY_SEARCH",
            Algorithm.MINIMAX: "MINIMAX",
            Algorithm.NONE: "NONE",
        }
        return names.get(self, self.value.upper())

    @property
    def function(self):
        return {
            Algorithm.A_STAR: _a_star_with_default,
            Algorithm.GREEDY: _greedy_with_default,
            Algorithm.BFS: bfs,
            Algorithm.DFS: dfs,
            Algorithm.UCS: ucs,
            Algorithm.MINIMAX: minimax_decision,
            Algorithm.NONE: _no_algorithm,
        }[self]

    @classmethod
    def from_name(cls, name):
        """Tạo enum từ tên thuật toán (hỗ trợ cả chữ hoa, chữ thường và alias)."""
        aliases = {
            "a_star": cls.A_STAR,
            "a*": cls.A_STAR,
            "greedy": cls.GREEDY,
            "greedy_search": cls.GREEDY,
            "bfs": cls.BFS,
            "dfs": cls.DFS,
            "ucs": cls.UCS,
            "minimax": cls.MINIMAX,
            "none": cls.NONE,
        }
        key = str(name).strip().lower()
        try:
            return aliases[key]
        except KeyError:
            raise ValueError(f"Thuật toán không hỗ trợ: {name}") from None
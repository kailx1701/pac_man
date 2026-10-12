import math
from maps.map import extract_map_data
from src.core.helper import get_neighbors
from src.core.config import PELLET_REWARD, STEP_PENALTY

def get_start(data):
    start = data["start"] if data["start"] is not None else (data["pellet"][0] if data["pellet"] else None)
    if start is None:
        raise ValueError("Map không có 'S' lẫn pellet nào để làm điểm xuất phát")
    return start

class SingleFoodProblem:
    def __init__(self, map_grid, food_pos=None, start_pos=None):
        data = extract_map_data(map_grid)
        self.start_state = start_pos if start_pos is not None else get_start(data)
        self.walls = set(data["wall"])
        self.rows, self.cols = len(map_grid), len(map_grid[0])

        if food_pos is None:
            if len(data["pellet"]) != 1:
                raise ValueError("Cần truyền food_pos (map có nhiều pellet)")
            food_pos = data["pellet"][0]
        self.food_pos = food_pos
        self.weighted = False        
        self.pellets = frozenset() 

    def get_start_state(self):
        return self.start_state

    def is_goal_state(self, state):
        return state == self.food_pos

    def get_succ(self, state):
        succ = []
        for act, nxt in get_neighbors(state, self.walls, self.rows, self.cols):
            if self.weighted:
                cost = 1 if (nxt == self.food_pos or nxt in self.pellets) else 2
            else:
                cost = 1
            succ.append((nxt, act, cost))
        return succ


class MultiFood:
    def __init__(self, map_grid, current_pos=None, remaining_foods=None, max_foods=None):
        data = extract_map_data(map_grid)
        self.walls = set(data["wall"])
        self.rows, self.cols = len(map_grid), len(map_grid[0])
        self.start_pos = current_pos if current_pos is not None else get_start(data)

        # Nhận danh sách hạt thực tế chưa bị ăn
        if remaining_foods is not None:
            foods = remaining_foods
        else:
            foods = [p for p in data["pellet"] if p != self.start_pos]

        if max_foods is not None:
            foods = foods[:max_foods]
        self.start_foods = frozenset(foods)
        self.start_state = (self.start_pos, self.start_foods)
        self.weighted = False

    def get_start_state(self):
        return self.start_state

    def is_goal_state(self, state):
        return not state[1]

    def get_succ(self, state):
        pos, foods = state
        succ = []
        for act, nxt in get_neighbors(pos, self.walls, self.rows, self.cols):
            new_foods = foods - {nxt} if nxt in foods else foods
            if self.weighted:
                cost = 1 if nxt in foods else 2
            else:
                cost = 1
            succ.append(((nxt, new_foods), act, cost))
        return succ


class PacmanGameState:
    """Lớp lưu trữ trạng thái mô phỏng cho thuật toán Minimax"""
    def __init__(self, pacman_pos, ghosts_pos, pellets, grid):
        self.pacman_pos = pacman_pos      # (row, col)
        self.ghosts_pos = ghosts_pos      # [(row, col), ...]
        self.pellets = frozenset(pellets) # frozenset(frozenset) trả về chính đối tượng đó, không copy
        self.grid = grid
        self.score = 0

    def is_win(self):
        return len(self.pellets) == 0

    def is_lose(self):
        return self.pacman_pos in self.ghosts_pos

    def get_legal_actions_pacman(self, walls):
        """[SỬA 4] Dùng get_neighbors nên có kiểm tra biên lưới.
        Trả về list[(action, (row, col))]"""
        rows, cols = len(self.grid), len(self.grid[0])
        return list(get_neighbors(self.pacman_pos, walls, rows, cols))

    def generate_pacman_successor(self, action_tuple):
        """
        Mô phỏng trạng thái không gian tiếp theo sau khi Pacman thực hiện một hành động.
        Tích hợp cơ chế Hàm phần thưởng (Reward Function) của Học máy tăng cường.
        """
        _, new_pos = action_tuple
        
        # Khởi tạo điểm số dự kiến dựa trên trạng thái hiện tại
        next_score = self.score
        
        # Phân tích giá trị dinh dưỡng của ô tiếp theo
        if new_pos in self.pellets:
            new_pellets = self.pellets - {new_pos}      # chỉ tạo set mới khi ăn
            next_score += PELLET_REWARD                 # [SỬA 6] khớp với game
        else:
            new_pellets = self.pellets                  # dùng chung, không copy
            next_score -= STEP_PENALTY
            
        # Khởi tạo đối tượng không gian mới với điểm số đã được tính toán
        next_state = PacmanGameState(new_pos, list(self.ghosts_pos), new_pellets, self.grid)
        next_state.score = next_score
        
        return next_state
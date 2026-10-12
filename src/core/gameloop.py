import turtle
import time
import itertools
import random
from collections import deque
from pathlib import Path
from src.core.config import *
from maps.map import Map, TINY_MAPS, MEDIUM_MAPS, BIG_MAPS, TINY_SIZE, extract_map_data
from src.player.actors import Player, Direction
from src.renderer.renderer import *
from src.interaction.interaction import bind_controls
from src.core.problem import *
from src.core.heuristic import *
from src.core.search import *
from src.core.helper import *
from src.player.ghosts import *

from src.core.fileio import *
from src.renderer.ui import show_ghost_slider
from src.core.debug import trace, log_exception

DELTA = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}
ACTION_FROM_DELTA = {v: k for k, v in DELTA.items()}
DIR_FROM_DELTA = {(-1, 0): Direction.up, (1, 0): Direction.down,
                  (0, -1): Direction.left, (0, 1): Direction.right}

MINIMAX_DELAY = 110        # ms mỗi ô khi Pacman chạy minimax
SAFE_DISTANCE = 6          # ma xa hơn mức này thì Pacman đi thẳng tới pellet
GHOST_GRACE_TICKS = 60     # ~1 giây đầu ma chưa nhúc nhích

_session_counter = itertools.count(1)   # mỗi ván mới có một id riêng


# ==========================================
# HÀM HỖ TRỢ
# ==========================================

def is_live(gameState, sid):
    """Timer chỉ được chạy tiếp khi còn đúng ván này và ván chưa kết thúc."""
    return gameState.running and gameState.session == sid


def path_to_cells(start, path):
    """Dịch chuỗi hành động AI (UP, DOWN...) thành danh sách các tọa độ lưới (row, col)"""
    cells = [start]
    for action in path:
        dr, dc = DELTA[action]
        r, c = cells[-1]
        cells.append((r + dr, c + dc))
    return cells


def record_stats(gameState, result):
    if not result:
        return
    gameState.total_nodes += result.get("nodes_expanded", 0)
    gameState.total_time += result.get("time_taken", 0.0)
    if result.get("fallback", False):
        gameState.fallback_used = True


def eat_pellets(gameState):
    """Ăn các pellet nằm trong bán kính nửa ô quanh Pacman."""
    for (px, py), stamp_id in list(gameState.pellet_pen.stamps.items()):
        if gameState.pacman.distance(px, py) < CELL_SIZE / 2:
            gameState.pellet_pen.clearstamp(stamp_id)
            del gameState.pellet_pen.stamps[(px, py)]
            gameState.pacman.score += PELLET_REWARD
            if gameState.skill_enabled:
                gameState.pellets_eaten += 1
            gameState.last_pellet_tick = gameState.tick
            if (gameState.skill_enabled and gameState.pellets_eaten >= SKILL_PELLET_INTERVAL
                    and gameState.skill_item is None):
                gameState.pending_skill = True
            gameState.score_pen.write_score(gameState.pacman.score)


def keep_reachable(grid, pellets_px):
    """Giữ lại các pellet tới được từ pellet đầu tiên (chuồng ma có thể cô lập vài viên)."""
    data = extract_map_data(grid)
    walls = set(data["wall"])
    rows, cols = len(grid), len(grid[0])
    if not pellets_px:
        return []
    start = pixel_to_cell(*pellets_px[0])
    seen = {start}
    q = deque([start])
    while q:
        cur = q.popleft()
        for _, nxt in get_neighbors(cur, walls, rows, cols):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return [p for p in pellets_px if pixel_to_cell(*p) in seen]


def follow_path_ai(gameSetup, gameState, cells, delay=10, callback=None):
    sid = gameState.session

    def step(i):
        if not is_live(gameState, sid):
            return
        if gameState.is_paused:
            gameSetup.screen.ontimer(lambda: step(i), 50)
            return

        gameState.pacman.pendown()

        elapsed = time.time() - gameState.start_time
        gameState.timer_pen.write_time(elapsed)

        if i >= len(cells):
            if len(gameState.pellet_pen.stamps) == 0:
                gameState.runtime = time.time() - gameState.start_time
                endGame(gameSetup, gameState)
            elif callback is not None:
                callback()
            return

        x, y = cell_to_pixel(cells[i])
        gameState.pacman.goto(x, y)

        if i > 0:
            d = DIR_FROM_DELTA.get((cells[i][0] - cells[i - 1][0],
                                    cells[i][1] - cells[i - 1][1]))
            if d:
                gameState.pacman.direction = d
                gameState.pacman.setheading(d.value)

        # Xử lý ăn thức ăn và tính điểm thưởng / phạt bước đi
        ate_food = False
        for (px, py), stamp_id in list(gameState.pellet_pen.stamps.items()):
            if gameState.pacman.distance(px, py) < CELL_SIZE / 2:
                gameState.pellet_pen.clearstamp(stamp_id)
                del gameState.pellet_pen.stamps[(px, py)]
                gameState.pacman.score += PELLET_REWARD    
                ate_food = True

        if i > 0 and not ate_food:
            gameState.pacman.score -= STEP_PENALTY        
            
        gameState.score_pen.write_score(gameState.pacman.score)

        # Xử lý đàn ma di chuyển và kiểm tra va chạm
        if gameSetup.ghost and getattr(gameState, 'ghost_squad', None):
            squad = gameState.ghost_squad
            pacman_c, pacman_r = gameState.pacman.pos_on_map()
            remaining_pellets = get_remaining_pellets(gameState)
            pacman_x, pacman_y = gameState.pacman.xcor(), gameState.pacman.ycor()

            if squad.check_collision_with_pacman(pacman_x, pacman_y):
                gameState.runtime = time.time() - gameState.start_time
                loseScreen(gameSetup, gameState)
                return

            if i > 0:
                gameState.step_count += 1

            if i > 0 and gameState.step_count % GHOST_MOVE_EVERY == 0:
                substeps = max(1, round(CELL_SIZE / squad.blinky.move_speed))
                for _ in range(substeps):
                    squad.update(
                        (pacman_r, pacman_c),
                        gameState.pacman.direction.value,
                        gameState.tick,
                        pellets_list=remaining_pellets,
                        map_grid=gameSetup.map.grid
                    )
                    gameState.tick += 1

                    if squad.check_collision_with_pacman(pacman_x, pacman_y):
                        gameState.runtime = time.time() - gameState.start_time
                        loseScreen(gameSetup, gameState)
                        return

        gameSetup.screen.update()
        gameSetup.screen.ontimer(lambda: step(i + 1), delay)
    step(0)

# ==========================================
# GAMESETUP AND GAMESTATE DEFINITION
# ==========================================

class GameSetup:
    """Class GameSetup chứa các biến cần thiết để thiết lập trò chơi ban đầu"""
    def __init__(self):
        self.ghost_count = DEFAULT_GHOST_COUNT
        self.ghost = self.ghost_count > 0
        self.map_size = TINY_SIZE
        self.auto_map_generate = False
        self.algorithm = Algorithm.NONE
        self.heuristic = Heuristic.NONE
        self.multifood = False 
        self.informed_search = False
        self.screen = init_screen()
        self.auto_mode = False
        self.map = Map()
        self.run_count = 1
        path = create_and_clear_results_folder()
        self.fileio = create_algorithm_data_text(self.run_count, path)
        self.search_count = 0

    def _initmap_(self):
        self.map = Map(auto_generate=self.auto_map_generate,
                       size=self.map_size,
                       ghost=self.ghost)

    def reset(self):
        self.run_count += 1
        self.search_count = 0
        self.ghost_count = DEFAULT_GHOST_COUNT
        self.ghost = self.ghost_count > 0
        self.map_size = TINY_SIZE
        self.auto_map_generate = False
        self.algorithm = Algorithm.NONE
        self.heuristic = Heuristic.NONE
        self.informed_search = False
        self.auto_mode = False
        self.map = Map()
        self.fileio = create_algorithm_data_text(self.run_count, RESULTS_DIR)
        self.search_count = 0


class GameState:
    """Class GameState lưu trữ dữ liệu trạng thái tại một thời điểm của trò chơi"""
    def __init__(self, gameSetup: GameSetup):
        self.wall_pen = Wall([])
        self.pellet_pen = Pellet([])
        self.ui_pen = UI_Pen()
        self.score_pen = UI_Pen()
        self.timer_pen = UI_Pen()
        self.pacman = Player()
        self.start_time = 0.0
        self.runtime = 0.0
        self.goal = False
        self.has_started = False
        self.is_paused = False
        self.pause_started_at = 0.0
        self.total_nodes = 0
        self.total_time = 0.0
        self.fallback_used = False
        # --- phần ma / điều khiển vòng lặp ---
        self.ghost_squad = None
        self.tick = 0
        self.step_count = 0
        self.running = False
        self.session = next(_session_counter)
        self.walls = set()
        self.pellets_eaten = 0
        self.skill_item = None
        self.skill_charges = 0
        self.skill_enabled = False
        self.skill_cooldown = 0
        self.skill_valid_cells = set()
        self.skill_hud_pen = None
        self.pending_skill = False
        self.effects = []
        self.avoiding_ghosts = False
        self.last_pellet_tick = 0
        self.minimax_target = None
        self.minimax_target_steps = 0
        # --- GHI FILE CHO MINIMAX --- #
        self.minimax_stats = None

    def reset(self, gameSetup):
        self.__init__(gameSetup)


# ==========================================
# FILE I/O FOR ALGORITHM DATA
# ==========================================

def write_algorithm_data(gameSetup: GameSetup, result: dict, search_id: int) -> None:
    algo_id = str(getattr(gameSetup.algorithm, "name", gameSetup.algorithm)).upper()
    if algo_id == "MINIMAX":
        value = result.get("value")
        value_text = f"{value:.2f}" if isinstance(value, (int, float)) else "N/A"
        t = result.get("time_taken", 0.0)
        data = (
            f"Algorithm: MINIMAX ({result.get('mode', 'alpha_beta')})        "
            f"Decision no.{search_id}\n\n"
            f"Agent: Pacman (MAX) vs {gameSetup.ghost_count} Ghost(s) (MIN)\n"
            f"Ghosts considered: {result.get('num_ghosts', 0)}\n"
            f"Search depth: {result.get('depth', 0)}\n"
            f"Chosen action: {result.get('action', '')}\n"
            f"Evaluation value: {value_text}\n"
            f"Nodes expanded: {result.get('nodes_expanded', 0)}\n"
            f"Decision time: {t:.6f} seconds ({t * 1000:.2f} ms)\n"
            f"{'-' * 40}\n"
        )
        with gameSetup.fileio.open("a", encoding="utf-8") as result_file:
            result_file.write(data)
        return
    if not hasattr(gameSetup, "fileio") or gameSetup.fileio is None:
        return
    
    problem = ("None") if gameSetup.ghost else (f"Multifood with max_food = {MAX_FOOD_MULTIFOOD}") if gameSetup.multifood else ("Singlefood")
    algo_name = gameSetup.algorithm.to_string() if hasattr(gameSetup.algorithm, 'to_string') else str(gameSetup.algorithm).upper()
    heu_name = gameSetup.heuristic.to_string() if hasattr(gameSetup.heuristic, 'to_string') else str(gameSetup.heuristic)
    data = (
        f"Problem: {problem}\n"
        f"Algorithm: {algo_name} - heuristic: {heu_name}        Run no.{search_id}\n\n"
        f"Solved: {result.get('is_solved', False)}\n"
        f"Path: {result.get('path', [])}\n"
        f"Total steps: {len(result.get('path', []))}\n"
        f"Total cost: {result.get('total_cost', 0)}\n"
        f"Nodes expanded: {result.get('nodes_expanded', 0)}\n"
        f"Execution time: {result.get('time_taken', 0.0)} seconds\n"
        f"{'-' * 40}\n"
    )
    with gameSetup.fileio.open("a", encoding="utf-8") as result_file:
        result_file.write(data)

# ==========================================
# RESTART SCREEN
# ==========================================

def restartGame(gameSetup: GameSetup, gameState: GameState):
    clear_game_screen(gameSetup.screen)      # thay cho update() + clear() + bgcolor("black")
    restart_pen = turtle.Turtle()

    restart_pen = turtle.Turtle()
    restart_pen.hideturtle()
    restart_pen.penup()

    def restart_selection(value):
        if value:
            return_to_main_menu(gameSetup, gameState)
        else:
            gameSetup.screen.bye()

    show_menu(restart_pen, gameSetup.screen, RESTART_MENU, restart_selection)
    gameSetup.screen.listen()


def return_to_main_menu(gameSetup, gameState):
    gameState.running = False
    for key in ("space", "Escape", "p"):
        gameSetup.screen.onkeyrelease(None, key)
    for key in ("Right", "Left", "Up", "Down"):
        gameSetup.screen.onkeypress(None, key=key)
    gameSetup.screen.onclick(None, 1)
    clear_game_screen(gameSetup.screen)      # <-- thay cho 6 dòng clearscreen ... bgcolor("black")
    gameSetup.reset()
    gameState.reset(gameSetup)
    startGame(gameSetup, gameState)


# ==========================================
# ENDGAME SCREENS
# ==========================================

def show_result_screen(gameSetup, gameState, title, color, lines):
    gameState.running = False
    for key in ("space", "Escape", "p"):
        gameSetup.screen.onkeyrelease(None, key)
    for key in ("Right", "Left", "Up", "Down"):
        gameSetup.screen.onkeypress(None, key=key)
    clear_game_screen(gameSetup.screen)

    result_pen = turtle.Turtle()
    result_pen.hideturtle()
    result_pen.penup()
    show_menu(result_pen, gameSetup.screen, CONTINUE_END,
              lambda _value: restartGame(gameSetup, gameState))
    render_1_text(result_pen, 0, 50, color, title, "center", ("Courier", 40, "bold"))
    for x, y, line_color, message, align, font in lines:
        render_1_text(result_pen, x, y, line_color, message, align, font)
    gameSetup.screen.update()
    gameSetup.screen.listen()


def endGame(gameSetup: GameSetup, gameState: GameState):
    algo_name = gameSetup.algorithm.to_string() if hasattr(gameSetup.algorithm, 'to_string') else str(gameSetup.algorithm).upper()
    lines = [
        (0, -20, "white", f"SCORE: {gameState.pacman.score}", "center", ("Courier", 20, "normal")),
        (0, -60, "white", f"ALGORITHM: {algo_name}", "center", ("Courier", 20, "normal")),
        (0, -100, "white", f"TIME: {round(gameState.runtime, 2)}s", "center", ("Courier", 20, "normal")),
        (0, -130, THEME["mint"], f"GHOSTS: {gameSetup.ghost_count}", "center", ("Courier", 16, "normal")),
    ]
    if gameSetup.auto_mode:
        lines.append((0, -170, "cyan",
                      f"NODES: {gameState.total_nodes} | SEARCH: {round(gameState.total_time, 3)}s",
                      "center", ("Courier", 16, "normal")))
        if gameState.fallback_used:
            lines.append((0, -195, "orange", "FALLBACK: NEAREST FOOD USED",
                          "center", ("Courier", 14, "normal")))
    show_result_screen(gameSetup, gameState, "YOU WIN!!!", "gold", lines)


def noPathScreen(gameSetup: GameSetup, gameState: GameState):
    algo_name = gameSetup.algorithm.to_string() if hasattr(gameSetup.algorithm, 'to_string') else str(gameSetup.algorithm).upper()
    lines = [
        (0, -10, "white", f"ALGORITHM: {algo_name}", "center", ("Courier", 20, "normal")),
        (0, -50, "yellow", f"FINAL SCORE: {gameState.pacman.score}", "center", ("Courier", 20, "normal")),
        (0, -90, THEME["mint"], f"GHOSTS: {gameSetup.ghost_count}", "center", ("Courier", 16, "normal")),
    ]
    show_result_screen(gameSetup, gameState, "PATH NOT FOUND!", "red", lines)


def loseScreen(gameSetup: GameSetup, gameState: GameState):
    """Màn hình thua khi bị ma bắt."""
    algo_name = gameSetup.algorithm.to_string() if hasattr(gameSetup.algorithm, 'to_string') else str(gameSetup.algorithm).upper()
    lines = [
        (0, -10, "white", f"ALGORITHM: {algo_name}", "center", ("Courier", 20, "normal")),
        (0, -50, "yellow", f"FINAL SCORE: {gameState.pacman.score}", "center", ("Courier", 20, "normal")),
        (0, -90, THEME["mint"], f"GHOSTS: {gameSetup.ghost_count}", "center", ("Courier", 16, "normal")),
    ]
    show_result_screen(gameSetup, gameState, "GAME OVER!", "red", lines)


# ==========================================
# MENU CHỌN CHẾ ĐỘ (CỦA NHÁNH KAI)
# ==========================================


# ==========================================
# MENU CHỌN CHẾ ĐỘ
# ==========================================

def startGame(gameSetup: GameSetup, gameState: GameState):
    menu_pen = turtle.Turtle()
    menu_pen.hideturtle()
    menu_pen.penup()
    menu_pen.speed(0)

    # Ngăn xếp lưu lịch sử từng bước để hỗ trợ nút Back và phím Escape
    steps = []

    def go_back():
        if len(steps) <= 1:
            return
        steps.pop()  # Bỏ bước hiện tại
        prev_step = steps[-1]
        render_step(prev_step)

    def go_to(step):
        if not steps or steps[-1] != step:
            steps.append(step)
        render_step(step)

    def _show(menu_data, callback, back_cb=None):
        try:
            show_menu(menu_pen, gameSetup.screen, menu_data, callback, back=back_cb)
        except TypeError:
            show_menu(menu_pen, gameSetup.screen, menu_data, callback)

    def render_step(step):
        menu_pen.clear()
        trace(f"menu shown step={step}")
        back_cb = go_back if len(steps) > 1 else None
        gameSetup.screen.onkey(back_cb, "Escape")

        if step == "main":
            # Lớp 1: Chọn Chế độ chơi (Auto / Manual)
            _show(MAIN_MENU, main_selection, back_cb=None)

        elif step == "ghost":
            # Lớp 2: Slider chỉnh số lượng ma (Thay thế GHOST_MENU)
            show_ghost_slider(
                menu_pen,
                gameSetup.screen,
                gameSetup.ghost_count,
                ghost_selection,
                back_cb
            )

        elif step == "adversarial":
            # Lớp 3 (Auto + Có ma): Chọn thuật toán đối kháng (Minimax...)
            _show(ADVERSARIAL_SEARCH_MENU, adversarial_selection, back_cb=back_cb)

        elif step == "search_type":
            # Lớp 3 (Auto + 0 ma): Chọn Informed vs Uninformed
            _show(SEARCH_TYPE_MENU, search_type_selection, back_cb=back_cb)

        elif step == "problem":
            # Lớp 4 (Auto + 0 ma): Chọn bài toán Single-food vs Multi-food
            _show(PROBLEM_MENU, problem_selection, back_cb=back_cb)

        elif step == "algo_informed":
            # Lớp 5a: Thuật toán tìm kiếm Heuristic (A*, Greedy)
            _show(INFORMED_SEARCH_MENU, algo_selection, back_cb=back_cb)

        elif step == "algo_uninformed":
            # Lớp 5b: Thuật toán tìm kiếm không Heuristic (BFS, DFS, UCS)
            _show(UNINFORMED_SEARCH_MENU, algo_selection, back_cb=back_cb)

        elif step == "heuristic":
            # Lớp 6: Chọn hàm Heuristic (Manhattan, Euclidean...)
            _show(HEURISTIC_MENU, heuristic_selection, back_cb=back_cb)

        elif step == "size":
            # Lớp 7: Chọn kích thước map
            _show(SIZE_MENU, size_selection, back_cb=back_cb)

        elif step == "map_type":
            # Lớp 8: Chọn map cố định hay sinh ngẫu nhiên
            _show(MAP_TYPE_MENU, map_type_selection, back_cb=back_cb)

    # --- Callbacks xử lý từng lựa chọn ---

    def main_selection(value):
        trace(f"menu selected main={value}")
        gameSetup.auto_mode = value
        go_to("ghost")

    def ghost_selection(value):
        trace(f"menu selected ghost_count={value}")
        count = max(0, min(4, int(value)))
        gameSetup.ghost_count = count
        gameSetup.ghost = count > 0

        if gameSetup.auto_mode:
            if gameSetup.ghost:
                go_to("adversarial")
            else:
                go_to("search_type")
        else:
            go_to("size")

    def adversarial_selection(value):
        trace(f"menu selected adversarial_algo={value}")
        gameSetup.algorithm = value
        gameSetup.informed_search = False
        go_to("size")

    def search_type_selection(value):
        trace(f"menu selected search_type={value}")
        gameSetup.informed_search = value
        go_to("problem")

    def problem_selection(value):
        trace(f"menu selected problem_multifood={value}")
        gameSetup.multifood = value
        if gameSetup.informed_search:
            go_to("algo_informed")
        else:
            go_to("algo_uninformed")

    def algo_selection(value):
        trace(f"menu selected algo={value}")
        gameSetup.algorithm = value
        if gameSetup.informed_search:
            go_to("heuristic")
        else:
            go_to("size")

    def heuristic_selection(value):
        trace(f"menu selected heuristic={value}")
        gameSetup.heuristic = value
        go_to("size")

    def size_selection(value):
        trace(f"menu selected map_size={value}")
        gameSetup.map_size = value
        go_to("map_type")

    def map_type_selection(value):
        trace(f"menu selected auto_map_generate={value}")
        gameSetup.auto_map_generate = value
        menu_pen.clear()
        steps.clear()
        launch_game(gameSetup, gameState, generate_map=True)

    # Khởi động tại Menu chính
    go_to("main")
    gameSetup.screen.listen()


def launch_game(gameSetup, gameState, generate_map=False):
    """Dựng map và mở một phiên chơi mới."""
    trace(f"launch_game generate_map={generate_map} ghosts={gameSetup.ghost_count} algorithm={gameSetup.algorithm}")
    if generate_map:
        gameSetup._initmap_()
    new_walls, new_pellets = gameSetup.map.calculate_maze_renderer_data()
    if gameSetup.ghost and new_pellets:
        new_pellets = keep_reachable(gameSetup.map.grid, new_pellets)
    if new_pellets:
        selected = scatter_pellets([pixel_to_cell(*p) for p in new_pellets], PELLET_DENSITY)
        new_pellets = [cell_to_pixel(cell) for cell in selected]
    if not new_pellets:
        try:
            raise ValueError("Map has no reachable pellets")
        except ValueError:
            log_exception("map setup failed")
        error_pen = turtle.Turtle(); error_pen.hideturtle(); error_pen.penup()
        error_pen.goto(0, 35); error_pen.color("red")
        error_pen.write("SETUP ERROR - see debug_trace.log", align="center", font=("Courier", 16, "bold"))
        show_menu(error_pen, gameSetup.screen,
                  [((0, -35, THEME["text"], "[ BACK TO MENU ]", "center", ("Courier", 16, "bold")), "menu")],
                  lambda _value: return_to_main_menu(gameSetup, gameState))
        gameSetup.screen.update()
        return
    gameState.wall_pen.walls = new_walls
    gameState.pellet_pen.pellets = new_pellets
    gameState.pellet_pen.stamps.clear()
    gameLoop(gameSetup, gameState)


# ==========================================
# VÒNG LẶP CỦA MA (dùng chung mọi chế độ)
# ==========================================

def ghost_loop(gameSetup, gameState, sid):
    if not is_live(gameState, sid) or gameState.ghost_squad is None:
        return

    if not gameState.is_paused:
        if gameState.tick > GHOST_GRACE_TICKS:
            p = gameState.pacman
            if gameState.tick % 15 == 0 or not hasattr(gameState, "_pellet_cells"):
                gameState._pellet_cells = [pixel_to_cell(px, py)
                                           for (px, py) in gameState.pellet_pen.stamps]
            gameState.ghost_squad.update(
                pixel_to_cell(p.xcor(), p.ycor()), p.direction.value, gameState.tick,
                pellets_list=gameState._pellet_cells, map_grid=gameSetup.map.grid)

            if gameState.ghost_squad.check_collision_with_pacman(p.xcor(), p.ycor()):
                loseScreen(gameSetup, gameState)
                return
        gameSetup.screen.update()
    gameSetup.screen.ontimer(lambda: ghost_loop(gameSetup, gameState, sid), 1000 // 60)


def ghosts_in_line(pacman_cell, ghost_cells, walls):
    """Return aligned ghosts with a clear row or column between them."""
    pr, pc = pacman_cell
    hit = []
    for index, (gr, gc) in enumerate(ghost_cells):
        if pr == gr:
            cells = ((pr, c) for c in range(min(pc, gc) + 1, max(pc, gc)))
        elif pc == gc:
            cells = ((r, pc) for r in range(min(pr, gr) + 1, max(pr, gr)))
        else:
            continue
        if all(cell not in walls for cell in cells):
            hit.append(index)
    return hit


class SkillItem(turtle.Turtle):
    def __init__(self, cell, lifetime=SKILL_LIFETIME_TICKS):
        super().__init__()
        self.hideturtle(); self.penup(); self.speed(0)
        self.shape("skill_item"); self.shapesize(1.0, 1.0)
        self.cell = cell
        self.goto(*cell_to_pixel(cell))
        self.ticks = lifetime
        self.showturtle()


def fx_loop(gameSetup, gameState, sid):
    if not is_live(gameState, sid):
        return
    if not gameState.is_paused:
        gameState.tick += 1
        if gameState.skill_cooldown > 0:
            gameState.skill_cooldown -= 1
        squad = gameState.ghost_squad
        ghosts = squad.ghosts if squad else []
        for ghost in ghosts:
            if not ghost.alive:
                ghost.respawn_ticks -= 1
                if ghost.respawn_ticks <= 0:
                    ghost.respawn()
            elif ghost.invuln_ticks > 0:
                ghost.invuln_ticks -= 1
            ghost.update_visual(gameState.tick)
            if gameState.tick % 30 == 0:
                pac_cell = pixel_to_cell(gameState.pacman.xcor(), gameState.pacman.ycor())
                trace(f"ghost tick={gameState.tick} color={ghost.color_name} alive={ghost.alive} visible={ghost.isvisible()} cell={ghost.get_grid_pos()} invuln={ghost.invuln_ticks} respawn={ghost.respawn_ticks} shape={ghost.shape()} pac_distance={ghost.distance(gameState.pacman.xcor(), gameState.pacman.ycor()):.1f} pac_cell={pac_cell}")
        item = gameState.skill_item
        if gameState.skill_enabled and gameState.pending_skill and item is None:
            pcell = pixel_to_cell(gameState.pacman.xcor(), gameState.pacman.ycor())
            occupied = {g.get_grid_pos() for g in ghosts}
            dist = {pcell: 0}; queue = deque([pcell])
            while queue:
                current = queue.popleft()
                for _, nxt in get_neighbors(current, gameState.walls, len(gameSetup.map.grid), len(gameSetup.map.grid[0])):
                    if nxt in gameState.skill_valid_cells and nxt not in dist:
                        dist[nxt] = dist[current] + 1; queue.append(nxt)
            pellet_cells = {pixel_to_cell(px, py) for px, py in gameState.pellet_pen.stamps}
            open_cells = [cell for cell in gameState.skill_valid_cells
                          if cell in dist and dist[cell] >= 5 and cell not in occupied
                          and cell != pcell and cell not in pellet_cells]
            if open_cells:
                cell = random.choice(open_cells)
                gameState.skill_item = item = SkillItem(cell)
                gameState.pellets_eaten = 0
            gameState.pending_skill = False
        if item:
            item.ticks -= 1
            if item.ticks <= 0:
                item.hideturtle(); item.clear(); gameState.skill_item = None
                gameState.pellets_eaten = 0
            else:
                (item.hideturtle if gameState.tick % max(2, 8 - (SKILL_LIFETIME_TICKS-item.ticks)//100) < 4
                 else item.showturtle)()
                if gameState.pacman.distance(item.xcor(), item.ycor()) < CELL_SIZE / 2:
                    gameState.skill_charges = min(SKILL_MAX_CHARGES, gameState.skill_charges + 1)
                    item.hideturtle(); item.clear(); gameState.skill_item = None
                    gameState.pellets_eaten = 0
                    gameState.skill_hud_value = None
                    float_text(gameState, item.cell, "+SKILL", "cyan", 15)
        for effect in list(gameState.effects):
            effect["ticks"] -= 1
            pen = effect["pen"]
            if effect["ticks"] <= 0:
                pen.clear(); gameState.effects.remove(effect)
            else:
                pen.clear()
                if effect.get("from") is not None:
                    pen.color("cyan"); pen.goto(*effect["from"]); pen.pendown(); pen.goto(*effect["to"]); pen.penup()
                if effect.get("text"):
                    x, y = effect["text_pos"]
                    pen.goto(x, y + (15-effect["ticks"])); pen.color(effect.get("color", "gold"))
                    pen.write(effect["text"], align="center", font=("Courier", 12, "bold"))
        if gameState.skill_enabled and gameState.skill_hud_pen is not None:
            if getattr(gameState, "skill_hud_value", None) != gameState.skill_charges:
                gameState.skill_hud_pen.clear()
                gameState.skill_hud_pen.goto(0, SCREEN_HEIGHT / 2 - 3 * CELL_SIZE)
                gameState.skill_hud_pen.color(THEME["lemon"] if gameState.skill_charges else THEME["muted"])
                gameState.skill_hud_pen.write(f"SKILL x{gameState.skill_charges}  [SPACE]", align="center",
                                              font=("Courier", 14, "bold"))
                gameState.skill_hud_value = gameState.skill_charges
    gameSetup.screen.ontimer(lambda: fx_loop(gameSetup, gameState, sid), 1000 // 60)


def float_text(gameState, cell, text, color, ticks):
    if len(gameState.effects) >= 6:
        return
    pen = turtle.Turtle(); pen.hideturtle(); pen.penup(); pen.speed(0); pen.color(color)
    gameState.effects.append({"pen": pen, "ticks": ticks, "text": text,
                              "text_pos": cell_to_pixel(cell), "color": color})


# ==========================================
# MANUAL MODE
# ==========================================

def main_GameLoop(gameSetup: GameSetup, gameState: GameState, pacman_start_x, pacman_start_y, sid=None) -> None:
    if sid is None:
        sid = gameState.session
    if not is_live(gameState, sid):
        return

    if gameState.is_paused:
        gameSetup.screen.ontimer(
            lambda: main_GameLoop(gameSetup, gameState, pacman_start_x, pacman_start_y, sid), 50)
        return

    gameState.score_pen.write_score(gameState.pacman.score)

    elapsed = time.time() - gameState.start_time
    gameState.timer_pen.write_time(elapsed)

    eat_pellets(gameState)

    gameState.pacman.check_wall_collision(gameSetup.map.grid)
    if getattr(gameState, "manual_started", False):
        gameState.pacman.move()
    gameSetup.screen.update()

    if gameSetup.ghost and gameState.ghost_squad:
        pacman_x, pacman_y = gameState.pacman.xcor(), gameState.pacman.ycor()
        if gameState.ghost_squad.check_collision_with_pacman(pacman_x, pacman_y):
            gameState.runtime = time.time() - gameState.start_time
            loseScreen(gameSetup, gameState)
            return

    if len(gameState.pellet_pen.stamps) == 0:
        gameState.runtime = time.time() - gameState.start_time
        endGame(gameSetup, gameState)
        return

    gameSetup.screen.ontimer(
        lambda: main_GameLoop(gameSetup, gameState, pacman_start_x, pacman_start_y, sid),
        1000 // 60)


# ==========================================
# AUTO MODE: MINIMAX CHO PACMAN
# ==========================================

def choose_minimax_step(gameSetup, gameState, pac, pellets, ghosts):
    """Trả về ô kế tiếp cho Pacman, hoặc None nếu kẹt."""
    from src.core.minimax import minimax_move, safe_plan
    t0 = time.perf_counter() # ĐO THỜI GIAN CHẠY MINIMAX

    grid = gameSetup.map.grid
    rows, cols = len(grid), len(grid[0])
    squad = gameState.ghost_squad

    if squad:
        starving = gameState.tick - gameState.last_pellet_tick >= 20 * 60
        for g in squad.ghosts:
            base = getattr(g, "base_move_speed", g.move_speed)
            g.move_speed = max(0.1, base * 0.7) if starving else base

    ratio = 1.0
    if squad and squad.ghosts:
        ratio = squad.ghosts[0].move_speed / CELL_SIZE * MINIMAX_DELAY / (1000 / 60)

    history = getattr(gameState, "minimax_history", None)
    if history is None:
        history = deque(maxlen=12)
        gameState.minimax_history = history
    history.append(pac)
    looped = len(history) == 12 and len(set(history)) <= 4

    targets = set(pellets)
    targets.discard(pac)
    bonus = {}
    skill_cell = None
    prefer = gameState.minimax_target if gameState.minimax_target in targets else None

    plan = safe_plan(pac, ghosts, targets, gameState.walls, rows, cols,
                     ratio=ratio, prefer=prefer, bonus=bonus, safest=looped)
    if plan:
        step, target, explored = plan
        gameState.minimax_target = target
        gameState.avoiding_ghosts = False
        gameState.total_nodes += explored
        gameState.minimax_stats = {               # GHI THÔNG TIN MINIMAX
            "mode": "safe_plan", "depth": 0, "value": None,
            "nodes_expanded": explored, "num_ghosts": len(ghosts),
            "time_taken": time.perf_counter() - t0}
        return step

    gameState.minimax_target = None
    gameState.avoiding_ghosts = True
    stats = {}                                    # GHI THÔNG TIN MINIMAX
    nxt, nodes = minimax_move(pac, ghosts, pellets, gameState.walls, rows, cols,
                              skill_cell=skill_cell, recent_cells=tuple(history),
                              ghost_move_ratio=ratio, stats = stats)
    stats["mode"] = "alpha_beta"                  # GHI THÔNG TIN MINIMAX
    stats["time_taken"] = time.perf_counter() - t0
    gameState.minimax_stats = stats
    gameState.total_nodes += nodes
    return nxt


def _bfs_minimax_fallback(gameState, grid, pac, pellets, farthest_from_ghost=False):
    """Tìm nước đi hợp lệ đầu tiên tới pellet bằng BFS, ưu tiên an toàn."""
    squad = gameState.ghost_squad
    ghost_cells = [g.get_grid_pos() for g in squad.ghosts if g.alive] if squad else []
    queue = deque([pac])
    parents = {pac: None}
    distance = {pac: 0}
    while queue:
        cell = queue.popleft()
        for _, nxt in get_neighbors(cell, gameState.walls, len(grid), len(grid[0])):
            if nxt not in parents:
                parents[nxt] = cell
                distance[nxt] = distance[cell] + 1
                queue.append(nxt)

    ghost_distance = {cell: 0 for cell in ghost_cells}
    queue = deque(ghost_cells)
    while queue:
        cell = queue.popleft()
        if ghost_distance[cell] >= 12:
            continue
        for _, nxt in get_neighbors(cell, gameState.walls, len(grid), len(grid[0])):
            if nxt not in ghost_distance:
                ghost_distance[nxt] = ghost_distance[cell] + 1
                queue.append(nxt)

    def first_step(target):
        current = target
        while parents[current] != pac:
            current = parents[current]
        return current

    candidates = [food for food in pellets if food in parents and food != pac]
    if candidates:
        if farthest_from_ghost:
            target = max(candidates, key=lambda food: (
                ghost_distance.get(food, 99), -distance[food]))
        else:
            target = min(candidates, key=lambda food: (
                ghost_distance.get(first_step(food), 99) <= 1,
                distance[food],
                -ghost_distance.get(first_step(food), 99)))
        return first_step(target)

    legal = list(get_neighbors(pac, gameState.walls, len(grid), len(grid[0])))
    if legal:
        return max((cell for _, cell in legal),
                   key=lambda cell: ghost_distance.get(cell, 99))
    return None


def run_minimax(gameSetup, gameState, sid):
    """Vòng lặp riêng khi chọn Minimax: mỗi lần đi đúng 1 ô."""
    if not is_live(gameState, sid):
        return
    screen = gameSetup.screen
    if gameState.is_paused:
        screen.ontimer(lambda: run_minimax(gameSetup, gameState, sid), 50)
        return

    gameState.pacman.pendown()
    gameState.timer_pen.write_time(time.time() - gameState.start_time)

    eat_pellets(gameState)
    if len(gameState.pellet_pen.stamps) == 0:
        gameState.runtime = time.time() - gameState.start_time
        endGame(gameSetup, gameState)
        return

    grid = gameSetup.map.grid
    pac = pixel_to_cell(gameState.pacman.xcor(), gameState.pacman.ycor())
    pellets = [pixel_to_cell(px, py) for (px, py) in gameState.pellet_pen.stamps]
    squad = gameState.ghost_squad
    ghosts = [(g.get_grid_pos()) for g in squad.ghosts
              if g.alive and g.invuln_ticks <= 0] if squad else []
    legal = [cell for _, cell in get_neighbors(pac, gameState.walls, len(grid), len(grid[0]))]

    t0 = time.perf_counter()
    try:
        if hasattr(gameState, "_prepared_minimax_step"):
            nxt = gameState._prepared_minimax_step
            del gameState._prepared_minimax_step
        else:
            nxt = choose_minimax_step(gameSetup, gameState, pac, pellets, ghosts)
    except Exception:
        gameState.total_time += time.perf_counter() - t0
        log_exception("minimax decision failed")
        nxt = None
    else:
        gameState.total_time += time.perf_counter() - t0

    if nxt is None:
        try:
            nxt = _bfs_minimax_fallback(gameState, grid, pac, pellets)
        except Exception:
            log_exception("minimax BFS fallback failed")
            nxt = None

    if nxt == pac:
        gameState.minimax_stagnation_count = getattr(gameState, "minimax_stagnation_count", 0) + 1
        if gameState.minimax_stagnation_count > 3:
            nxt = _bfs_minimax_fallback(gameState, grid, pac, pellets, farthest_from_ghost=True)
            gameState.minimax_stagnation_count = 0
    else:
        gameState.minimax_stagnation_count = 0

    if nxt != pac and nxt not in legal:
        nxt = _bfs_minimax_fallback(gameState, grid, pac, pellets)

    if not legal:
        noPathScreen(gameSetup, gameState)
        return
    if nxt not in legal:
        nxt = max(legal, key=lambda cell: min(
            (abs(cell[0] - ghost[0]) + abs(cell[1] - ghost[1]) for ghost in ghosts),
            default=99))

    stats = gameState.minimax_stats or {"mode": "fallback"}
    gameState.minimax_stats = None
    gameSetup.search_count += 1
    try:
        write_algorithm_data(gameSetup, {
            **stats,
            "action": ACTION_FROM_DELTA.get((nxt[0] - pac[0], nxt[1] - pac[1]), "STAY"),
        }, gameSetup.search_count)
    except Exception:
        log_exception("write minimax data failed")

    d = DIR_FROM_DELTA.get((nxt[0] - pac[0], nxt[1] - pac[1]))
    if d:
        gameState.pacman.direction = d
        gameState.pacman.setheading(d.value)
        gameState.pacman.anim_tick += 1
        gameState.pacman.shape(f"pacman_{(0, 1, 2, 1)[(gameState.pacman.anim_tick // 4) % 4]}")

    x, y = cell_to_pixel(nxt)
    gameState.pacman.goto(x, y)
    eat_pellets(gameState)
    if len(gameState.pellet_pen.stamps) == 0:
        gameState.runtime = time.time() - gameState.start_time
        endGame(gameSetup, gameState)
        return

    screen.update()
    screen.ontimer(lambda: run_minimax(gameSetup, gameState, sid), MINIMAX_DELAY)


# ==========================================
# GAMELOOP CHUNG
# ==========================================

def gameLoop(gameSetup: GameSetup, gameState: GameState):
    trace("gameLoop entered")
    gameState.skill_enabled = not gameSetup.auto_mode and gameSetup.ghost_count > 0
    startup_timings = []
    draw_started = time.perf_counter()
    # INIT
    gameState.wall_pen.draw()
    gameState.pellet_pen.draw()
    trace(f"walls/pellets drawn walls={len(gameState.wall_pen.walls)} pellets={len(gameState.pellet_pen.pellets)}")
    gameState.ui_pen.draw_ui_area()
    gameSetup.screen.update()
    startup_timings.append(("initial_draw_ms", (time.perf_counter()-draw_started)*1000))
    gameState.startup_timings = startup_timings

    # START COOR
    if not gameState.pellet_pen.pellets:
        raise ValueError("Map has no reachable pellets")
    pacman_start_coor = gameState.pellet_pen.pellets[0]
    pacman_start_x = pacman_start_coor[0]
    pacman_start_y = pacman_start_coor[1]

    # PACMAN COOR UPDATES
    gameState.pacman.goto(pacman_start_x, pacman_start_y)
    gameState.pacman.showturtle()

    gameState.has_started = False
    gameState.is_paused = True
    gameState.pause_started_at = 0.0
    gameState.tick = 0
    gameState.running = True
    sid = gameState.session

    pause_pen = turtle.Turtle()
    pause_pen.hideturtle()
    pause_pen.penup()
    menu_pen = turtle.Turtle()
    menu_pen.hideturtle()
    menu_pen.penup()
    menu_button_pos = (-SCREEN_WIDTH / 2 + 103, SCREEN_HEIGHT / 2 - 2 * CELL_SIZE)

    overlay = turtle.Turtle()
    overlay.hideturtle()
    overlay.penup()
    overlay.speed(0)
    overlay_open = {"value": False}
    countdown_pen = turtle.Turtle()
    countdown_pen.hideturtle(); countdown_pen.penup(); countdown_pen.speed(0)
    countdown = {"active": False}

    def restart_current_game():
        ghost, count, auto, algorithm, size, auto_map = (gameSetup.ghost, gameSetup.ghost_count,
            gameSetup.auto_mode, gameSetup.algorithm, gameSetup.map_size, gameSetup.auto_map_generate)
        gameState.running = False
        for key in ("space", "Escape", "p", "Right", "Left", "Up", "Down"):
            gameSetup.screen.onkeyrelease(None, key)
            gameSetup.screen.onkeypress(None, key)
        clear_game_screen(gameSetup.screen)
        gameSetup.ghost, gameSetup.ghost_count = ghost, count
        gameSetup.auto_mode, gameSetup.algorithm = auto, algorithm
        gameSetup.map_size, gameSetup.auto_map_generate = size, auto_map
        gameSetup._initmap_()
        gameState.reset(gameSetup)
        launch_game(gameSetup, gameState)

    def close_overlay():
        overlay.clear()
        if overlay_open.get("frame"):
            overlay_open["frame"].clear()
        overlay_open["value"] = False
        draw_game_menu_button()
        gameSetup.screen.update()
        trace("pause menu closed")

    def pause_selection(value):
        if value == "continue":
            gameState.start_time += time.time() - gameState.pause_started_at
            gameState.pause_started_at = 0.0
            gameState.is_paused = False
            close_overlay()
        elif value == "restart":
            restart_current_game()
        elif value == "menu":
            return_to_main_menu(gameSetup, gameState)

    def open_pause_menu():
        if not gameState.has_started or not gameState.running or overlay_open["value"]:
            return
        if not gameState.is_paused:
            gameState.is_paused = True
            gameState.pause_started_at = time.time()
        overlay_open["value"] = True
        trace("pause menu opened")
        frame = turtle.Turtle(); frame.hideturtle(); frame.penup(); frame.color("white", "black"); frame.pensize(3)
        frame.begin_fill()
        frame.goto(-170, 150); frame.pendown()
        for _ in range(2):
            frame.forward(340); frame.right(90); frame.forward(310); frame.right(90)
        frame.end_fill(); frame.penup()
        overlay_open["frame"] = frame
        show_menu(overlay, gameSetup.screen, PAUSE_MENU, pause_selection)
        gameSetup.screen.update()

    def draw_game_menu_button():
        text = [((menu_button_pos[0], menu_button_pos[1], THEME["text"], "MENU",
                 "center", ("Courier", 12, "bold")), "open")]
        show_menu(menu_pen, gameSetup.screen, text, lambda _value: open_pause_menu())

    draw_game_menu_button()
    trace("game MENU button drawn")
    gameSetup.screen.onkeyrelease(lambda: None, key="space")
    gameSetup.screen.onkeyrelease(lambda: None, key="Escape")
    gameSetup.screen.onkeyrelease(lambda: None, key="p")
    gameSetup.screen.listen()
    pause_pen.goto(0, 0)
    pause_pen.color(THEME["text"])
    pause_pen.write("PRESS SPACE TO START", align="center", font=("Courier", 20, "bold"))
    hint_pen = turtle.Turtle(); hint_pen.hideturtle(); hint_pen.penup(); hint_pen.color(THEME["muted"])
    hint_pen.goto(0, -30)
    hint_pen.write("ARROWS: MOVE   SPACE: SHOOT   ESC/P: PAUSE" if gameState.skill_enabled else "ESC/P: PAUSE",
                   align="center", font=("Courier", 11, "normal"))
    if gameState.skill_enabled:
        gameState.skill_hud_pen = turtle.Turtle(); gameState.skill_hud_pen.hideturtle(); gameState.skill_hud_pen.penup()
        gameState.skill_hud_value = None
    gameSetup.screen.update()
    trace("game key bindings registered; PRESS SPACE displayed")

    # ---- KHỞI TẠO BẢN ĐỒ VÀ MA DỰA TRÊN SỐ LƯỢNG MA (GHOST_COUNT) ----
    grid = gameSetup.map.grid
    rows, cols = len(grid), len(grid[0])
    data = extract_map_data(grid)
    walls = set(data["wall"])
    gameState.walls = walls
    gameState.ghost_squad = None

    door_cells = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != " ":
                continue
            neighbors = [grid[nr][nc] for nr, nc in ((r-1,c), (r+1,c), (r,c-1), (r,c+1))
                         if 0 <= nr < rows and 0 <= nc < cols]
            if "G" in neighbors and "." in neighbors:
                door_cells.add((r, c))
    ghost_walls = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                   if value not in (".", "G") and (r, c) not in door_cells}
    pac_start_cell = pixel_to_cell(pacman_start_x, pacman_start_y)
    gameState.skill_valid_cells = set()
    queue = deque([pac_start_cell]); gameState.skill_valid_cells.add(pac_start_cell)
    while queue:
        current = queue.popleft()
        for _, nxt in get_neighbors(current, walls, rows, cols):
            if nxt not in gameState.skill_valid_cells and grid[nxt[0]][nxt[1]] == ".":
                gameState.skill_valid_cells.add(nxt); queue.append(nxt)
    gameState.skill_enabled = not gameSetup.auto_mode and gameSetup.ghost_count > 0

    if gameSetup.ghost_count > 0:
        ghost_started = time.perf_counter()
        trace(f"before GhostSquad ghost_count={gameSetup.ghost_count} map_G={len(data['ghost'])}")
        try:
            squad = GhostSquad(ghost_walls, rows, cols, num_ghosts=gameSetup.ghost_count)
            if data["ghost"]:
                spawns = [data["ghost"][0]] * gameSetup.ghost_count
            else:
                spawns = pick_ghost_spawns(ghost_walls, rows, cols,
                                           pixel_to_cell(pacman_start_x, pacman_start_y),
                                           n=gameSetup.ghost_count)
            if len(spawns) != gameSetup.ghost_count:
                raise ValueError(f"Expected {gameSetup.ghost_count} ghost spawns, got {len(spawns)}")
            trace(f"GhostSquad spawn cells={spawns}")
            carve_ghost_exits(grid, ghost_walls, spawns, gameState.skill_valid_cells)   # <-- thêm
            squad.set_start_positions(spawns)
            squad.set_start_positions(spawns)
            gameState.ghost_squad = squad
            path_started = time.perf_counter()
            pac_cell = pixel_to_cell(pacman_start_x, pacman_start_y)
            food_cells = [pixel_to_cell(px,py) for px,py in gameState.pellet_pen.stamps]
            for index, ghost in enumerate(squad.ghosts):
                target = ghost.calculate_target_tile(
                    pac_cell, gameState.pacman.direction.value, squad.ghosts, ghost_walls,
                    rows, cols, food_cells, grid, ghost_index=index)
                if target is None:
                    trace(f"ghost target missing index={index} personality={ghost.personality}; holding spawn tile")
                    target = ghost.get_grid_pos()
                ghost.update_ai_path(target, ghost_walls, rows, cols)
            startup_timings.append(("ghost_first_paths_ms", (time.perf_counter()-path_started)*1000))
            startup_timings.append(("ghost_setup_ms", (time.perf_counter()-ghost_started)*1000))
            trace(f"GhostSquad ready count={len(squad.ghosts)} elapsed_ms={(time.perf_counter()-ghost_started)*1000:.1f}")
            gameSetup.screen.update()
        except Exception:
            log_exception("GhostSquad setup failed")
            gameState.ghost_squad = None
            pause_pen.clear()
            pause_pen.goto(0, 35); pause_pen.color("red")
            pause_pen.write("SETUP ERROR - see debug_trace.log", align="center", font=("Courier", 16, "bold"))
            show_menu(menu_pen, gameSetup.screen,
                      [((0, -35, "white", "[ BACK TO MENU ]", "center", ("Courier", 16, "bold")), "menu")],
                      lambda _value: return_to_main_menu(gameSetup, gameState))
            gameSetup.screen.update()
            return

    # Thuật toán
    def ucs_weighted(p, n=30000):
        p.weighted = True
        return ucs(p, n)

    ALGORITHMS = {
        "dfs":    lambda p, n=30000: dfs(p, n),
        "bfs":    lambda p, n=30000: bfs(p, n),
        "ucs":    ucs_weighted,
        "greedy": lambda p, n=30000: greedy_search(p, get_heuristic(None, p), n),
        "a_star": lambda p, n=30000: a_star(p, get_heuristic(None, p), n),
    }

    MULTI_THRESHOLD = 5
    gameState.start_time = time.time()

    if gameSetup.auto_mode:
        def run_next_search(prepare_only=False):
            search_started = time.perf_counter()
            if not is_live(gameState, sid):
                return
            if len(gameState.pellet_pen.stamps) == 0:
                gameState.runtime = time.time() - gameState.start_time
                endGame(gameSetup, gameState)
                return

            row, col = pixel_to_cell(gameState.pacman.xcor(), gameState.pacman.ycor())
            start = (row, col)
            foods = [pixel_to_cell(px, py) for (px, py) in gameState.pellet_pen.stamps.keys()]
            
            algo_key = str(gameSetup.algorithm).lower()
            if hasattr(gameSetup.algorithm, 'name'):
                algo_key = gameSetup.algorithm.name.lower()
            algo = ALGORITHMS.get(algo_key, ALGORITHMS["a_star"])

            result = None

            # Ít pellet: giải bài toán nhiều pellet
            if len(foods) <= MULTI_THRESHOLD:
                problem = MultiFood(gameSetup.map.grid, current_pos=start, remaining_foods=foods)
                result = solve_multi_food(problem, algo)
                record_stats(gameState, result)

            # Nhiều pellet: fallback về tìm pellet gần nhất
            if result is None or not result["is_solved"]:
                foods.sort(key=lambda p: abs(p[0] - row) + abs(p[1] - col))
                for food in foods:
                    problem = SingleFoodProblem(gameSetup.map.grid, food_pos=food, start_pos=start)
                    problem.pellets = frozenset(foods)
                    result = algo(problem, 30000)
                    record_stats(gameState, result)
                    if result["is_solved"]:
                        break

            gameSetup.search_count += 1
            try:
                write_algorithm_data(gameSetup, result, gameSetup.search_count)
            except Exception:
                pass

            if result is not None and result["is_solved"]:
                if not any(name == "first_search_ms" for name, _ in startup_timings):
                    startup_timings.append(("first_search_ms", (time.perf_counter()-search_started)*1000))
                cells = path_to_cells(start, result["path"])
                if prepare_only:
                    gameState._prepared_search_cells = cells
                    return
                follow_path_ai(gameSetup, gameState, cells, delay=40, callback=run_next_search)
            else:
                if prepare_only:
                    gameState._prepared_search_failed = True
                    return
                noPathScreen(gameSetup, gameState)

    def start_game_once():
        if not gameState.running or gameState.has_started or countdown["active"] or overlay_open["value"]:
            return
        countdown["active"] = True
        countdown_pen.clear(); pause_pen.clear(); hint_pen.clear()

        def begin_running():
            if not is_live(gameState, sid):
                return
            countdown["active"] = False
            countdown_pen.clear()
            gameState.has_started = True
            gameState.is_paused = False
            gameState.start_time = time.time()
            gameState.tick = 0
            if gameState.ghost_squad:
                ghost_loop(gameSetup, gameState, sid)
                fx_loop(gameSetup, gameState, sid)
            if gameSetup.auto_mode:
                if (str(gameSetup.algorithm).lower() == "minimax" or getattr(gameSetup.algorithm, 'name', '') == 'MINIMAX') and gameState.ghost_squad:
                    run_minimax(gameSetup, gameState, sid)
                elif getattr(gameState, "_prepared_search_failed", False):
                    gameState._prepared_search_failed = False
                    noPathScreen(gameSetup, gameState)
                    return
                else:
                    prepared = getattr(gameState, "_prepared_search_cells", None)
                    if prepared:
                        gameState._prepared_search_cells = None
                        follow_path_ai(gameSetup, gameState, prepared, delay=40, callback=run_next_search)
                    else:
                        run_next_search()
            else:
                gameState.manual_started = False
                directions = (("Right", Direction.right), ("Left", Direction.left),
                              ("Up", Direction.up), ("Down", Direction.down))
                for key, direction in directions:
                    def move(d=direction):
                        gameState.pacman.turn(d)
                        gameState.manual_started = True
                    gameSetup.screen.onkeypress(move, key)
                main_GameLoop(gameSetup, gameState, pacman_start_x, pacman_start_y, sid)

        def countdown_step(index):
            if not is_live(gameState, sid) or not countdown["active"]:
                return
            countdown_pen.clear(); countdown_pen.goto(0, 0); countdown_pen.color(THEME["lemon"])
            if index > 0:
                countdown_pen.write(str(index), align="center", font=("Courier", 64, "bold"))
                gameSetup.screen.update()
                gameSetup.screen.ontimer(lambda: countdown_step(index - 1), 700)
            else:
                countdown_pen.write("GO!", align="center", font=("Courier", 56, "bold"))
                gameSetup.screen.update(); gameSetup.screen.ontimer(begin_running, 250)
        countdown_step(3)

    def fire_skill():
        if (not gameState.skill_enabled or not gameState.has_started or not gameState.running
                or gameState.is_paused or countdown["active"]):
            return
        if gameState.skill_charges <= 0:
            float_text(gameState, pixel_to_cell(gameState.pacman.xcor(), gameState.pacman.ycor()), "NO SKILL", THEME["muted"], 20)
            return
        if gameState.skill_cooldown > 0:
            return
        gameState.skill_charges -= 1
        gameState.skill_cooldown = SKILL_COOLDOWN_TICKS
        start = pixel_to_cell(gameState.pacman.xcor(), gameState.pacman.ycor())
        dr, dc = {Direction.up: (-1, 0), Direction.down: (1, 0),
                  Direction.left: (0, -1), Direction.right: (0, 1)}[gameState.pacman.direction]
        ray = []; cell = start
        while True:
            nxt = (cell[0] + dr, cell[1] + dc)
            if not (0 <= nxt[0] < rows and 0 <= nxt[1] < cols) or nxt in gameState.walls:
                break
            ray.append(nxt); cell = nxt
        pen = turtle.Turtle(); pen.hideturtle(); pen.penup(); pen.speed(0); pen.color("cyan")
        pen.goto(*cell_to_pixel(start)); pen.pendown(); pen.pensize(3); pen.goto(*cell_to_pixel(cell)); pen.penup()
        if len(gameState.effects) < 6:
            gameState.effects.append({"pen": pen, "ticks": 10})
        targets = [g for g in (gameState.ghost_squad.ghosts if gameState.ghost_squad else [])
                   if g.alive and g.get_grid_pos() in ray]
        for ghost in targets:
            ghost.kill(); gameState.pacman.score += SKILL_SCORE_PER_GHOST
            float_text(gameState, ghost.get_grid_pos(), "+50", "gold", 15)
        if not targets:
            float_text(gameState, cell, "MISS", "cyan", 15)
        gameState.score_pen.write_score(gameState.pacman.score)
        gameState.skill_hud_value = None

    def pause_toggle():
        if not gameState.has_started or not gameState.running or countdown["active"]:
            return
        if overlay_open["value"]:
            pause_selection("continue")
        else:
            open_pause_menu()

    def space_action():
        if not gameState.has_started:
            start_game_once()
        elif gameState.skill_enabled:
            fire_skill()

    gameSetup.screen.onkeyrelease(space_action, key="space")
    gameSetup.screen.onkeyrelease(pause_toggle, "Escape")
    gameSetup.screen.onkeyrelease(pause_toggle, "p")
    gameState._space_handler = space_action
    gameState._start_handler = start_game_once
    gameState._escape_handler = pause_toggle

    trace("game key/click bindings active")
    if gameSetup.auto_mode:
        prepare_started = time.perf_counter()
        if (str(gameSetup.algorithm).lower() == "minimax" or getattr(gameSetup.algorithm, 'name', '') == 'MINIMAX') and gameState.ghost_squad:
            pcell = pixel_to_cell(pacman_start_x, pacman_start_y)
            pellet_cells = [pixel_to_cell(px,py) for px,py in gameState.pellet_pen.stamps if pixel_to_cell(px,py) != pcell]
            ghost_cells = [g.get_grid_pos() for g in gameState.ghost_squad.ghosts
                           if g.alive and g.invuln_ticks <= 0]
            gameState._prepared_minimax_step = choose_minimax_step(
                gameSetup, gameState, pcell, pellet_cells, ghost_cells)
            startup_timings.append(("first_minimax_planning_ms", (time.perf_counter()-prepare_started)*1000))
        else:
            run_next_search(prepare_only=True)
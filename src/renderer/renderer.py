import turtle
from src.core.config import (SCREEN_HEIGHT, SCREEN_WIDTH, CELL_SIZE, THEME)
from maps.map import *
from src.renderer.ui import show_menu as _show_pastel_menu, clear_ui

# ==============================
# TEXT DATA AND RENDER
# ==============================
MAIN_MENU = [
    ((0, 100, "yellow", "THE PACMAN GAME", "center", ("Courier", 50, "bold")), None),
    ((0, 0  , "white" , "[ MANUAL ]"     , "center", ("Courier", 25, "bold")), False),
    ((0, -70, "cyan"  , "[ AUTO ]"       , "center", ("Courier", 25, "bold")), True)
]

# Menu chọn số lượng ma nguyên bản của branch Kai
GHOST_MENU = [
    ((0, 120 , "yellow", "NUMBER OF GHOSTS"       , "center", ("Courier", 35, "bold")), None),
    ((0, 60  , "white" , "[ 0 GHOST (NO ENEMY) ]" , "center", ("Courier", 20, "bold")), 0),
    ((0, 15  , "red"   , "[ 1 GHOST  (BLINKY) ]"  , "center", ("Courier", 20, "bold")), 1),
    ((0, -30 , "cyan"  , "[ 2 GHOSTS (+INKY) ]"   , "center", ("Courier", 20, "bold")), 2),
    ((0, -75 , "pink"  , "[ 3 GHOSTS (+PINKY) ]"  , "center", ("Courier", 20, "bold")), 3),
    ((0, -120, "orange", "[ 4 GHOSTS (+CLYDE) ]"  , "center", ("Courier", 20, "bold")), 4),
]

MAP_TYPE_MENU = [
    ((0, 120 , "yellow", "RANDOM MAP OR EXIST MAP", "center", ("Courier", 40, "bold")), None),
    ((0, 0   , "white" , "[ RANDOM ]"       , "center", ("Courier", 25, "bold")), True),
    ((0, -70 , "white" , "[ EXIST ]"        , "center", ("Courier", 25, "bold")), False)
]

SIZE_MENU = [
    ((0, 120 , "yellow", "CHOOSE YOUR MAP SIZE", "center", ("Courier", 40, "bold")), None),
    ((0, 40  , "green" , "[ TINY ]"            , "center", ("Courier", 25, "bold")), TINY_SIZE),
    ((0, -30 , "orange", "[ MEDIUM ]"          , "center", ("Courier", 25, "bold")), MEDIUM_SIZE),
    ((0, -100, "red"   , "[ LARGE ]"           , "center", ("Courier", 25, "bold")), BIG_SIZE)
]

ALGORITHM_MENU = [
    ((0, 120 , "yellow" , "CHOOSE ALGORITHM", "center", ("Courier", 40, "bold")), None),
    ((0, 50  , "white"  , "[ A* SEARCH ]"   , "center", ("Courier", 20, "bold")), 'a_star'),
    ((0, 10  , "white"  , "[ GREEDY ]"      , "center", ("Courier", 20, "bold")), 'greedy'),
    ((0, -30 , "white"  , "[ BFS ]"         , "center", ("Courier", 20, "bold")), 'bfs'),
    ((0, -70 , "white"  , "[ DFS ]"         , "center", ("Courier", 20, "bold")), 'dfs'),
    ((0, -110, "white"  , "[ UCS ]"         , "center", ("Courier", 20, "bold")), 'ucs'),
    ((0, -150, "white"  , "[ MINIMAX ]"     , "center", ("Courier", 20, "bold")), 'minimax')
]

CONTINUE_END = [
    ((0, -270, "white", ">> CLICK TO CONTINUE <<", "center", ("Courier", 18, "bold")), True),
]

RESTART_MENU = [
    ((0, 80, "yellow", "DO YOU WANT TO RESTART?", "center", ("Courier", 30, "bold")), None),
    ((0, -10, "green", "[ YES ]", "center", ("Courier", 24, "bold")), True),
    ((0, -80, "red", "[ NO ]", "center", ("Courier", 24, "bold")), False),
]

PAUSE_MENU = [
    ((0, 105, "yellow", "PAUSED", "center", ("Courier", 30, "bold")), None),
    ((0, 35, "white", "[ CONTINUE ]", "center", ("Courier", 20, "bold")), "continue"),
    ((0, -25, "cyan", "[ RESTART ]", "center", ("Courier", 20, "bold")), "restart"),
    ((0, -85, "orange", "[ BACK TO MENU ]", "center", ("Courier", 20, "bold")), "menu"),
]
ADVERSARIAL_SEARCH_MENU = [
    ((0, 120, "yellow", "ADVERSARIAL SEARCH", "center", ("Courier", 35, "bold")), None),
    ((0, 30 , "white" , "[ MINIMAX ]"       , "center", ("Courier", 22, "bold")), 'minimax'),
]

SEARCH_TYPE_MENU = [
    ((0, 120, "yellow", "SEARCH STRATEGY", "center", ("Courier", 35, "bold")), None),
    ((0, 40 , "white" , "[ UNINFORMED SEARCH ]", "center", ("Courier", 20, "bold")), False),
    ((0, -30, "white" , "[ INFORMED SEARCH ]"  , "center", ("Courier", 20, "bold")), True),
]

PROBLEM_MENU = [
    ((0, 120, "yellow", "PROBLEM TYPE", "center", ("Courier", 35, "bold")), None),
    ((0, 40 , "white" , "[ SINGLE FOOD ]", "center", ("Courier", 22, "bold")), False),
    ((0, -30, "white" , "[ MULTI FOOD ]" , "center", ("Courier", 22, "bold")), True),
]

INFORMED_SEARCH_MENU = [
    ((0, 120, "yellow", "INFORMED ALGORITHMS", "center", ("Courier", 35, "bold")), None),
    ((0, 40 , "white" , "[ A* SEARCH ]"      , "center", ("Courier", 22, "bold")), 'a_star'),
    ((0, -30, "white" , "[ GREEDY SEARCH ]"  , "center", ("Courier", 22, "bold")), 'greedy'),
]

UNINFORMED_SEARCH_MENU = [
    ((0, 120, "yellow", "UNINFORMED ALGORITHMS", "center", ("Courier", 35, "bold")), None),
    ((0, 50 , "white" , "[ BFS ]", "center", ("Courier", 22, "bold")), 'bfs'),
    ((0, 0  , "white" , "[ DFS ]", "center", ("Courier", 22, "bold")), 'dfs'),
    ((0, -50, "white" , "[ UCS ]", "center", ("Courier", 22, "bold")), 'ucs'),
]

HEURISTIC_MENU = [
    ((0, 120, "yellow", "CHOOSE HEURISTIC", "center", ("Courier", 35, "bold")), None),
    ((0, 40 , "white" , "[ MANHATTAN ]", "center", ("Courier", 20, "bold")), 'manhattan'),
    ((0, -30, "white" , "[ EUCLIDEAN ]", "center", ("Courier", 20, "bold")), 'euclidean'),
]


def render_1_text(pen: turtle.Turtle, x, y, color, msg: str, text_align, text_font) -> None:
    pen.goto(x, y)
    pen.color(color)
    pen.write(msg, align=text_align, font=text_font)


def render_many_text(pen: turtle.Turtle, text_list):
    for single_text in text_list:
        render_1_text(pen, *(single_text[0]))


class Pen(turtle.Turtle):
    def __init__(self):
        super().__init__()
        self.hideturtle()
        self.penup()
        self.speed(0)
        self.color("silver")


class Wall(Pen):
    def __init__(self, walls):
        super().__init__()
        self.pencolor("blue")
        self.pensize(2)
        self.hideturtle()
        self.speed(0)
        self.walls = walls

    def draw(self):
        wall_set = set(self.walls)
        half_cell = CELL_SIZE / 2

        for x, y in self.walls:
            if (x, y + CELL_SIZE) not in wall_set:
                self.penup()
                self.goto(x - half_cell, y + half_cell)
                self.pendown()
                self.goto(x + half_cell, y + half_cell)

            if (x, y - CELL_SIZE) not in wall_set:
                self.penup()
                self.goto(x - half_cell, y - half_cell)
                self.pendown()
                self.goto(x + half_cell, y - half_cell)

            if (x - CELL_SIZE, y) not in wall_set:
                self.penup()
                self.goto(x - half_cell, y - half_cell)
                self.pendown()
                self.goto(x - half_cell, y + half_cell)

            if (x + CELL_SIZE, y) not in wall_set:
                self.penup()
                self.goto(x + half_cell, y - half_cell)
                self.pendown()
                self.goto(x + half_cell, y + half_cell)


class Pellet(Pen):
    def __init__(self, pellets):
        super().__init__()
        self.shape("circle")
        self.shapesize(0.3, 0.3)
        self.pencolor("white")
        self.fillcolor("gold")
        self.stamps = {}
        self.pellets = pellets

    def draw(self):
        for x, y in self.pellets:
            self.goto(x, y)
            stamp_id = self.stamp()
            self.stamps[(x, y)] = stamp_id


class UI_Pen(Pen):
    def __init__(self):
        super().__init__()
        self.font = ("Courier", 30, "bold")

    def draw_ui_area(self):
        self.pensize(2)
        x = SCREEN_WIDTH / 2
        top_y = 0.98 * SCREEN_HEIGHT / 2
        bottom_y = top_y - 1.5 * CELL_SIZE
        self.goto(x, top_y)
        self.pendown()
        self.goto(-x, top_y)
        self.goto(-x, bottom_y)
        self.goto(x, bottom_y)
        self.goto(x, top_y)

    def write_score(self, score):
        self.clear()
        msg = f"SCORE: {score}"
        self.goto(0, SCREEN_HEIGHT / 2 - 2 * CELL_SIZE)
        self.write(msg, False, "center", ("Courier", 24, "bold"))

    def write_time(self, elapsed_time):
        self.clear()
        msg = f"TIME: {round(elapsed_time, 1)}s"
        self.goto(SCREEN_WIDTH / 2 - 16, SCREEN_HEIGHT / 2 - 2 * CELL_SIZE)
        self.write(msg, False, "right", ("Courier", 24, "bold"))


def clear_game_screen(screen):
    clear_ui(screen)
    screen.clearscreen()
    import src.renderer.sprites as sprite_defs
    sprite_defs._registered = False
    sprite_defs.register_all_shapes(screen)
    screen.bgcolor(THEME["background"])
    screen.tracer(0)


def refresh_screen(screen):
    screen.update()


def init_screen():
    screen = turtle.Screen()
    from src.core.debug import install_hooks, trace
    install_hooks(screen)
    from src.renderer.sprites import register_all_shapes
    register_all_shapes(screen)
    screen.tracer(0)
    screen.title("Pacman - Kai Edition")
    screen.setup(SCREEN_WIDTH, SCREEN_HEIGHT)
    screen.bgcolor(THEME["background"])
    trace("screen initialized")
    return screen


def game_loop(screen) -> None:
    screen.update()


def show_menu(pen: turtle.Turtle, screen, text_data: list[tuple], on_select, back=None, selected_value=None):
    _show_pastel_menu(pen, screen, text_data, on_select, back=back,
                      selected_value=selected_value)
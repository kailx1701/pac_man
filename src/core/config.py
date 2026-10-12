"""
    This config.py contains all constant global variables.
        * These variables should not be changed.
        * Constant variables are noted with upper case letter.
"""

# CONSTANTS
# -----------------------------------

CELL_SIZE = 25 
SCREEN_WIDTH = CELL_SIZE * 33  
LOGIC_HEIGHT = CELL_SIZE * 28  
SCREEN_HEIGHT = LOGIC_HEIGHT + 50
GRID_ROWS = LOGIC_HEIGHT // CELL_SIZE
GRID_COLUMNS = SCREEN_WIDTH // CELL_SIZE
ROW_MARGIN = (SCREEN_WIDTH - (CELL_SIZE * GRID_COLUMNS)) / 2
COLUMN_MARGIN = (LOGIC_HEIGHT - (CELL_SIZE * GRID_ROWS)) / 2

MAZE_ROWS = GRID_ROWS - 2
MAZE_COLUMNS = GRID_COLUMNS
MAZE_START_X = (-SCREEN_WIDTH / 2) + ROW_MARGIN + CELL_SIZE / 2
MAZE_START_Y = (SCREEN_HEIGHT / 2) - COLUMN_MARGIN - (CELL_SIZE * 3 / 2) - 50

PACMAN_MOVE_SPEED = 5
PELLET_REWARD = 10
STEP_PENALTY = 1
PELLET_DENSITY = 0.35
PELLET_MIN = 15
SKILL_PELLET_INTERVAL = 10
SKILL_LIFETIME_TICKS = 600
SKILL_MAX_CHARGES = 3
SKILL_COOLDOWN_TICKS = 30
GHOST_RESPAWN_TICKS = 480
GHOST_SPAWN_INVULN_TICKS = 60
GHOST_SPEED = 5.0
GHOST_SPRITE_MODE = "vector"
SKILL_SCORE_PER_GHOST = 50

# MÀU NỀN MENU GỐC VÀ CÁC THÀNH PHẦN GIAO DIỆN
THEME = {
    "background": "#1b1d36", "text": "#f4f0ff", "dark_text": "#25243b",
    "mint": "#A8E6CF", "peach": "#FFD3B6", "pink": "#FFAAA5",
    "lavender": "#CBAACB", "lemon": "#FFF1A8", "sky": "#A0D2EB",
    "muted": "#77798c", "shadow": "#111326",
}

# MÀU RIÊNG CHO MÀN HÌNH GAMEPLAY
GAMEPLAY_BG = "#0a0f1d"       # Nền xanh đen navy trầm sâu cho mê cung
WALL_COLOR = "#2d68ff"        # Màu tường xanh dương cổ điển sắc nét

BACK_TO_FIRST = False
DEFAULT_GHOST_COUNT = 2
NUM_GHOSTS = 2
GHOST_MOVE_EVERY = 1          # 1 = ma nhanh bằng Pacman, 2 = chậm bằng nửa, 3 = chậm bằng 1/3
MAX_FOOD_MULTIFOOD = 12
MINIMAX_DEPTH = 3
DEBUG_TRACE = True
BACK_MARGIN_LEFT = 70
BACK_MARGIN_BOTTOM = 50
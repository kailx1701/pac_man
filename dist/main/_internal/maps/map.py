import random
import sys
from pathlib import Path
from src.core.config import *

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.config import (CELL_SIZE, MAZE_ROWS, MAZE_COLUMNS,
                             MAZE_START_X, MAZE_START_Y)


def pad_map(core_map: list[str]) -> list[str]:
    """Tự động căn giữa và đệm khoảng trắng để mọi bản đồ đều đạt kích thước chuẩn (26x33)"""
    core_rows = len(core_map)
    core_cols = len(core_map[0])
    
    top_pad = (MAZE_ROWS - core_rows) // 2
    bottom_pad = MAZE_ROWS - core_rows - top_pad
    left_pad = (MAZE_COLUMNS - core_cols) // 2
    right_pad = MAZE_COLUMNS - core_cols - left_pad
    
    empty_row = " " * MAZE_COLUMNS
    padded = [empty_row] * top_pad
    
    for row in core_map:
        padded.append(" " * left_pad + row + " " * right_pad)
        
    padded.extend([empty_row] * bottom_pad)
    return padded

# TINY MAPS
tiny_1 = pad_map([
    "XXXXXXXXXXXXXXX",
    "X.            X",
    "X XXX XXX XXX X",
    "X X X X X X X X",
    "X             X",
    "X XXX XXX XXX X",
    "X X X X X X X X",
    "X      .      X",
    "X XXX XXX XXX X",
    "X            .X",  # Hạt duy nhất nằm ở góc dưới bên phải
    "XXXXXXXXXXXXXXX"
])

tiny_2 = pad_map([
    "XXXXXXXXXXXXXXX",
    "X.            X",
    "X XXX X X XXX X",
    "X   X X.X X   X",
    "XXX X X X X XXX",
    "X             X",
    "XXX XXXXXXX XXX",
    "X             X",
    "X XXX X X XXX X",
    "X            .X",  # Hạt duy nhất nằm ở góc dưới bên phải
    "XXXXXXXXXXXXXXX"
])

tiny_3 = pad_map([
    "XXXXXXXXXXXXXXX",
    "X.            X",
    "X X XXXXXXX X X",
    "X X    .    X X",
    "X X XXXXXXX X X",
    "X             X",
    "X X XXXXXXX X X",
    "X X         X X",
    "X X XXXXXXX X X",
    "X            .X",  # Hạt duy nhất nằm ở góc dưới bên phải
    "XXXXXXXXXXXXXXX"
])

tiny_4 = pad_map([
    "XXXXXXXXXXXXXXX",
    "X.            X",
    "X XXXXX XXXXX X",
    "X             X",
    "X XX XXXXX XX X",
    "X XX       XX X",
    "X XX XXXXX XX X",
    "X    .        X",
    "X XXXXX XXXXX X",
    "X            .X",  # Hạt duy nhất nằm ở góc dưới bên phải
    "XXXXXXXXXXXXXXX"
])

tiny_5 = pad_map([
    "XXXXXXXXXXXXXXX",
    "X.            X",
    "X X XXXXXXX X X",
    "X X X     X X X",
    "X X X XXX X X X",
    "X X X     X X X",
    "X X X XXX X X X",
    "X X X     X X X",
    "X X XXXXXXX X X",
    "X  .         .X",  # Hạt duy nhất nằm ở góc dưới bên phải
    "XXXXXXXXXXXXXXX"
])

# MEDIUM MAPS
medium_1 = pad_map([
    "XXXXXXXXXXXXXXXXXXXXX",
    "X...................X",
    "X.XXX.XXXXX.XXXXX.X.X",
    "X.XXX.X   X.X   X.X.X",
    "X.....XXXXX.XXXXX...X",
    "X.XXX.............X.X",
    "X.XXX.XXXXX.XXXXX.X.X",
    "X.....X   X.X   X...X",
    "X.XXX.XXXXX.XXXXX.X.X",
    "X.XXX.............X.X",
    "X.....XXXXX.XXXXX...X",
    "X.XXX.X   X.X   X.X.X",
    "X.XXX.XXXXX.XXXXX.X.X",
    "X...................X",
    "XXXXXXXXXXXXXXXXXXXXX"
])

medium_2 = pad_map([
    "XXXXXXXXXXXXXXXXXXXXX",
    "X...................X",
    "X.XXXXXXX.X.XXXXXXX.X",
    "X.......X.X.X.......X",
    "X.XXXXX.X.X.X.XXXXX.X",
    "X.......X.X.X.......X",
    "X.XXXXX.X.X.X.XXXXX.X",
    "X.......X.X.X.......X",
    "X.XXXXX.X.X.X.XXXXX.X",
    "X.......X.X.X.......X",
    "X.XXXXX.X.X.X.XXXXX.X",
    "X.......X.X.X.......X",
    "X.XXXXXXX.X.XXXXXXX.X",
    "X...................X",
    "XXXXXXXXXXXXXXXXXXXXX"
])

medium_3 = pad_map([
    "XXXXXXXXXXXXXXXXXXXXX",
    "X...................X",
    "X.X.XXXXXXX.XXXXXXX.X",
    "X.X.X.............X.X",
    "X.X.X.XXXXXXXXXXX.X.X",
    "X.X.X.X.........X.X.X",
    "X.X.X.X.XXXXXXX.X.X.X",
    "X.X.X.X.........X.X.X",
    "X.X.X.X.XXXXXXX.X.X.X",
    "X.X.X.X.........X.X.X",
    "X.X.X.XXXXXXXXXXX.X.X",
    "X.X.X.............X.X",
    "X.X.XXXXXXX.XXXXXXX.X",
    "X...................X",
    "XXXXXXXXXXXXXXXXXXXXX"
])

medium_4 = pad_map([
    "XXXXXXXXXXXXXXXXXXXXX",
    "X...................X",
    "X.XXXXX.XXXXX.XXXXX.X",
    "X.X...X.X...X.X...X.X",
    "X.X.X.X.X.X.X.X.X.X.X",
    "X.X...X.X...X.X...X.X",
    "X.XXXXX.XXXXX.XXXXX.X",
    "X...................X",
    "X.XXXXX.XXXXX.XXXXX.X",
    "X.X...X.X...X.X...X.X",
    "X.X.X.X.X.X.X.X.X.X.X",
    "X.X...X.X...X.X...X.X",
    "X.XXXXX.XXXXX.XXXXX.X",
    "X...................X",
    "XXXXXXXXXXXXXXXXXXXXX"
])

medium_5 = pad_map([
    "XXXXXXXXXXXXXXXXXXXXX",
    "X...................X",
    "X.XXX.X.X.X.X.X.XXX.X",
    "X.XXX.X.X.X.X.X.XXX.X",
    "X...................X",
    "X.X.XXXXXXX.XXXXXXX.X",
    "X.X.X.....X.X.....X.X",
    "X.X.XXXXXXX.XXXXXXX.X",
    "X.X.X.....X.X.....X.X",
    "X.X.XXXXXXX.XXXXXXX.X",
    "X...................X",
    "X.XXX.X.X.X.X.X.XXX.X",
    "X.XXX.X.X.X.X.X.XXX.X",
    "X...................X",
    "XXXXXXXXXXXXXXXXXXXXX"
])


# LARGE MAPS
big_1 = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X...............................X",
    "X.XXX.XXX.XXXXXX.XXXXXX.XXX.XXX.X",
    "X.X X.X X.X    X.X    X.X X.X X.X",
    "X.XXX.X X.XXXXXX.XXXXXX.X X.XXX.X",
    "X.....XXX.X....X.X....X.XXX.....X",
    "XXXXX.......XX.X.X.XX.......XXXXX",
    "X.....XXXXX...........XXXXX.....X",
    "X.XXX.......XXXXXXXXX.......XXX.X",
    "X.....XXXXX...........XXXXX.....X",
    "X.XXX.......XXXX.XXXX.......XXX.X",
    "X.X X.XXXXX.X  X.X  X.XXXXX.X X.X",
    "X.X X.X   X.X  X.X  X.X   X.X X.X",
    "X.X X.X   X.X  X.X  X.X   X.X X.X",
    "X.X X.XXXXX.X  X.X  X.XXXXX.X X.X",
    "X.XXX.......XXXX.XXXX.......XXX.X",
    "X.....XXXXX...........XXXXX.....X",
    "X.XXX.......XXXXXXXXX.......XXX.X",
    "X.....XXXXX...........XXXXX.....X",
    "XXXXX.......XX.X.X.XX.......XXXXX",
    "X.....XXX.X....X.X....X.XXX.....X",
    "X.XXX.X X.XXXXXX.XXXXXX.X X.XXX.X",
    "X.X X.X X.X    X.X    X.X X.X X.X",
    "X.XXX.XXX.XXXXXX.XXXXXX.XXX.XXX.X",
    "X...............................X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

big_2 = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X...............................X",
    "X.XXXXXXX.XXXXXXXXXXXXX.XXXXXXX.X",
    "X...............................X",
    "X.XXXXXXX.XXXXXXXXXXXXX.XXXXXXX.X",
    "X...............................X",
    "X.........X.X.XXXXX.X.X.........X",
    "X.X.....X.X.X.X...X.X.X.X.....X.X",
    "X.XXXXXXX.X.X.......X.X.XXXXXXX.X",
    "X...............................X",
    "X...............................X",
    "X.XXX..X..X..XX...XX..X..X.X..X.X",
    "X.X  X.X..X.X..X.X..X.XX.X.X..X.X",
    "X.X  X.X..X.X....X..X.X.XX.XXXX.X",
    "X.X  X.X..X.X..X.X..X.X..X.X..X.X",
    "X.XXX...XX...XX..X..X.X..X.X..X.X",
    "X...............................X",
    "X.XXXXXXX.X.X.X...X.X.X.XXXXXXX.X",
    "X.X.....X.X.X.X...X.X.X.X.....X.X",
    "X.X.....X.X.X.XXXXX.X.X.X.....X.X",
    "X...............................X",
    "X.XXXXXXX.XXXXXXXXXXXXX.XXXXXXX.X",
    "X...............................X",
    "X.XXXXXXX.XXXXXXXXXXXXX.XXXXXXX.X",
    "X...............................X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

big_3 = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X...............................X",
    "X.XXXXXXX.XXXXXXXXXXXXX.XXXXXXX.X",
    "X.X     X.X...........X.X     X.X",
    "X.XXXXXXX.X...........X.XXXXXXX.X",
    "X...............................X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X.X     X.X X.X   X.X X.X     X.X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X...............................X",
    "X...............................X",
    "X.XXX..X..X.X..X..XX..X..X.X..X.X",
    "X.X  X.X..X.X..X.X  X.XX.X.X..X.X",
    "X.X  X.X..X..XX..XXXX.X.XX.XXXX.X",
    "X.X  X.X..X..X...X..X.X..X.X..X.X",
    "X.XXX...XX...X...X..X.X..X.X..X.X",
    "X...............................X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X.X     X.X X.X   X.X X.X     X.X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X...............................X",
    "X.XXXXXXX.X...........X.XXXXXXX.X",
    "X.X     X.X...........X.X     X.X",
    "X.XXXXXXX.XXXXXXXXXXXXX.XXXXXXX.X",
    "X...............................X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

big_4 = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X...............................X",
    "X.XXXXXXX.XXXXXXXXXXXXX.XXXXXXX.X",
    "X.X     X.X...........X.X     X.X",
    "X.XXXXXXX.X...........X.XXXXXXX.X",
    "X...............................X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X.X     X.X X.X   X.X X.X     X.X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X...............................X",
    "X...............................X",
    "X..X...X..X...X....X....XXXXX...X",
    "X..X..X...X...X...X X.....X.....X",
    "X..XXX....XXXXX..XXXXX....X.....X",
    "X..X..X...X...X..X...X....X.....X",
    "X..X...X..X...X..X...X..XXXXX...X",
    "X...............................X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X.X     X.X X.X   X.X X.X     X.X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X...............................X",
    "X.XXXXXXX.X...........X.XXXXXXX.X",
    "X.X     X.X...........X.X     X.X",
    "X.XXXXXXX.XXXXXXXXXXXXX.XXXXXXX.X",
    "X...............................X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

big_5 = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X...............................X",
    "X.XXXXXXX.XXXXXXXXXXXXX.XXXXXXX.X",
    "X.X     X.X...........X.X     X.X",
    "X.XXXXXXX.X...........X.XXXXXXX.X",
    "X...............................X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X.X     X.X X.X   X.X X.X     X.X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X...............................X",
    "X...............................X",
    "X.X..X.XXX.XXX.XXX.XXX.X..X.X.X.X",
    "X.XX.X.X...X X.X...X X.X..X.X.X.X",
    "X.X.XX.X.X.X X.X...XXX.XX.X.XXX.X",
    "X.X..X.X.X.X X.X...X.X.X.XX.X.X.X",
    "X.X..X.XXX.XXX.XXX.X.X.X..X.X.X.X",
    "X...............................X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X.X     X.X X.X   X.X X.X     X.X",
    "X.XXXXXXX.XXX.XXXXX.XXX.XXXXXXX.X",
    "X...............................X",
    "X.XXXXXXX.X...........X.XXXXXXX.X",
    "X.X     X.X...........X.X     X.X",
    "X.XXXXXXX.XXXXXXXXXXXXX.XXXXXXX.X",
    "X...............................X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

TINY_MAPS = [tiny_1, tiny_2, tiny_3, tiny_4, tiny_5]
MEDIUM_MAPS = [medium_1, medium_2, medium_3, medium_4, medium_5]
# BIG_MAPS = [big_1, big_2, big_3, big_4, big_5]
BIG_MAPS = [big_5]


MAP_LIST = TINY_MAPS + MEDIUM_MAPS + BIG_MAPS


TINY_SIZE = (11,15)
MEDIUM_SIZE = (15,21)
BIG_SIZE = (26,33)


def create_ghosthouse(grid: list[str], ghost_num:int = 4) -> list[str]:
    height = len(grid)
    width = len(grid[0])
    temp_grid = [list(row) for row in grid]
    if 0 >= ghost_num > 6:
        raise ValueError("Invalide number of ghosts")
    
    house_width, house_height = 3, 2
    left = (width - house_width) // 2
    top = (height - house_height) // 2
    right = left + house_width - 1
    bottom = top + house_height - 1
    door = left + house_width // 2

    count_ghost = 1
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            if count_ghost <= ghost_num:
                temp_grid[y][x] = "G" # Ghost spawnpoints
                count_ghost += 1
            else:
                temp_grid[y][x] = " "

    for y in range(top - 1, bottom + 2):
        for x in range(left - 1, right + 2):
            is_outer_ring = y in (top - 1, bottom + 1) or x in (left - 1, right + 1)
            if is_outer_ring:
                temp_grid[y][x] = "X"

    for y in range(top - 2, bottom + 3):
        for x in range(left - 2, right + 3):
            is_outer_ring = y in (top - 2, bottom + 2) or x in (left - 2, right + 2)
            if is_outer_ring:
                temp_grid[y][x] = "."

    temp_grid[bottom + 1][door] = " "
    result = ["".join(row) for row in temp_grid]
    return result

def map_generator(height: int, width: int, ghost: bool = False) -> list[str] :
    """
        map_generator:

        input:
        height : height of the map (max 26)
        width : width of the map ((max 33)
        ghost : True if map have ghost, False if not

        output: (list[str]) map grid
        
        this map_generator using randomized DFS to create tunnels
    """
    if height < 3 or width < 3 or height > 26 or width > 33:
        raise ValueError("Invalid map size")

    grid = [["X" for _ in range(width)] for __ in range(height)]

    direction = [(2,0),(-2,0),(0,2),(0,-2)]
    def carve(x,y):
        grid[y][x] = "."
        random.shuffle(direction)
        for dx,dy in direction:
            ny = y + dy
            nx = x + dx
            if 1 <= nx < width - 1 and 1 <= ny < height - 1:
                if grid[ny][nx] == "X":
                    grid[y + dy // 2][x + dx // 2] = "."
                    carve(nx,ny)
    carve(1,1)

    grid = ["".join(row) for row in grid]
    if ghost:
        grid = create_ghosthouse(grid, ghost_num = NUM_GHOSTS)

    return pad_map(grid)

def extract_map_data(map: list[str]) -> dict:
    wall = []
    pellet = [] 
    start = None 
    ghost = []
    data = dict()
    map_width = len(map[0])
    map_height = len(map)

    for row in range(map_height):
        for col in range(map_width):
            symbol = map[row][col]
            if symbol == "X":
                wall.append((row,col))
            elif symbol == ".":
                pellet.append((row,col))
            elif symbol == "S":
                start = (row,col)
            elif symbol == "G":
                ghost.append((row,col))

    data["wall"] = wall
    data["pellet"] = pellet
    data["start"] = start
    data["ghost"] = ghost
    return data


class Map:
    def __init__(self, auto_generate: bool = False, size: tuple[int,int] = TINY_SIZE, ghost: bool = False):
        if auto_generate:
            self.grid = map_generator(*size, ghost)
        else:
            if size == TINY_SIZE:
                self.grid = random.choice(TINY_MAPS)
            if size == MEDIUM_SIZE:
                self.grid = random.choice(MEDIUM_MAPS)
            if size == BIG_SIZE:
                self.grid = random.choice(BIG_MAPS)

        if ghost:
            self.grid = create_ghosthouse(self.grid, ghost_num = NUM_GHOSTS)
    
    def calculate_maze_renderer_data(self):
        walls = []
        pellets = []
        
        for row in range(MAZE_ROWS):
            for col in range(MAZE_COLUMNS):
                character = self.grid[row][col]
                character_x = MAZE_START_X + CELL_SIZE * col
                character_y = MAZE_START_Y - CELL_SIZE * row
                
                if character == "X":
                    walls.append((character_x, character_y))
                elif character == ".":
                    pellets.append((character_x, character_y))
        return walls, pellets

    def is_wall(self, x, y):
        return self.grid[x][y] == "X"

if __name__ == "__main__":

    # test map_generator()
    a = map_generator(*TINY_SIZE, ghost=True)
    for row in a:
        print(row)
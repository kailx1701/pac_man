from src.core.gameloop import *

def main() -> None:
    gameSetup = GameSetup()
    gameState = GameState(gameSetup)
    startGame(gameSetup, gameState)
    gameSetup.screen.mainloop()
if  __name__ == "__main__":
    main()


"""import turtle
from src.interaction.interaction import *
from src.renderer.renderer import Wall, Pellet, UI_Pen, init_screen
from src.player.actors import *
from src.player.ghosts import *
from maps.map import map_1
from src.core.config import CELL_SIZE, MAZE_START_X, MAZE_START_Y
from src.core.problem import SingleFoodProblem, MultiFood
from src.core.heuristic import manhattan, multi_food_heuristic
from src.core.search import a_star

AUTO_MODE = True    
DELTA = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}


def cell_to_pixel(cell):
    row, col = cell
    return MAZE_START_X + CELL_SIZE * col, MAZE_START_Y - CELL_SIZE * row


def path_to_cells(start, path):
    cells = [start]
    for action in path:
        dr, dc = DELTA[action]
        r, c = cells[-1]
        cells.append((r + dr, c + dc))
    return cells


def follow_path(screen, pacman, cells, delay=80):
    def step(i):
        if i >= len(cells):
            return
        x, y = cell_to_pixel(cells[i])
        pacman.goto(x, y)
        screen.update()
        screen.ontimer(lambda: step(i + 1), delay)
    step(0)

def game_loop(screen, pacman, score_pen, ui_pen, pellet_pen) -> None:
    score_pen.write_score(pacman.score)
    pacman.move()
    screen.update()
    screen.ontimer (lambda: game_loop (
        screen, 
        pacman,
        score_pen,
        ui_pen,
        pellet_pen), 
        1000 // 60
    )

def main() -> None:
    screen = init_screen()
    wall_pen = Wall()
    pellet_pen = Pellet()
    ui_pen = UI_Pen()
    score_pen = UI_Pen()

    ghost_start_coor =  pellet_pen.pellets[0]
    ghost_start_x = ghost_start_coor[0]
    ghost_start_y = ghost_start_coor[1]
    ghost = Ghost()
    ghost.goto (ghost_start_x, ghost_start_y)
   

    wall_pen.draw()
    pellet_pen.draw()
    ui_pen.draw_ui_area() 
    if AUTO_MODE:
        problem = MultiFood(map_1, max_foods=30)
        print("start =", problem.start_pos)
        result = a_star(problem, multi_food_heuristic)

        print(result)                    
        if result["is_solved"]:
            cells = path_to_cells(problem.start_pos, result["path"])
            follow_path(screen, ghost, cells)
    else:
        bind_controls(screen, ghost)
        game_loop(screen, ghost, score_pen, ui_pen, pellet_pen)
    screen.mainloop()
if  __name__ == "__main__":
    main()"""

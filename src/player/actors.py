import turtle
from enum import Enum
from src.core.config import *
from src.core.helper import pixel_to_cell

class Direction(Enum):
    right = 0
    left = 180
    up = 90
    down = -90


class Actor(turtle.Turtle):
    def __init__(self):
        super().__init__()
        self.hideturtle()
        self.penup()
        self.speed(0)


class Player(Actor):
    def __init__(self):
        super().__init__()
        self.shape("pacman_idle")
        self.shapesize(1.0, 1.0)
        self.pencolor("white")
        self.fillcolor("gold")
        self.state = "stop"
        self.move_speed = PACMAN_MOVE_SPEED
        self.score = 0
        self.direction = Direction.right
        self.anim_tick = 0

    def move(self):
        if self.state != "stop":
            self.anim_tick += 1
            frame = (0, 1, 2, 1)[(self.anim_tick // 4) % 4]
            self.shape(f"pacman_{frame}")
            self.setheading(self.direction.value)
            self.forward(self.move_speed)
            if round(self.ycor()) > SCREEN_HEIGHT / 2 - 2 * CELL_SIZE:
                self.sety(-SCREEN_HEIGHT / 2)
            elif round(self.ycor()) < -SCREEN_HEIGHT / 2:
                self.sety(SCREEN_HEIGHT / 2 - 2 * CELL_SIZE)
            elif round(self.xcor()) < -SCREEN_WIDTH / 2:
                self.setx(SCREEN_WIDTH / 2)
            elif round(self.xcor()) > SCREEN_WIDTH / 2:
                self.setx(-SCREEN_WIDTH / 2)

    def turn(self, direction: Direction) -> None:
        self.direction = direction
        self.setheading(direction.value)
        self.state = "move"

    def pos_on_map(self) -> tuple[int, int]:
        x_screen = self.xcor()
        y_screen = self.ycor()
        x = round((x_screen - MAZE_START_X) / CELL_SIZE)
        y = round((MAZE_START_Y - y_screen) / CELL_SIZE)
        return x, y

    def check_wall_collision(self, grid: list[str]) -> None:
        """
        Kiểm tra va chạm tường và cập nhật vị trí cho Pacman.
        """
        x_screen = round(self.xcor())
        y_screen = round(self.ycor())
        y, x = pixel_to_cell(self.xcor(), self.ycor())
        direction = self.direction
        directions = {
            Direction.right: (1, 0),
            Direction.left: (-1, 0),
            Direction.up: (0, 1),
            Direction.down: (0, -1),
        }
        move_x, move_y = directions[direction]

        for row in range(max(0, y - 2), min(MAZE_ROWS, y + 3)):
            for col in range(max(0, x - 2), min(MAZE_COLUMNS, x + 3)):
                if grid[row][col] == "X":
                    wall_x = MAZE_START_X + CELL_SIZE * col
                    wall_y = MAZE_START_Y - CELL_SIZE * row

                    offset_x = wall_x - x_screen
                    offset_y = wall_y - y_screen

                    ahead = offset_x * move_x + offset_y * move_y
                    side = abs(offset_x * move_y - offset_y * move_x)

                    if 0 < ahead < CELL_SIZE and side <= CELL_SIZE * 0.75:
                        if direction in (Direction.left, Direction.right):
                            self.setx(wall_x - move_x * CELL_SIZE)
                        else:
                            self.sety(wall_y - move_y * CELL_SIZE)
                        self.state = "stop"
                        break
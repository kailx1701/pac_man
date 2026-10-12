import turtle as t
from src.player.actors import *
"""
    This interaction.py was implemented by Duy Anh
    * This file contains declartion and implementation of functions needed for interaction
"""

def bind_controls(screen: t._Screen, player: Player) -> None:
    screen.listen()
    screen.onkeypress(lambda: player.turn(Direction.right), key="Right")
    screen.onkeypress(lambda: player.turn(Direction.left), key="Left")
    screen.onkeypress(lambda: player.turn(Direction.up), key="Up")
    screen.onkeypress(lambda: player.turn(Direction.down), key="Down")
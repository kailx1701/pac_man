import math
import turtle
from src.renderer.geometry import register_all

_registered = False


def register_all_shapes(screen):
    global _registered
    if _registered:
        return
    register_all(screen, turtle.Shape)
    star = []
    for index in range(10):
        radius = 10 if index % 2 == 0 else 4
        angle = math.radians(index * 36 - 90)
        star.append((radius * math.cos(angle), radius * math.sin(angle)))
    skill = turtle.Shape("compound")
    skill.addcomponent(star, "gold", "red")
    screen.register_shape("skill_item", skill)
    _registered = True

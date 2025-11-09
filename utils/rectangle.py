from .math_utils import MathUtils as mu

class Rectangle:
    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, px: float, py: float) -> bool:
        return (self.x <= px <= self.x + self.width) and (self.y <= py <= self.y + self.height)

    def limit(self, px: float, py:float) -> tuple[float, float]:
        return (
            mu.limit(self.x, px, self.x + self.width),
            mu.limit(self.y, py, self.y + self.height)
        )
class BulletInfo:
    def __init__(self, 
                 id: int, 
                 power: float,
                 heading: float,
                 speed: float,
                 x: float,
                 y: float
                ) -> None:
        self.id: int = id
        self.power: float = power
        self.heading: float = heading
        self.speed: float = speed
        self.x: float = x
        self.y: float = y
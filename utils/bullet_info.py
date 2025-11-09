class BulletInfo:
    def __init__(self,
                 owner_id: int,
                 position: tuple[float, float],
                 fire_time: int,
                 power: float,
                 direction: float,
                 speed: float,
                ) -> None:
        self.owner_id = owner_id
        self.position = position
        self.fire_time = fire_time
        self.power = power
        self.direction = direction
        self.speed = speed

    def on_tick_update(self) -> None:
        pass
from .bullet_info import BulletInfo

class WaveBullet:
    def __init__(self, 
                 owner_id: int,
                 position: tuple[float, float],
                 fire_time: int,
                 power: float,
                 direction: float,
                 speed: float,
                 distance: float = 0
                ) -> None:
        self.bullet_info = BulletInfo(
            owner_id,
            position,
            fire_time,
            power,
            direction,
            speed,
        )
        self.distance = distance
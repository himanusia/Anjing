import asyncio

from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent
import math

# ------------------------------------------------------------------
# Anjing
# ------------------------------------------------------------------
"""
===== RADAR =====
v1.0
- kosongan
v1.1
- radar 360
v1.2
- radar lock
v1.3
- conditional radar lock

===== FIRE =====
v2.0
- fire
v2.1
- fire ke scanned bot / head-on targeting
v2.2.1
- precise linear targeting
v2.2.2
- approx linear targeting (singkat)

"""
# ------------------------------------------------------------------

class Anjing(Bot):
    async def run(self) -> None:
        self.set_turn_radar_left(float('inf'))
        self.set_adjust_radar_for_gun_turn(True)

    def _prediksi_sudut(self,
        xm: float, ym: float, enemy_deg: float, enemy_speed: float,
        xk: float, yk: float, bullet_speed: float
    ):
        los_rad = math.atan2(ym - yk, xm - xk)
        fire_dir = los_rad + enemy_speed * math.sin(math.radians(enemy_deg) - los_rad) / bullet_speed
        return self.calc_gun_bearing(math.degrees(fire_dir))

    async def on_scanned_bot(self, scanned_bot_event: ScannedBotEvent) -> None:
        fire_power = 1
        sudut = self._prediksi_sudut(
            scanned_bot_event.x, scanned_bot_event.y, scanned_bot_event.direction, scanned_bot_event.speed,
            self.get_x(), self.get_y(), self.calc_bullet_speed(fire_power)
        )
        self.set_turn_gun_left(sudut)
        await self.fire(1)

        if (scanned_bot_event.energy < 100):
            sudut = self.normalize_relative_angle(self.radar_bearing_to(scanned_bot_event.x, scanned_bot_event.y))
            self.set_turn_radar_left(float('inf') * sudut)

async def main() -> None:
    bot = Anjing()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())

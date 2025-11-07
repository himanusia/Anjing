import asyncio

from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent
import math

# ------------------------------------------------------------------
# Anjing
# ------------------------------------------------------------------

class Anjing(Bot):
    async def run(self) -> None:
        self.old_enemy_dir: float = 0
        
        self.set_turn_radar_left(float('inf'))
        self.set_adjust_radar_for_gun_turn(True)
        self.set_adjust_radar_for_body_turn(True)
        self.set_adjust_gun_for_body_turn(True)

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

        self.set_turn_left((self.bearing_to(scanned_bot_event.x, scanned_bot_event.y)))
        self.set_forward(self.distance_to(scanned_bot_event.x, scanned_bot_event.y))

    def _prediksi_sudut(self,
        xm: float, ym: float, enemy_deg: float, enemy_speed: float,
        xk: float, yk: float, bullet_speed: float
    ) -> float:
        new_enemy_dir = math.radians(enemy_deg)
        dir_change = new_enemy_dir - self.old_enemy_dir
        self.old_enemy_dir = new_enemy_dir

        t, pred_x, pred_y = 0, xm, ym
        while (t * bullet_speed < math.dist((pred_x, pred_y), (xk, yk))):
            pred_x += math.cos(new_enemy_dir) * enemy_speed
            pred_y += math.sin(new_enemy_dir) * enemy_speed
            new_enemy_dir += dir_change
            t += 1

        return self.gun_bearing_to(pred_x, pred_y)

async def main() -> None:
    bot = Anjing()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())

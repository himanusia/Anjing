import asyncio

from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent, TickEvent

import numpy as np

# ------------------------------------------------------------------
# Anjing
# ------------------------------------------------------------------

class Anjing(Bot):
    MOVE_WALL_MARGIN: float = 25
    GUN_FACTOR: float = 3.0

    async def run(self) -> None:        
        self.move_dir: bool  = True
        self.enemy_distance: float = float('inf')
        self.old_enemy_dir: float = 0
        self.old_enemy_id: int = 0
        self.old_enemy_energy: float = 0
        self.arena_diagonal: float = np.hypot(self.get_arena_width(), self.get_arena_height())
        self.sag_dir: int = 1
        
        self.set_turn_radar_left(float('inf'))
        self.set_adjust_radar_for_gun_turn(True)
        self.set_adjust_radar_for_body_turn(True)
        self.set_adjust_gun_for_body_turn(True)

    async def on_tick(self, tick_event: TickEvent) -> None:
        del tick_event

        if self.get_enemy_count() == 1:
            return

        x = Anjing.MOVE_WALL_MARGIN + self.enemy_distance / 3
        y = Anjing.MOVE_WALL_MARGIN
        
        if self.distance_remaining == 0:
            self.move_dir = not self.move_dir
            
        if self.move_dir:
            x, y = y, x
            
        if self.get_x() > self.get_arena_width() / 2:
            x = self.get_arena_width() - x
            
        if self.get_y() > self.get_arena_height() / 2:
            y = self.get_arena_height() - y
            
        turn = np.radians(self.bearing_to(x, y))
        self.set_turn_left(np.degrees(np.tan(turn)))
        self.set_forward(self.distance_to(x, y) * np.cos(turn))

    async def on_scanned_bot(self, scanned_bot_event: ScannedBotEvent) -> None:
        self.enemy_distance = self.distance_to(scanned_bot_event.x, scanned_bot_event.y)

        fire_power = max(0.1, Anjing.GUN_FACTOR * scanned_bot_event.energy / self.enemy_distance)
        sudut = self._prediksi_sudut(
            scanned_bot_event.x, scanned_bot_event.y, scanned_bot_event.direction, scanned_bot_event.speed,
            self.get_x(), self.get_y(), self.calc_bullet_speed(fire_power)
        )
        self.set_turn_gun_left(sudut)
        await self.fire(1)

        if self.get_gun_heat() < 0.7:
            sudut = self.normalize_relative_angle(self.radar_bearing_to(scanned_bot_event.x, scanned_bot_event.y))
            self.set_turn_radar_left(float('inf') * sudut)

        energy_drop = self.old_enemy_energy - scanned_bot_event.energy
        if 0.1 <= energy_drop <= 3 and \
            self.get_enemy_count() == 1 and \
            scanned_bot_event.scanned_bot_id == self.old_enemy_id and \
            self.turn_remaining == 0:

            distance = (3 + energy_drop * 2) * 8
            direction = self.bearing_to(scanned_bot_event.x, scanned_bot_event.y) \
                        + (90 - 15 * self.enemy_distance / self.arena_diagonal) * self.sag_dir
            to_x = self.get_x() + np.cos(np.radians(direction)) * distance
            to_y = self.get_y() + np.sin(np.radians(direction)) * distance
            if (to_x < Anjing.MOVE_WALL_MARGIN or to_x > self.get_arena_width() - Anjing.MOVE_WALL_MARGIN or
                to_y < Anjing.MOVE_WALL_MARGIN or to_y > self.get_arena_height() - Anjing.MOVE_WALL_MARGIN):
                self.sag_dir *= -1

            turn = np.radians(self.bearing_to(scanned_bot_event.x, scanned_bot_event.y) \
                        + (90 - 15 * self.enemy_distance / self.arena_diagonal) * self.sag_dir)
            self.set_turn_left(self.normalize_relative_angle(np.degrees(np.tan(turn))))
            self.set_forward(distance * np.sign(np.cos(turn)))
        self.old_enemy_id = scanned_bot_event.scanned_bot_id
        self.old_enemy_energy = scanned_bot_event.energy

    def _prediksi_sudut(self,
        xm: float, ym: float, enemy_deg: float, enemy_speed: float,
        xk: float, yk: float, bullet_speed: float
    ) -> float:
        new_enemy_dir = np.radians(enemy_deg)
        dir_change = new_enemy_dir - self.old_enemy_dir
        self.old_enemy_dir = new_enemy_dir

        t, pred_x, pred_y = 0, xm, ym
        while (t * bullet_speed < np.hypot((pred_x - xk), (pred_y - yk))):
            new_enemy_dir = self.normalize_relative_angle(new_enemy_dir + dir_change)
            pred_x += np.cos(new_enemy_dir) * enemy_speed
            pred_y += np.sin(new_enemy_dir) * enemy_speed
            t += 1
        
        return self.gun_bearing_to(pred_x, pred_y)

async def main() -> None:
    bot = Anjing()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())

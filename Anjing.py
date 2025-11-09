import asyncio

from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import (ScannedBotEvent, 
                                                 BotDeathEvent, 
                                                 BulletHitBotEvent, 
                                                 BulletHitBulletEvent, 
                                                 BulletHitWallEvent, 
                                                 BulletFiredEvent, 
                                                 SkippedTurnEvent
                                                )
from robocode_tank_royale.bot_api.graphics.color import Color

import numpy as np

from utils import EnemyInfo, BulletInfo

# ------------------------------------------------------------------
# Anjing
# ------------------------------------------------------------------

class Anjing(Bot):
    MOVE_WALL_MARGIN: float = 25
    GUN_FACTOR: float = 3.0

    def __init__(self) -> None:
        super().__init__()
        self._arena_diagonal: float = float('inf')
        self._move_dir: bool  = True
        self._target_enemy: EnemyInfo | None = None
        self._enemy_dict: dict[int, EnemyInfo] = {}
        self._bullet_dict: dict[int, BulletInfo] = {}

        self._sag_dir: int = 1

    async def run(self) -> None:        
        self._arena_diagonal = np.hypot(self.get_arena_width(), self.get_arena_height())
        
        self.set_turn_radar_left(float('inf'))
        self.set_adjust_radar_for_gun_turn(True)
        self.set_adjust_radar_for_body_turn(True)
        self.set_adjust_gun_for_body_turn(True)

        # Reset enemy info
        self._enemy_dict = {}
        self._bullet_dict = {}
        self._target_enemy = None

        self.body_color = Color.from_rgb(0, 0, 0)
        self.radar_color = Color.from_rgb(0, 0, 0)
        self.bullet_color = Color.from_rgb(255, 127, 127)

        while self.is_running():
            await self._handle_select_target()
            await self._handle_movement()
            await self._handle_gun()
            await self._handle_radar()
            await self._handle_taunt()

            await self.go()


    async def _handle_select_target(self) -> None:
        # Select Shortest Distance Alive Target
        for enemy in self._enemy_dict.values():
            if enemy.is_alive:
                if self._target_enemy is None or enemy.distance < self._target_enemy.distance:
                    self._target_enemy = enemy


    async def _handle_movement(self) -> None:
        # Make sure we have a target
        if self._target_enemy is None:
            return
        enemy = self._target_enemy

        # Stop and Go Movement
        if self.get_enemy_count() == 1:
            energy_drop = enemy.history[-1].energy if enemy.history else enemy.energy - enemy.energy
            if 0.1 <= energy_drop <= 3 and \
                self.get_enemy_count() == 1 and \
                self.turn_remaining == 0:

                distance = (3 + energy_drop * 2) * 8
                direction = self.bearing_to(*enemy.position) \
                            + (90 - 15 * enemy.distance / self._arena_diagonal) * self._sag_dir
                to_x = self.get_x() + np.cos(np.radians(direction)) * distance
                to_y = self.get_y() + np.sin(np.radians(direction)) * distance
                if (to_x < Anjing.MOVE_WALL_MARGIN or to_x > self.get_arena_width() - Anjing.MOVE_WALL_MARGIN or
                    to_y < Anjing.MOVE_WALL_MARGIN or to_y > self.get_arena_height() - Anjing.MOVE_WALL_MARGIN):
                    self._sag_dir *= -1

                turn = np.radians(self.bearing_to(*enemy.position) \
                            + (90 - 15 * enemy.distance / self._arena_diagonal) * self._sag_dir)
                self.set_turn_left(self.normalize_relative_angle(np.degrees(np.tan(turn))))
                self.set_forward(distance * np.sign(np.cos(turn)))
                return

        # Corner Movement
        next_pos = (Anjing.MOVE_WALL_MARGIN + enemy.distance / 3, Anjing.MOVE_WALL_MARGIN)
        
        if self.distance_remaining == 0:
            self._move_dir = not self._move_dir
            
        if self._move_dir:
            next_pos = (next_pos[1], next_pos[0])
            
        if self.get_x() > self.get_arena_width() / 2:
            next_pos = (self.get_arena_width() - next_pos[0], next_pos[1])

        if self.get_y() > self.get_arena_height() / 2:
            next_pos = (next_pos[0], self.get_arena_height() - next_pos[1])

        turn = np.radians(self.bearing_to(*next_pos))
        self.set_turn_left(np.degrees(np.tan(turn)))
        self.set_forward(self.distance_to(*next_pos) * np.cos(turn))


    async def _handle_gun(self) -> None:
        # Make sure we have a target
        if self._target_enemy is None:
            return
        enemy = self._target_enemy

        # adaptive fire power
        fire_power = max(0.1, Anjing.GUN_FACTOR * enemy.energy / enemy.distance)

        if self.gun_turn_remaining == 0:
            self.set_fire(fire_power)

        # Gun Lock and Fire (called 1 tick before updating enemy info)
        if enemy.last_seen + 1 == self.get_turn_number():
            xm, ym = enemy.position
            bullet_speed = self.calc_bullet_speed(fire_power)
            new_enemy_dir = enemy.direction
            dir_change = new_enemy_dir - (enemy.history[-1].direction if enemy.history else enemy.direction)
            self._old_enemy_dir_ = new_enemy_dir

            g = self.get_graphics()
            t, pred_x, pred_y = 0, xm, ym
            while (t * bullet_speed < np.hypot((pred_x - self.get_x()), (pred_y - self.get_y()))):
                new_enemy_dir += dir_change
                pred_x += np.cos(np.radians(new_enemy_dir)) * enemy.speed
                pred_y += np.sin(np.radians(new_enemy_dir)) * enemy.speed
                
                color = Color.from_rgba(t * 8, 0, 0, t * 15)
                g.set_fill_color(color)
                g.fill_circle(pred_x, pred_y, 20)
                t += 1
            self.set_turn_gun_left(self.gun_bearing_to(pred_x, pred_y))


    async def _handle_radar(self) -> None:
        # Make sure we have a target
        if self._target_enemy is None:
            return
        enemy = self._target_enemy

        # Radar Lock (called 1 tick before updating enemy info)
        if self.get_enemy_count() == 1 or \
            (enemy.last_seen + 1 == self.get_turn_number() and self.get_gun_heat() < 0.7):
            sudut = self.normalize_relative_angle(self.radar_bearing_to(*enemy.position))
            self.set_turn_radar_left(float('inf') * sudut)


    async def _handle_taunt(self) -> None:
        turn_color = self.get_turn_number() * 5
        self.tracks_color = Color.from_rgb(turn_color % 256, turn_color % 256, 0)

        heat_color = int(100 * (1 - max(0, self.get_gun_heat())))
        self.scan_color = Color.from_rgb(heat_color, 10, 10)
        self.gun_color = Color.from_rgb(heat_color, 10, 10)
        self.turret_color = Color.from_rgb(100 - heat_color, 10, 10)


    async def on_scanned_bot(self, scanned_bot_event: ScannedBotEvent) -> None:
        if scanned_bot_event.scanned_bot_id not in self._enemy_dict:
            self._enemy_dict[scanned_bot_event.scanned_bot_id] = EnemyInfo(
                scanned_bot_event.scanned_bot_id,
                scanned_bot_event.energy,
                scanned_bot_event.direction,
                scanned_bot_event.speed,
                (scanned_bot_event.x, scanned_bot_event.y),
                scanned_bot_event.turn_number,
                self.distance_to(scanned_bot_event.x, scanned_bot_event.y)
            )
        else:
            enemy = self._enemy_dict[scanned_bot_event.scanned_bot_id]
            enemy.add_history(enemy.copy())
            enemy.set_energy(scanned_bot_event.energy)
            enemy.set_direction(scanned_bot_event.direction)
            enemy.set_speed(scanned_bot_event.speed)
            enemy.set_position((scanned_bot_event.x, scanned_bot_event.y))
            enemy.set_last_seen(scanned_bot_event.turn_number)
            enemy.set_distance(self.distance_to(scanned_bot_event.x, scanned_bot_event.y))


    async def on_bot_death(self, bot_death_event: BotDeathEvent) -> None:
        if bot_death_event.victim_id in self._enemy_dict:
            self._enemy_dict[bot_death_event.victim_id].is_alive = False
            if self._target_enemy and self._target_enemy.id == bot_death_event.victim_id:
                self._target_enemy = None


    async def on_bullet_hit_bot(self, bullet_hit_event: BulletHitBotEvent) -> None:
        del bullet_hit_event


    async def on_bullet_hit_wall(self, bullet_hit_wall_event: BulletHitWallEvent) -> None:
        del bullet_hit_wall_event


    async def on_bullet_hit_bullet(self, bullet_hit_bullet_event: BulletHitBulletEvent) -> None:
        del bullet_hit_bullet_event


    async def on_bullet_fired(self, bullet_fired_event: BulletFiredEvent) -> None:
        del bullet_fired_event


    async def on_skipped_turn(self, skipped_turn_event: SkippedTurnEvent) -> None:
        print("Skipped turn:", skipped_turn_event)


async def main() -> None:
    bot = Anjing()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())

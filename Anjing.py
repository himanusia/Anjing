import asyncio

from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import (HitByBulletEvent, 
                                                 ScannedBotEvent, 
                                                 BotDeathEvent, 
                                                 BulletHitBotEvent, 
                                                 BulletHitBulletEvent, 
                                                 BulletHitWallEvent, 
                                                 BulletFiredEvent, 
                                                 SkippedTurnEvent, 
                                                 TickEvent,
                                                )
from robocode_tank_royale.bot_api.graphics.color import Color

import numpy as np

from utils import (
                    EnemyInfo, 
                    WaveBullet,
                    MathUtils as mu,
                    Rectangle as rect,
                  )

# ------------------------------------------------------------------
# Anjing
# ------------------------------------------------------------------

class Anjing(Bot):
    MOVE_WALL_MARGIN: int = 25
    WALL_STICK: int = 160
    GUN_FACTOR: float = 3.0

    def __init__(self) -> None:
        super().__init__()
        self._arena_diagonal: float = float('inf')

        self._target_enemy: EnemyInfo | None = None
        self._enemy_dict: dict[int, EnemyInfo] = {}
        self._wave_bullet: dict[int, list[WaveBullet]] = {}


    async def run(self) -> None:
        arena_height, arena_width = self.get_arena_height(), self.get_arena_width()
        self._arena_diagonal = np.hypot(arena_height, arena_width)
        self._arena_rect = rect(
                                Anjing.MOVE_WALL_MARGIN, 
                                Anjing.MOVE_WALL_MARGIN,
                                arena_width - 2 * Anjing.MOVE_WALL_MARGIN,
                                arena_height - 2 * Anjing.MOVE_WALL_MARGIN, 
                               )

        self.set_turn_radar_left(float('inf'))
        self.set_adjust_radar_for_gun_turn(True)
        self.set_adjust_radar_for_body_turn(True)
        self.set_adjust_gun_for_body_turn(True)

        # Reset enemy info
        self._target_enemy = None
        self._enemy_dict = {}
        self._wave_bullet = {}

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
        wave_bullet = self.get_closest_surfable_wave()
        if wave_bullet is None:
            return

        danger_left, pos_left = self.check_danger(wave_bullet, -1)
        danger_right, pos_right = self.check_danger(wave_bullet, 1)

        pos = pos_left if danger_left < danger_right else pos_right
        turn = np.radians(self.bearing_to(*pos))
        self.set_turn_left(np.degrees(np.tan(turn)))
        self.set_forward(self.distance_to(*pos) * np.cos(turn))
    

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

            # g = self.get_graphics()

            t, pred_x, pred_y = 0, xm, ym
            while (t * bullet_speed < np.hypot((pred_x - self.get_x()), (pred_y - self.get_y()))):
                new_enemy_dir += dir_change
                pred_x += np.cos(np.radians(new_enemy_dir)) * enemy.speed
                pred_y += np.sin(np.radians(new_enemy_dir)) * enemy.speed
                
                # color = Color.from_rgba(t * 8, 0, 0, t * 15)
                # g.set_fill_color(color)
                # g.fill_circle(pred_x, pred_y, 20)
                t += 1

            pred_x, pred_y = self._arena_rect.limit(pred_x, pred_y)
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
            enemy = self._enemy_dict[scanned_bot_event.scanned_bot_id] = EnemyInfo(
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

        energy_drop = (enemy.history[-1].energy if enemy.history else enemy.energy) - scanned_bot_event.energy
        speed = self.calc_bullet_speed(energy_drop)

        # Detect Enemy Bullet and Log Wave Bullet
        if 0.1 <= energy_drop <= 3:
            self._wave_bullet[enemy.id] = self._wave_bullet.get(enemy.id, []) + [
                WaveBullet(
                    enemy.id,
                    enemy.history[-1].position,
                    self.get_turn_number(),
                    energy_drop,
                    mu.angle_between_points(enemy.history[-1].position, (self.get_x(), self.get_y())),
                    speed,
                    speed * 2,
                )
            ]


    async def on_bot_death(self, bot_death_event: BotDeathEvent) -> None:
        if bot_death_event.victim_id in self._enemy_dict:
            self._enemy_dict[bot_death_event.victim_id].is_alive = False
            if self._target_enemy and self._target_enemy.id == bot_death_event.victim_id:
                self._target_enemy = None


    async def on_hit_by_bullet(self, hit_by_bullet_event: HitByBulletEvent) -> None:
        if self._wave_bullet.get(hit_by_bullet_event.bullet.owner_id):
            for wave_bullet in self._wave_bullet[hit_by_bullet_event.bullet.owner_id]:
                if np.hypot(
                    self.get_x() - wave_bullet.bullet_info.position[0],
                    self.get_y() - wave_bullet.bullet_info.position[1]
                ) <= wave_bullet.distance + self.calc_bullet_speed(hit_by_bullet_event.bullet.power):
                
                    self.log_hit(wave_bullet, (hit_by_bullet_event.bullet.x, hit_by_bullet_event.bullet.y))
                    self._wave_bullet[hit_by_bullet_event.bullet.owner_id].remove(wave_bullet)
    

    async def on_bullet_hit_bot(self, bullet_hit_event: BulletHitBotEvent) -> None:
        # gausa munculin wave
        del bullet_hit_event


    async def on_bullet_hit_wall(self, bullet_hit_wall_event: BulletHitWallEvent) -> None:
        # remove wave
        del bullet_hit_wall_event


    async def on_bullet_hit_bullet(self, bullet_hit_bullet_event: BulletHitBulletEvent) -> None:
        # shielding
        del bullet_hit_bullet_event


    async def on_bullet_fired(self, bullet_fired_event: BulletFiredEvent) -> None:
        # add wave buat guess factor
        del bullet_fired_event


    async def on_tick(self, tick_event: TickEvent) -> None:
        del tick_event

        g = self.get_graphics()

        for wave_bullet_list in self._wave_bullet.values():
            for wave_bullet in wave_bullet_list:
                wave_bullet.distance += wave_bullet.bullet_info.speed

                bullet_current_position = mu.project(wave_bullet.bullet_info.position, wave_bullet.bullet_info.direction, wave_bullet.distance)

                g.draw_line(*wave_bullet.bullet_info.position, *bullet_current_position)
                g.draw_circle(*wave_bullet.bullet_info.position, wave_bullet.distance)
                g.set_stroke_color(Color.from_rgb(200, 200, 200))

                if wave_bullet.distance ** 2 > (self.get_x() - wave_bullet.bullet_info.position[0]) ** 2 + \
                   (self.get_y() - wave_bullet.bullet_info.position[1]) ** 2:

                    wave_bullet_list.remove(wave_bullet)


    async def on_skipped_turn(self, skipped_turn_event: SkippedTurnEvent) -> None:
        print("Skipped turn:", skipped_turn_event)


    def wall_smoothing(self, location: tuple[float, float], angle_deg: float, orientation: int) -> float:
        angle_rad = np.radians(angle_deg)
        while not self._arena_rect.contains(*mu.project(location, np.degrees(angle_rad), Anjing.WALL_STICK)):
            angle_rad += orientation * 0.05

        return np.degrees(angle_rad)


    def get_closest_surfable_wave(self) -> WaveBullet | None:
        closest_wave = None
        closest_distance = float('inf')

        for wave_bullet_list in self._wave_bullet.values():
            for wave_bullet in wave_bullet_list:
                distance_to_wave = np.hypot(
                    self.get_x() - wave_bullet.bullet_info.position[0],
                    self.get_y() - wave_bullet.bullet_info.position[1]
                ) - wave_bullet.distance

                if 0 < distance_to_wave < closest_distance:
                    closest_distance = distance_to_wave
                    closest_wave = wave_bullet

        return closest_wave


    def get_factor_index(self, wave_bullet: WaveBullet, position: tuple[float, float]) -> int:
        abs_angle = mu.angle_between_points(wave_bullet.bullet_info.position, position)
        offset_angle = self.normalize_relative_angle(abs_angle - wave_bullet.bullet_info.direction)
        max_escape_angle = mu.max_escape_angle(wave_bullet.bullet_info.speed)
        factor = mu.limit(-1, offset_angle / max_escape_angle, 1)

        return int(
            mu.limit(
                0,
                (factor + 1) / 2 * EnemyInfo.BIN,
                EnemyInfo.BIN - 1
            )
        )


    def log_hit(self, wave_bullet: WaveBullet, location: tuple[float, float]) -> None:
        index = self.get_factor_index(wave_bullet, location)
        enemy = self._enemy_dict.get(wave_bullet.bullet_info.owner_id)
        if enemy:
            enemy.surf_stat[index] += 1


    def predict_position(self, wave_bullet: WaveBullet, direction: int) -> tuple[float, float]:
        # posisi & state awal
        x, y = self.get_x(), self.get_y()
        predicted_velocity = self.get_speed()
        predicted_heading = self.get_direction()

        fire_x, fire_y = wave_bullet.bullet_info.position
        bullet_speed = wave_bullet.bullet_info.speed

        counter = 0
        intercepted = False

        while not intercepted and counter < 500:
            abs_bearing = mu.angle_between_points((fire_x, fire_y), (x, y)) 

            move_angle = self.wall_smoothing(
                (x, y),
                abs_bearing + direction * 90.0,
                direction
            ) - predicted_heading

            move_dir = 1.0

            if np.cos(np.radians(move_angle)) < 0:
                move_angle += 180.0
                move_dir = -1.0

            move_angle = self.normalize_relative_angle(move_angle)

            max_turn = max(0, 10.0 - 0.75 * abs(predicted_velocity))

            turn = mu.limit(-max_turn, move_angle, max_turn)
            predicted_heading = self.normalize_relative_angle(predicted_heading + turn)

            if predicted_velocity * move_dir < 0:
                predicted_velocity += 2.0 * move_dir
            else:
                predicted_velocity += move_dir

            predicted_velocity = mu.limit(-8.0, predicted_velocity, 8.0)

            x, y = mu.project((x, y), predicted_heading, predicted_velocity)

            counter += 1

            traveled = wave_bullet.distance + counter * bullet_speed

            if np.hypot(x - fire_x, y - fire_y) < traveled + bullet_speed:
                intercepted = True

        return (x, y)


    def check_danger(self, wave_bullet: WaveBullet, direction: int) -> tuple[float, tuple[float, float]]:
        position = self.predict_position(wave_bullet, direction)
        index = self.get_factor_index(wave_bullet, position)
        enemy = self._enemy_dict.get(wave_bullet.bullet_info.owner_id)

        if enemy:
            danger = enemy.surf_stat[index]

            for en in self._enemy_dict.values():
                danger += 1 / ((position[0] - en.position[0]) ** 2 + (position[1] - en.position[1]) ** 2)

            return danger, position
        return 0.0, position


async def main() -> None:
    bot = Anjing()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())

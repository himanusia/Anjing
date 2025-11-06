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
v2.2.1
- approx linear targeting

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
        # 1. Vektor kecepatan musuh
        theta = math.radians(enemy_deg)
        vx = enemy_speed * math.cos(theta)
        vy = enemy_speed * math.sin(theta)

        # 2. Selisih posisi awal
        dx = xm - xk
        dy = ym - yk

        # 3. Koefisien kuadrat
        a = vx*vx + vy*vy - bullet_speed**2
        b = 2 * (dx*vx + dy*vy)
        c = dx*dx + dy*dy

        D = b*b - 4*a*c
        if D < 0:
            return self.gun_bearing_to(xm, ym)  # tidak ada solusi nyata -> peluru kepelanan
        sqrtD = math.sqrt(D)
        t1 = (-b + sqrtD) / (2*a)
        t2 = (-b - sqrtD) / (2*a)

        # ambil t positif terkecil
        ts = [t for t in (t1, t2) if t > 0]
        if not ts: # ga mungkin
            return self.gun_bearing_to(xm, ym)
        t = min(ts)

        # 5. Titik tumbukan
        x_hit = xm + vx * t
        y_hit = ym + vy * t
        return self.gun_bearing_to(x_hit, y_hit)

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

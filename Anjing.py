import asyncio

from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent

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
- fire ke scanned bot

"""
# ------------------------------------------------------------------

class Anjing(Bot):
    async def run(self) -> None:
        self.set_turn_radar_left(float('inf'))
        self.set_adjust_radar_for_gun_turn(True)

    async def on_scanned_bot(self, scanned_bot_event: ScannedBotEvent) -> None:
        self.set_turn_gun_left(self.gun_bearing_to(scanned_bot_event.x, scanned_bot_event.y))
        await self.fire(1)

        if (scanned_bot_event.energy < 100):
            sudut = self.normalize_relative_angle(self.radar_bearing_to(scanned_bot_event.x, scanned_bot_event.y))
            self.set_turn_radar_left(float('inf') * sudut)

async def main() -> None:
    bot = Anjing()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())

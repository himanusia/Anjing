import asyncio

from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent

# ------------------------------------------------------------------
# Anjing
# ------------------------------------------------------------------
"""
===== RADAR =====
V1.0
- kosongan
V1.1
- radar 360
V1.2
- radar lock

"""
# ------------------------------------------------------------------

class Anjing(Bot):
    async def run(self) -> None:
        self.set_turn_radar_left(float('inf'))

    async def on_scanned_bot(self, scanned_bot_event: ScannedBotEvent) -> None:
        sudut = self.normalize_relative_angle(self.radar_bearing_to(scanned_bot_event.x, scanned_bot_event.y))
        self.set_turn_radar_left(float('inf') * sudut)

async def main() -> None:
    bot = Anjing()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())

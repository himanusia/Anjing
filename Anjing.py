import asyncio

from robocode_tank_royale.bot_api.bot import Bot

# ------------------------------------------------------------------
# Anjing
# ------------------------------------------------------------------
"""
V1.0
- kosongan
V1.1
- radar 360
"""
# ------------------------------------------------------------------
class Anjing(Bot):
    async def run(self) -> None:
        self.set_turn_radar_left(float('inf'))


async def main() -> None:
    bot = Anjing()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())

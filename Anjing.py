import asyncio

from robocode_tank_royale.bot_api.bot import Bot

# ------------------------------------------------------------------
# Anjing
# ------------------------------------------------------------------
"""
V1.0
- kosongan
"""
# ------------------------------------------------------------------
class Anjing(Bot):
    async def run(self) -> None:
        pass


async def main() -> None:
    bot = Anjing()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())

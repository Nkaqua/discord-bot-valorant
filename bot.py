import discord
from discord.ext import commands

from config import DISCORD_TOKEN, get_required_env


EXTENSIONS = [
    "cogs.rank",
    "cogs.tracker",
    "cogs.player",
    "cogs.watcher",
    "cogs.summary",
    "cogs.agentstats",
]


class ValorantBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):
        for extension in EXTENSIONS:
            await self.load_extension(extension)
            print(f"Loaded extension: {extension}")

        synced = await self.tree.sync()

        print("Slash commands synced globally.")
        print(f"Synced commands: {[cmd.name for cmd in synced]}")


bot = ValorantBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


def main():
    token = get_required_env("DISCORD_TOKEN", DISCORD_TOKEN)
    bot.run(token)


if __name__ == "__main__":
    main()

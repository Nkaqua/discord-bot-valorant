import discord
from discord.ext import commands

from config import DISCORD_TOKEN, get_required_env


class ClearEverywhereBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.cleaned = False

    async def on_ready(self):
        if self.cleaned:
            return

        self.cleaned = True
        print("古いSlash Commandを全サーバーとグローバルから削除します。")

        for guild in self.guilds:
            guild_object = discord.Object(id=guild.id)

            self.tree.clear_commands(guild=guild_object)
            synced_guild = await self.tree.sync(guild=guild_object)

            print(f"Guild commands cleared: {guild.name} ({guild.id})")
            print(f"Remaining guild commands: {[cmd.name for cmd in synced_guild]}")

        self.tree.clear_commands(guild=None)
        synced_global = await self.tree.sync()

        print("Global commands cleared")
        print(f"Remaining global commands: {[cmd.name for cmd in synced_global]}")

        await self.close()


bot = ClearEverywhereBot()


def main():
    token = get_required_env("DISCORD_TOKEN", DISCORD_TOKEN)
    bot.run(token)


if __name__ == "__main__":
    main()

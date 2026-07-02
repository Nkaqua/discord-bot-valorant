import discord
from discord.ext import commands

from config import DISCORD_TOKEN, DISCORD_GUILD_ID, get_required_env


class ClearCommandBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("古いSlash Commandを削除します。")

        # 1. 開発用サーバーのコマンドを削除
        if DISCORD_GUILD_ID:
            guild = discord.Object(id=int(DISCORD_GUILD_ID))

            self.tree.clear_commands(guild=guild)
            synced_guild = await self.tree.sync(guild=guild)

            print(f"Guild commands cleared: {DISCORD_GUILD_ID}")
            print(f"Remaining guild commands: {[cmd.name for cmd in synced_guild]}")

        # 2. グローバルコマンドを削除
        self.tree.clear_commands(guild=None)
        synced_global = await self.tree.sync()

        print("Global commands cleared")
        print(f"Remaining global commands: {[cmd.name for cmd in synced_global]}")

        await self.close()


bot = ClearCommandBot()


def main():
    token = get_required_env("DISCORD_TOKEN", DISCORD_TOKEN)
    bot.run(token)


if __name__ == "__main__":
    main()
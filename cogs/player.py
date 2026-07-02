import discord
from discord import app_commands
from discord.ext import commands

from utils.player_store import save_player, list_players, delete_player


class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="saveplayer",
        description="よく使うValorantのnameとtagを保存します",
    )
    @app_commands.describe(
        alias="保存名です。例: me, friend, duo",
        name="Valorantの名前です。例: Shohei",
        tag="Valorantのタグです。例: JP1",
    )
    async def saveplayer(
        self,
        interaction: discord.Interaction,
        alias: str,
        name: str,
        tag: str,
    ):
        save_player(
            discord_user_id=interaction.user.id,
            alias=alias,
            name=name,
            tag=tag,
        )

        await interaction.response.send_message(
            f"`{alias}` として `{name}#{tag}` を保存しました。"
        )

    @app_commands.command(
        name="players",
        description="保存しているValorantプレイヤー一覧を表示します",
    )
    async def players(self, interaction: discord.Interaction):
        players = list_players(interaction.user.id)

        if not players:
            await interaction.response.send_message(
                "保存されているプレイヤーはありません。\n"
                "例: `/saveplayer alias:me name:Shohei tag:JP1`"
            )
            return

        lines = []

        for alias, player in players.items():
            lines.append(f"- `{alias}`: {player['name']}#{player['tag']}")

        embed = discord.Embed(
            title="保存済みプレイヤー一覧",
            description="\n".join(lines),
            color=discord.Color.green(),
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="deleteplayer",
        description="保存しているValorantプレイヤーを削除します",
    )
    @app_commands.describe(
        alias="削除したい保存名です。例: me, friend, duo",
    )
    async def deleteplayer(
        self,
        interaction: discord.Interaction,
        alias: str,
    ):
        deleted = delete_player(
            discord_user_id=interaction.user.id,
            alias=alias,
        )

        if deleted:
            await interaction.response.send_message(
                f"`{alias}` を削除しました。"
            )
        else:
            await interaction.response.send_message(
                f"`{alias}` は保存されていません。"
            )


async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
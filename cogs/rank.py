from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from config import VALORANT_NAME, VALORANT_TAG
from services.henrik import fetch_valorant_rank
from utils.player_autocomplete import saved_player_alias_autocomplete
from utils.player_resolver import resolve_player


class RankCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="rank",
        description="指定したValorantプレイヤーのランクを表示します",
    )
    @app_commands.describe(
    name="Valorantの名前を入力します。例: Shohei",
    tag="Valorantのタグを入力します。例: JP1",
    alias="保存済みプレイヤーの名前です。例: me, friend",
    )
    @app_commands.autocomplete(alias=saved_player_alias_autocomplete)
    async def rank(
    self,
    interaction: discord.Interaction,
    name: Optional[str] = None,
    tag: Optional[str] = None,
    alias: Optional[str] = None,
    ):
        await interaction.response.defer()

        try:
            target_name, target_tag = resolve_player(
                discord_user_id=interaction.user.id,
                name=name,
                tag=tag,
                alias=alias,
            )

            if not target_name or not target_tag:
                await interaction.followup.send(
                    "Valorantの名前とタグが設定されていません。\n"
                    "例: `/rank name:Shohei tag:JP1`\n"
                    "または `.env` に `VALORANT_NAME` と `VALORANT_TAG` を設定してください。"
                )
                return

            result = await fetch_valorant_rank(target_name, target_tag)
            data = result.get("data", {})

            account = data.get("account", {})
            current = data.get("current", {})
            peak = data.get("peak", {})

            riot_name = account.get("name", target_name)
            riot_tag = account.get("tag", target_tag)

            current_tier = "Unrated"
            rr = "不明"
            last_change = "不明"
            elo = "不明"
            peak_tier = "不明"
            if isinstance(current, dict):
                tier = current.get("tier", {})
                if isinstance(tier, dict):
                    current_tier = tier.get("name", "Unrated")

                rr = current.get("rr", "不明")
                last_change = current.get("last_change", "不明")
                elo = current.get("elo", "不明")

            if isinstance(peak, dict):
                tier = peak.get("tier", {})
                if isinstance(tier, dict):
                    peak_tier = tier.get("name", "不明")

            embed = discord.Embed(
                title=f"{riot_name}#{riot_tag} のValorantランク",
                color=discord.Color.red(),
            )

            embed.add_field(name="現在ランク",
                            
            value=str(current_tier), inline=False)
            embed.add_field(name="RR", value=str(rr), inline=True)
            embed.add_field(name="前試合の変動", value=str(last_change), inline=True)
            embed.add_field(name="Elo", value=str(elo), inline=True)
            embed.add_field(name="最高ランク", value=str(peak_tier), inline=False)

            embed.set_footer(text="Powered by HenrikDev API")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"ランク情報を取得できませんでした。\n```{e}```"
            )


async def setup(bot):
    await bot.add_cog(RankCog(bot))

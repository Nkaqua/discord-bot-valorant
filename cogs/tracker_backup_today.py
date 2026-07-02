from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from config import VALORANT_NAME, VALORANT_TAG
from services.henrik import fetch_account, fetch_recent_competitive_matches_by_puuid
from utils.valorant_stats import extract_one_match_summary, debug_match_players

class TrackerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="tracker",
        description="直近5試合の成績をTracker風に表示します",
    )
    @app_commands.describe(
        name="Valorantの名前を入力します。例: Shohei",
        tag="Valorantのタグを入力します。例: JP1",
    )
    async def tracker(
        self,
        interaction: discord.Interaction,
        name: Optional[str] = None,
        tag: Optional[str] = None,
    ):
        await interaction.response.defer()

        try:
            target_name = name if name else VALORANT_NAME
            target_tag = tag if tag else VALORANT_TAG
            if not target_name or not target_tag:
                await interaction.followup.send(
                    "Valorantの名前とタグが設定されていません。\n"
                    "例: `/tracker name:Shohei tag:JP1`\n"
                    "または `.env` に `VALORANT_NAME` と `VALORANT_TAG` を設定してください。"
                )
                return

            account_result = await fetch_account(target_name, target_tag)
            account_data = account_result.get("data", {})
            target_puuid = account_data.get("puuid")

            if not target_puuid:
                await interaction.followup.send(
                    "対象プレイヤーのPUUIDを取得できませんでした。"
                )
                return

            result = await fetch_recent_competitive_matches_by_puuid(target_puuid, size=5)
            matches = result.get("data", [])

            if not matches:
                await interaction.followup.send(
                    "直近の試合情報を取得できませんでした。"
                )
                return
            embed = discord.Embed(
                title=f"{target_name}#{target_tag} の直近5試合",
                description="KDA / ACS / HS率 / エージェント / マップを表示します。",
                color=discord.Color.purple(),
            )

            for index, match_data in enumerate(matches[:5], start=1):
                summary = extract_one_match_summary(
                    match_data,
                    target_name,
                    target_tag,
                    target_puuid,
                )

                if not summary:
                    debug_match_players(match_data, index, target_puuid)

                    embed.add_field(
                        name=f"{index}試合目",
                        value="この試合内で対象プレイヤーを見つけられませんでした。PowerShellのDEBUG出力を確認してください。",
                        inline=False,
                    )
                    continue
                score_text = "スコア不明"
                if (
                    summary["team_score"] is not None
                    and summary["enemy_score"] is not None
                ):
                    score_text = f"{summary['team_score']} - {summary['enemy_score']}"

                field_title = (
                    f"{index}試合目：{summary['result']} "
                    f"({score_text}) / {summary['map']} / {summary['agent']}"
                )

                field_value = (
                    f"モード: {summary['mode']}\n"
                    f"KDA: {summary['kills']} / {summary['deaths']} / {summary['assists']}\n"
                    f"ACS: {summary['acs']}\n"
                    f"HS率: {summary['hs_rate']}"
                )

                embed.add_field(
                    name=field_title,
                    value=field_value,
                    inline=False,
                )
            embed.set_footer(text="Powered by HenrikDev API")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"Tracker情報を取得できませんでした。\n```{e}```"
            )


async def setup(bot):
    await bot.add_cog(TrackerCog(bot))
from collections import Counter
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from services.henrik import fetch_account, fetch_recent_competitive_matches_by_puuid
from utils.player_autocomplete import saved_player_alias_autocomplete
from utils.player_resolver import resolve_player
from utils.valorant_stats import extract_one_match_summary


def parse_percent(value):
    if not isinstance(value, str) or value == "不明":
        return None

    try:
        return float(value.rstrip("%"))
    except ValueError:
        return None


def average(values):
    values = [value for value in values if value is not None]

    if not values:
        return None

    return sum(values) / len(values)


class SummaryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="summary",
        description="直近10試合の成績サマリーを表示します",
    )
    @app_commands.describe(
        name="Valorantの名前を入力します。例: Shohei",
        tag="Valorantのタグを入力します。例: JP1",
        alias="保存済みプレイヤーの名前です。例: me, friend",
    )
    @app_commands.autocomplete(alias=saved_player_alias_autocomplete)
    async def summary(
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
                    "例: `/summary name:Shohei tag:JP1`\n"
                    "または `/saveplayer alias:me name:Shohei tag:JP1` で保存してください。"
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

            result = await fetch_recent_competitive_matches_by_puuid(
                target_puuid,
                size=10,
            )
            matches = result.get("data", [])

            if not matches:
                await interaction.followup.send(
                    "直近のCompetitive試合情報を取得できませんでした。"
                )
                return

            summaries = []

            for match_data in matches:
                summary = extract_one_match_summary(
                    match_data,
                    target_name,
                    target_tag,
                    target_puuid,
                )

                if summary:
                    summaries.append(summary)

            if not summaries:
                await interaction.followup.send(
                    "Competitiveの試合は取得できましたが、対象プレイヤーを見つけられませんでした。"
                )
                return

            total_matches = len(summaries)
            wins = sum(1 for summary in summaries if summary["result"] == "WIN")
            losses = sum(1 for summary in summaries if summary["result"] == "LOSE")
            win_rate = wins / total_matches * 100

            total_kills = sum(summary["kills"] for summary in summaries)
            total_deaths = sum(summary["deaths"] for summary in summaries)
            total_assists = sum(summary["assists"] for summary in summaries)

            acs_values = [
                summary["acs"]
                for summary in summaries
                if isinstance(summary["acs"], int)
            ]
            hs_values = [parse_percent(summary["hs_rate"]) for summary in summaries]

            avg_acs = average(acs_values)
            avg_hs = average(hs_values)

            agents = Counter(summary["agent"] for summary in summaries)
            maps = Counter(summary["map"] for summary in summaries)

            most_used_agent, agent_count = agents.most_common(1)[0]
            most_played_map, map_count = maps.most_common(1)[0]

            embed = discord.Embed(
                title=f"{target_name}#{target_tag} の直近{total_matches}試合サマリー",
                description="Competitiveの直近試合から集計しています。",
                color=discord.Color.gold(),
            )

            embed.add_field(
                name="勝敗",
                value=f"{wins}勝 {losses}敗 / 勝率 {win_rate:.1f}%",
                inline=False,
            )
            embed.add_field(
                name="合計KDA",
                value=f"{total_kills} / {total_deaths} / {total_assists}",
                inline=True,
            )
            embed.add_field(
                name="平均ACS",
                value="不明" if avg_acs is None else f"{avg_acs:.0f}",
                inline=True,
            )
            embed.add_field(
                name="平均HS率",
                value="不明" if avg_hs is None else f"{avg_hs:.1f}%",
                inline=True,
            )
            embed.add_field(
                name="最多エージェント",
                value=f"{most_used_agent} ({agent_count}試合)",
                inline=True,
            )
            embed.add_field(
                name="最多マップ",
                value=f"{most_played_map} ({map_count}試合)",
                inline=True,
            )

            embed.set_footer(text="Powered by HenrikDev API")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"サマリー情報を取得できませんでした。\n```{e}```"
            )


async def setup(bot):
    await bot.add_cog(SummaryCog(bot))

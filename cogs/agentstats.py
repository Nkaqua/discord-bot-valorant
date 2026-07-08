from collections import defaultdict
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


def format_average(value, suffix=""):
    if value is None:
        return "不明"

    return f"{value:.1f}{suffix}"


class AgentStatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="agentstats",
        description="直近試合のエージェント別成績を表示します",
    )
    @app_commands.describe(
        name="Valorantの名前を入力します。例: Shohei",
        tag="Valorantのタグを入力します。例: JP1",
        alias="保存済みプレイヤーの名前です。例: me, friend",
    )
    @app_commands.autocomplete(alias=saved_player_alias_autocomplete)
    async def agentstats(
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
                    "例: `/agentstats name:Shohei tag:JP1`\n"
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
                size=20,
            )
            matches = result.get("data", [])

            if not matches:
                await interaction.followup.send(
                    "直近のCompetitive試合情報を取得できませんでした。"
                )
                return

            agent_stats = defaultdict(
                lambda: {
                    "matches": 0,
                    "wins": 0,
                    "losses": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                    "acs": [],
                    "hs": [],
                }
            )

            for match_data in matches:
                summary = extract_one_match_summary(
                    match_data,
                    target_name,
                    target_tag,
                    target_puuid,
                )

                if not summary:
                    continue

                stats = agent_stats[summary["agent"]]
                stats["matches"] += 1
                stats["kills"] += summary["kills"]
                stats["deaths"] += summary["deaths"]
                stats["assists"] += summary["assists"]

                if summary["result"] == "WIN":
                    stats["wins"] += 1
                elif summary["result"] == "LOSE":
                    stats["losses"] += 1

                if isinstance(summary["acs"], int):
                    stats["acs"].append(summary["acs"])

                hs_rate = parse_percent(summary["hs_rate"])
                if hs_rate is not None:
                    stats["hs"].append(hs_rate)

            if not agent_stats:
                await interaction.followup.send(
                    "Competitiveの試合は取得できましたが、対象プレイヤーを見つけられませんでした。"
                )
                return

            sorted_agents = sorted(
                agent_stats.items(),
                key=lambda item: (item[1]["matches"], item[1]["wins"]),
                reverse=True,
            )

            embed = discord.Embed(
                title=f"{target_name}#{target_tag} のエージェント別成績",
                description="Competitiveの直近最大20試合から集計しています。",
                color=discord.Color.teal(),
            )

            for agent, stats in sorted_agents[:8]:
                matches_count = stats["matches"]
                win_rate = stats["wins"] / matches_count * 100
                avg_acs = average(stats["acs"])
                avg_hs = average(stats["hs"])

                value = (
                    f"{stats['wins']}勝 {stats['losses']}敗 / 勝率 {win_rate:.1f}%\n"
                    f"KDA: {stats['kills']} / {stats['deaths']} / {stats['assists']}\n"
                    f"平均ACS: {format_average(avg_acs)} / "
                    f"平均HS率: {format_average(avg_hs, '%')}"
                )

                embed.add_field(
                    name=f"{agent} ({matches_count}試合)",
                    value=value,
                    inline=False,
                )

            if len(sorted_agents) > 8:
                embed.set_footer(
                    text=f"Powered by HenrikDev API / 上位8エージェントを表示"
                )
            else:
                embed.set_footer(text="Powered by HenrikDev API")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"エージェント別成績を取得できませんでした。\n```{e}```"
            )


async def setup(bot):
    await bot.add_cog(AgentStatsCog(bot))

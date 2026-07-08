import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import HENRIK_API_KEY, VALORANT_REGION
from utils.player_autocomplete import saved_player_alias_autocomplete
from utils.player_store import list_players
from utils.watcher_store import (
    load_watchers,
    save_watchers,
    set_watcher,
    remove_watcher,
)


CHECK_INTERVAL_MINUTES = 5


class WatcherCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.watch_loop.start()

    def cog_unload(self):
        self.watch_loop.cancel()

    @app_commands.command(
        name="watchplayer",
        description="このチャンネルに試合結果通知を設定します",
    )
    @app_commands.describe(
        alias="保存済みプレイヤー名です。例: me, friend, duo",
    )
    @app_commands.autocomplete(alias=saved_player_alias_autocomplete)
    async def watchplayer(self, interaction: discord.Interaction, alias: str):
        players = list_players(interaction.user.id)

        if alias not in players:
            await interaction.response.send_message(
                f"`{alias}` は保存されていません。\n"
                f"先に `/saveplayer alias:{alias} name:名前 tag:タグ` をしてください。",
                ephemeral=True,
            )
            return

        set_watcher(
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            discord_user_id=interaction.user.id,
            alias=alias,
        )

        await interaction.response.send_message(
            f"✅ このチャンネルを `{alias}` の試合結果通知チャンネルにしました。\n"
            f"{CHECK_INTERVAL_MINUTES}分ごとに確認します。"
        )

    @app_commands.command(
        name="stopwatch",
        description="このサーバーの試合結果通知を停止します",
    )
    async def stopwatch(self, interaction: discord.Interaction):
        deleted = remove_watcher(interaction.guild.id)

        if deleted:
            await interaction.response.send_message("✅ 試合結果通知を停止しました。")
        else:
            await interaction.response.send_message("通知設定はありません。")

    @tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
    async def watch_loop(self):
        data = load_watchers()

        for guild_id, watcher in data.items():
            channel = self.bot.get_channel(int(watcher["channel_id"]))

            if channel is None:
                continue

            players = list_players(int(watcher["discord_user_id"]))
            alias = watcher["alias"]

            if alias not in players:
                continue

            player = players[alias]
            name = player["name"]
            tag = player["tag"]

            latest = await self.get_latest_match(name, tag)

            if latest is None:
                continue

            match_id = latest["match_id"]

            if watcher.get("last_match_id") == match_id:
                continue

            watcher["last_match_id"] = match_id
            save_watchers(data)

            embed = discord.Embed(
                title="🎮 新しい試合結果",
                description=f"`{name}#{tag}` の試合が終了しました。",
                color=discord.Color.blue(),
            )

            embed.add_field(name="Map", value=latest["map"], inline=True)
            embed.add_field(name="Agent", value=latest["agent"], inline=True)
            embed.add_field(name="Result", value=latest["result"], inline=True)
            embed.add_field(name="K/D/A", value=latest["kda"], inline=True)
            embed.add_field(name="ACS", value=str(latest["acs"]), inline=True)
            embed.add_field(name="HS%", value=latest["hs"], inline=True)

            await channel.send(embed=embed)

    @watch_loop.before_loop
    async def before_watch_loop(self):
        await self.bot.wait_until_ready()

    async def get_latest_match(self, name: str, tag: str):
        url = (
            f"https://api.henrikdev.xyz/valorant/v3/matches/"
            f"{VALORANT_REGION}/{name}/{tag}"
        )

        headers = {
            "Authorization": HENRIK_API_KEY,
        }

        params = {
            "mode": "competitive",
            "size": 1,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as res:
                if res.status != 200:
                    print(f"Henrik API error: {res.status}")
                    return None

                json_data = await res.json()

        matches = json_data.get("data", [])

        if not matches:
            return None

        match = matches[0]

        metadata = match.get("metadata", {})
        players = match.get("players", {})
        all_players = players.get("all_players", [])

        target = None

        for p in all_players:
            if (
                p.get("name", "").lower() == name.lower()
                and p.get("tag", "").lower() == tag.lower()
            ):
                target = p
                break

        if target is None:
            return None

        stats = target.get("stats", {})
        team = target.get("team", "").lower()

        teams = match.get("teams", {})
        result = "不明"

        if team in teams:
            has_won = teams[team].get("has_won")
            if has_won is True:
                result = "WIN"
            elif has_won is False:
                result = "LOSE"

        kills = stats.get("kills", 0)
        deaths = stats.get("deaths", 0)
        assists = stats.get("assists", 0)
        headshots = stats.get("headshots", 0)
        bodyshots = stats.get("bodyshots", 0)
        legshots = stats.get("legshots", 0)

        total_shots = headshots + bodyshots + legshots
        hs_percent = 0

        if total_shots > 0:
            hs_percent = round(headshots / total_shots * 100, 1)

        return {
            "match_id": metadata.get("matchid"),
            "map": metadata.get("map", "不明"),
            "agent": target.get("character", "不明"),
            "result": result,
            "kda": f"{kills}/{deaths}/{assists}",
            "acs": stats.get("score", 0),
            "hs": f"{hs_percent}%",
        }


async def setup(bot):
    await bot.add_cog(WatcherCog(bot))

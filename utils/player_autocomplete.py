from discord import app_commands

from utils.player_store import list_players


async def saved_player_alias_autocomplete(interaction, current):
    players = list_players(interaction.user.id)
    current = str(current or "").lower()

    choices = []

    for alias, player in players.items():
        if current and current not in alias.lower():
            continue

        name = player.get("name", "不明")
        tag = player.get("tag", "不明")

        choices.append(
            app_commands.Choice(
                name=f"{alias} - {name}#{tag}",
                value=alias,
            )
        )

        if len(choices) >= 25:
            break

    return choices

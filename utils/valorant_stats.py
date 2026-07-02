def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_text(value):
    return str(value or "").strip().lower()


def normalize_puuid(value):
    return str(value or "").strip().lower()


def get_nested_value(data, keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)

    return current


def get_player_list(match_data):
    players = match_data.get("players", [])

    if isinstance(players, list):
        return players

    if isinstance(players, dict):
        player_list = []

        if isinstance(players.get("all_players"), list):
            player_list.extend(players.get("all_players"))

        if isinstance(players.get("red"), list):
            player_list.extend(players.get("red"))

        if isinstance(players.get("blue"), list):
            player_list.extend(players.get("blue"))

        for value in players.values():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and item not in player_list:
                        player_list.append(item)

        return player_list

    return []


def get_player_puuid(player):
    candidates = [
        player.get("puuid"),
        player.get("PUUID"),
        player.get("subject"),
        get_nested_value(player, ["account", "puuid"]),
        get_nested_value(player, ["account", "PUUID"]),
        get_nested_value(player, ["account", "subject"]),
        get_nested_value(player, ["player", "puuid"]),
        get_nested_value(player, ["player", "PUUID"]),
        get_nested_value(player, ["player", "subject"]),
    ]

    for value in candidates:
        if value:
            return str(value)

    return None


def get_player_name(player):
    candidates = [
        player.get("name"),
        get_nested_value(player, ["account", "name"]),
        get_nested_value(player, ["player", "name"]),
    ]

    for value in candidates:
        if value:
            return str(value)

    return ""


def get_player_tag(player):
    candidates = [
        player.get("tag"),
        get_nested_value(player, ["account", "tag"]),
        get_nested_value(player, ["player", "tag"]),
    ]

    for value in candidates:
        if value:
            return str(value)

    return ""


def find_target_player(match_data, target_name, target_tag, target_puuid=None):
    player_list = get_player_list(match_data)

    for player in player_list:
        player_puuid = get_player_puuid(player)

        if (
            target_puuid
            and player_puuid
            and normalize_puuid(player_puuid) == normalize_puuid(target_puuid)
        ):
            return player

        player_name = normalize_text(get_player_name(player))
        player_tag = normalize_text(get_player_tag(player))

        if (
            player_name == normalize_text(target_name)
            and player_tag == normalize_text(target_tag)
        ):
            return player

    return None


def get_map_name(match_data):
    metadata = match_data.get("metadata", {})
    map_info = metadata.get("map", "不明")

    if isinstance(map_info, dict):
        return map_info.get("name", "不明")

    return map_info or "不明"


def get_round_count(match_data, player_team_id=None):
    teams = match_data.get("teams", [])

    if isinstance(teams, list) and player_team_id:
        for team in teams:
            if team.get("team_id") == player_team_id:
                rounds = team.get("rounds", {})
                won = safe_int(rounds.get("won"))
                lost = safe_int(rounds.get("lost"))
                total = won + lost

                if total > 0:
                    return total

    metadata = match_data.get("metadata", {})

    if metadata.get("rounds_played"):
        return safe_int(metadata.get("rounds_played"))

    rounds = match_data.get("rounds", [])
    if isinstance(rounds, list) and len(rounds) > 0:
        return len(rounds)

    return 0


def get_match_result(match_data, player_team_id):
    teams = match_data.get("teams", [])

    if isinstance(teams, list):
        for team in teams:
            if team.get("team_id") == player_team_id:
                won = team.get("won")
                rounds = team.get("rounds", {})

                team_rounds = safe_int(rounds.get("won"))
                enemy_rounds = safe_int(rounds.get("lost"))

                if won is True:
                    return "WIN", team_rounds, enemy_rounds

                if won is False:
                    return "LOSE", team_rounds, enemy_rounds

                if team_rounds > enemy_rounds:
                    return "WIN", team_rounds, enemy_rounds

                if team_rounds < enemy_rounds:
                    return "LOSE", team_rounds, enemy_rounds

    return "不明", None, None


def calc_hs_rate(headshots, bodyshots, legshots):
    headshots = safe_int(headshots)
    bodyshots = safe_int(bodyshots)
    legshots = safe_int(legshots)

    total_hits = headshots + bodyshots + legshots

    if total_hits == 0:
        return "不明"

    return f"{headshots / total_hits * 100:.1f}%"


def calc_acs(score, rounds):
    score = safe_int(score)
    rounds = safe_int(rounds)

    if rounds == 0:
        return "不明"

    return round(score / rounds)


def get_agent_name(player):
    agent = player.get("agent", {})

    if isinstance(agent, dict):
        return agent.get("name", "不明")

    if isinstance(agent, str):
        return agent

    return player.get("character", "不明")


def get_stats(player):
    stats = player.get("stats", {})

    if not isinstance(stats, dict):
        return {}

    return stats


def extract_one_match_summary(match_data, target_name, target_tag, target_puuid=None):
    player = find_target_player(
        match_data,
        target_name,
        target_tag,
        target_puuid,
    )

    if not player:
        return None

    player_team_id = player.get("team_id") or player.get("team")

    result, team_score, enemy_score = get_match_result(
        match_data,
        player_team_id,
    )

    stats = get_stats(player)

    kills = safe_int(stats.get("kills"))
    deaths = safe_int(stats.get("deaths"))
    assists = safe_int(stats.get("assists"))

    headshots = safe_int(stats.get("headshots"))
    bodyshots = safe_int(stats.get("bodyshots"))
    legshots = safe_int(stats.get("legshots"))

    score = safe_int(stats.get("score"))
    rounds = get_round_count(match_data, player_team_id)

    summary = {
        "result": result,
        "team_score": team_score,
        "enemy_score": enemy_score,
        "map": get_map_name(match_data),
        "agent": get_agent_name(player),
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "acs": calc_acs(score, rounds),
        "hs_rate": calc_hs_rate(headshots, bodyshots, legshots),
        "mode": "Competitive",
    }

    print("[DEBUG] summary created:", summary)

    return summary


def debug_match_players(match_data, index, target_puuid=None):
    metadata = match_data.get("metadata", {})
    players = get_player_list(match_data)

    print("========== DEBUG MATCH ==========")
    print(f"match index: {index}")
    print(f"mode: {metadata.get('mode')} / mode_id: {metadata.get('mode_id')}")
    print(f"map: {metadata.get('map')}")
    print(f"target_puuid: {target_puuid}")
    print(f"players count: {len(players)}")

    for i, player in enumerate(players, start=1):
        player_puuid = get_player_puuid(player)
        player_name = get_player_name(player)
        player_tag = get_player_tag(player)

        is_target = (
            target_puuid
            and player_puuid
            and normalize_puuid(player_puuid) == normalize_puuid(target_puuid)
        )

        print(f"--- player {i} ---")
        print(f"name: {player_name}#{player_tag}")
        print(f"puuid: {player_puuid}")
        print(f"is_target: {is_target}")
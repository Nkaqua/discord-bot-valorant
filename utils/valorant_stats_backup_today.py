def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def calc_hs_rate(headshots, bodyshots, legshots):
    headshots = safe_int(headshots)
    bodyshots = safe_int(bodyshots)
    legshots = safe_int(legshots)

    total_shots = headshots + bodyshots + legshots

    if total_shots == 0:
        return "不明"

    return f"{headshots / total_shots * 100:.1f}%"


def calc_acs(score, rounds):
    score = safe_int(score)
    rounds = safe_int(rounds)

    if rounds == 0:
        return "不明"

    return round(score / rounds)

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

def find_target_player(match_data, target_name, target_tag,target_puuid=None):
    players = match_data.get("players", [])

    # v4形式: players が list
    if isinstance(players, list):
        for player in players:
            player_name = str(player.get("name", "")).lower()
            player_tag = str(player.get("tag", "")).lower()

    if player_name == target_name.lower() and player_tag == target_tag.lower():
        return player
    
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
                elif won is False:
                    return "LOSE", team_rounds, enemy_rounds

                if team_rounds > enemy_rounds:
                    return "WIN", team_rounds, enemy_rounds
                elif team_rounds < enemy_rounds:
                    return "LOSE", team_rounds, enemy_rounds

                return "不明", None, None

def extract_one_match_summary(match_data, target_name, target_tag, target_puuid=None):
    player = find_target_player(
        match_data,
        target_name,
        target_tag,
        target_puuid,
    )

    if not player:
        return None

    map_name = get_map_name(match_data)

    player_team_id = (
        player.get("team_id")
        or player.get("team")
        or "不明"
    )

    result, team_score, enemy_score = get_match_result(
        match_data,
        player_team_id,
    )

    agent_info = player.get("agent", {})

    if isinstance(agent_info, dict):
        agent_name = agent_info.get("name", "不明")
    else:
        agent_name = player.get("character", "不明")

    stats = player.get("stats", {})
    kills = safe_int(stats.get("kills"))
    deaths = safe_int(stats.get("deaths"))
    assists = safe_int(stats.get("assists"))

    headshots = safe_int(stats.get("headshots"))
    bodyshots = safe_int(stats.get("bodyshots"))
    legshots = safe_int(stats.get("legshots"))

    score = safe_int(stats.get("score"))
    rounds = get_round_count(match_data, player_team_id)

    hs_rate = calc_hs_rate(headshots, bodyshots, legshots)
    acs = calc_acs(score, rounds)

    metadata = match_data.get("metadata", {})
    queue_info = metadata.get("queue", {})

    if isinstance(queue_info, dict):
        mode_name = queue_info.get("name", "不明")
    else:
        mode_name = (
            metadata.get("mode")
            or metadata.get("mode_id")
            or "不明"
        )
        return {
        "result": result,
        "team_score": team_score,
        "enemy_score": enemy_score,
        "map": map_name,
        "agent": agent_name,
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "acs": acs,
        "hs_rate": hs_rate,
        "mode": mode_name,
    }

def get_nested_value(data, keys):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)

    return current


def get_player_list(match_data):
    players = match_data.get("players", [])

    # v4形式: players がそのまま list
    if isinstance(players, list):
        return players

    # v3形式や別形式: players が dict
    if isinstance(players, dict):
        player_list = []

        # よくある形式
        if isinstance(players.get("all_players"), list):

            if isinstance(players.get("all_players"), list):
                player_list.extend(players.get("all_players"))

        # 念のため red / blue 形式にも対応
        if isinstance(players.get("red"), list):
            player_list.extend(players.get("red"))

        if isinstance(players.get("blue"), list):
            player_list.extend(players.get("blue"))

        # その他、dict内にlistがあれば拾う
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

def debug_match_players(match_data, index, target_puuid=None):
    metadata = match_data.get("metadata", {})
    players = get_player_list(match_data)

    print("========== DEBUG MATCH ==========")
    print(f"match index: {index}")
    print(f"mode: {metadata.get('mode')} / mode_id: {metadata.get('mode_id')}")
    print(f"map: {metadata.get('map')}")
    print(f"target_puuid: {target_puuid}")
    print(f"players count: {len(players)}")

    for i, player in enumerate(players[:5], start=1):
        print(f"--- player sample {i} ---")
        print(f"keys: {list(player.keys())}")
        print(f"puuid: {get_player_puuid(player)}")
        print(f"name: {get_player_name(player)}")
        print(f"tag: {get_player_tag(player)}")
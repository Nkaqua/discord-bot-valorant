import json
from pathlib import Path


DATA_DIR = Path("data")
PLAYERS_FILE = DATA_DIR / "players.json"


def ensure_players_file():
    DATA_DIR.mkdir(exist_ok=True)

    if not PLAYERS_FILE.exists():
        PLAYERS_FILE.write_text("{}", encoding="utf-8")


def load_players():
    ensure_players_file()

    try:
        text = PLAYERS_FILE.read_text(encoding="utf-8")
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def save_players(data):
    ensure_players_file()

    PLAYERS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def normalize_alias(alias):
    return str(alias or "me").strip().lower()


def save_player(discord_user_id, alias, name, tag):
    data = load_players()

    user_id = str(discord_user_id)
    alias = normalize_alias(alias)

    if user_id not in data:
        data[user_id] = {}

    data[user_id][alias] = {
        "name": name,
        "tag": tag,
    }

    save_players(data)


def get_player(discord_user_id, alias="me"):
    data = load_players()

    user_id = str(discord_user_id)
    alias = normalize_alias(alias)

    return data.get(user_id, {}).get(alias)


def list_players(discord_user_id):
    data = load_players()

    user_id = str(discord_user_id)

    return data.get(user_id, {})


def delete_player(discord_user_id, alias):
    data = load_players()

    user_id = str(discord_user_id)
    alias = normalize_alias(alias)

    if user_id not in data:
        return False

    if alias not in data[user_id]:
        return False

    del data[user_id][alias]
    save_players(data)

    return True
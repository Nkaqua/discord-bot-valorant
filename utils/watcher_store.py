import json
import os

WATCHER_FILE = "data/watchers.json"


def load_watchers():
    if not os.path.exists(WATCHER_FILE):
        return {}

    with open(WATCHER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_watchers(data):
    os.makedirs(os.path.dirname(WATCHER_FILE), exist_ok=True)

    with open(WATCHER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def set_watcher(guild_id, channel_id, discord_user_id, alias):
    data = load_watchers()

    data[str(guild_id)] = {
        "channel_id": str(channel_id),
        "discord_user_id": str(discord_user_id),
        "alias": alias,
        "last_match_id": None,
    }

    save_watchers(data)


def remove_watcher(guild_id):
    data = load_watchers()
    key = str(guild_id)

    if key not in data:
        return False

    del data[key]
    save_watchers(data)
    return True
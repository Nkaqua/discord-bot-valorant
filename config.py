import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")

HENRIK_API_KEY = os.getenv("HENRIK_API_KEY")

VALORANT_REGION = os.getenv("VALORANT_REGION", "ap")
VALORANT_PLATFORM = os.getenv("VALORANT_PLATFORM", "pc")
VALORANT_NAME = os.getenv("VALORANT_NAME")
VALORANT_TAG = os.getenv("VALORANT_TAG")


def get_required_env(name, value):
    if not value:
        raise RuntimeError(f"{name} が .env に設定されていません。")
    return value
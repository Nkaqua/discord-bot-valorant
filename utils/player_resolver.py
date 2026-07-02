from config import VALORANT_NAME, VALORANT_TAG
from utils.player_store import get_player


def resolve_player(discord_user_id, name=None, tag=None, alias=None):
    # name と tag が両方入力されている場合は、それを最優先で使う
    if name and tag:
        return name, tag

    # 片方だけ入力された場合はエラー
    if name and not tag:
        raise ValueError("name を入力した場合は tag も入力してください。")

    if tag and not name:
        raise ValueError("tag を入力した場合は name も入力してください。")

    # alias が指定されていれば、その保存データを探す
    if alias:
        saved = get_player(discord_user_id, alias)

        if not saved:
            raise ValueError(
                f"`{alias}` という保存プレイヤーが見つかりません。\n"
                "先に `/saveplayer` で保存してください。"
            )

        return saved["name"], saved["tag"]

    # alias が指定されていない場合は、me を探す
    saved = get_player(discord_user_id, "me")

    if saved:
        return saved["name"], saved["tag"]

    # me がなければ .env の設定を使う
    if VALORANT_NAME and VALORANT_TAG:
        return VALORANT_NAME, VALORANT_TAG

    raise ValueError(
        "プレイヤー情報がありません。\n"
        "例: `/saveplayer alias:me name:Shohei tag:JP1` で保存してください。"
    )
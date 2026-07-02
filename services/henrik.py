import aiohttp

from config import (
    HENRIK_API_KEY,
    VALORANT_REGION,
    VALORANT_PLATFORM,
    get_required_env,
)


async def henrik_get(url, params=None):
    api_key = get_required_env("HENRIK_API_KEY", HENRIK_API_KEY)

    headers = {
        "Authorization": api_key,
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=headers,
            params=params,
            timeout=20,
        ) as response:
            data = await response.json()

            if response.status != 200:
                raise RuntimeError(f"API Error {response.status}: {data}")

            return data


async def fetch_account(name, tag):
    url = f"https://api.henrikdev.xyz/valorant/v2/account/{name}/{tag}"
    return await henrik_get(url)

async def fetch_valorant_rank(name, tag):
    url = (
        f"https://api.henrikdev.xyz/valorant/v3/mmr/"
        f"{VALORANT_REGION}/{VALORANT_PLATFORM}/{name}/{tag}"
    )
    return await henrik_get(url)


async def fetch_recent_matches(name, tag, size=5):
    url = (
        f"https://api.henrikdev.xyz/valorant/v4/matches/"
        f"{VALORANT_REGION}/{VALORANT_PLATFORM}/{name}/{tag}"
    )

    params = {
        "size": size,
    }

    return await henrik_get(url, params=params)

async def fetch_recent_competitive_matches_by_puuid(puuid, size=10):
    url = (
        f"https://api.henrikdev.xyz/valorant/v4/by-puuid/matches/"
        f"{VALORANT_REGION}/{VALORANT_PLATFORM}/{puuid}"
    )

    params = {
        "size": size,
        "mode": "competitive",
    }

    print(f"[DEBUG] fetch competitive matches by puuid: {puuid}")

    return await henrik_get(url, params=params)
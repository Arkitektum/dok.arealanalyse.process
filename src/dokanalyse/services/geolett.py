from os import path
from uuid import UUID
from typing import Dict
import json
import aiohttp
from async_lru import alru_cache

_LOCAL_GEOLETT_IDS = [
    '0c5dc043-e5b3-4349-8587-9b464d013aaa'
]

_CACHE_TTL = 86400 * 7


async def get_geolett_data(id: UUID) -> Dict:
    if id is None:
        return None

    if id in _LOCAL_GEOLETT_IDS:
        geolett = _fetch_local_geolett_data()
    else:
        geolett = await _fetch_geolett_data()

    result = list(filter(lambda item: item['id'] == str(id), geolett))

    return result[0] if len(result) > 0 else None


@alru_cache(maxsize=32, ttl=_CACHE_TTL)
async def _fetch_geolett_data() -> Dict:
    try:
        url = 'https://register.geonorge.no/geolett/api/'

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None

                return await response.json()
    except:
        return None


def _fetch_local_geolett_data() -> Dict:
    dir_path = path.dirname(path.realpath(__file__))

    file_path = path.join(
        path.dirname(dir_path), 'resources/geolett.local.json')

    with open(file_path, 'r') as file:
        return json.load(file)


__all__ = ['get_geolett_data']

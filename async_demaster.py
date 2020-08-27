"""
Track name demastering script.
Removes nonsense like "Remastered" and "Live at".
modified from original at https://github.com/hankhank10/demaster
"""

import logging
import re

import aiohttp

API_URL = "http://demaster.hankapi.com/demaster"
OFFLINE_PATTERN = re.compile(
    r"(\s(\(|-\s+))((199\d|20[0-2]\d)\s+)?(Remast|Live|Mono|From|Feat).*", re.IGNORECASE
)

_LOGGER = logging.getLogger(__name__)


def strip_name_offline(full_song_name):
    """Use an offline regex to shorten the track name."""
    match = OFFLINE_PATTERN.search(full_song_name)
    if match:
        short_name = full_song_name[: match.start()]
        _LOGGER.debug("Demastered to %s", short_name)
        return short_name
    return full_song_name


async def strip_name_api(session, full_song_name):
    """Call the demaster API to retrieve a short track name."""
    if session is None:
        local_session = True
        session = aiohttp.ClientSession()
    else:
        local_session = False

    params = {
        "format": "simple",
        "long_track_name": full_song_name,
    }

    short_name = None

    try:
        async with session.get(API_URL, params=params) as response:
            if response.status == 200:
                short_name = await response.text()
                if short_name != full_song_name:
                    _LOGGER.debug("Demastered to %s", short_name)
    except aiohttp.ClientError as err:
        _LOGGER.error("Problem connecting to demaster API [%s]", err)
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Unknown issue connecting to demaster API [%s]", err)

    if local_session:
        await session.close()

    if short_name is None:
        raise ConnectionError

    return short_name


async def strip_name(full_song_name, session=None, offline=False):
    """Main entry point."""
    if offline:
        return strip_name_offline(full_song_name)

    try:
        return await strip_name_api(session, full_song_name)
    except ConnectionError:
        _LOGGER.debug("Online API failed, returning offline version")
        return strip_name_offline(full_song_name)

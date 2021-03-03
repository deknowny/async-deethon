"""This module contains the Session class."""
import asyncio
import time
import re
import typing as ty
from pathlib import Path
from typing import Union, Generator, Any, Tuple, Optional, Callable

import aiohttp

from . import errors, consts, utils, types


class Session:
    """A session is required to connect to Deezer's unofficial API."""

    def __init__(self, arl_token: str):
        """
        Creates a new Deezer session instance.

        Args:
            arl_token (str): The arl token is used to make API requests
                on Deezer's unofficial API

        Raises:
            DeezerLoginError: The specified arl token is not valid.
        """
        self._arl_token: str = arl_token
        self._session: ty.Optional[aiohttp.ClientSession] = None
        self._cookies = {"arl": self._arl_token}
        self._csrf_token = ""
        self._session_expires = 0

    async def update_requests_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False),
                skip_auto_headers={"User-Agent"},
                raise_for_status=True,
            )

    async def _refresh_session(self) -> None:
        user = await self.get_api(consts.METHOD_GET_USER)
        if user["USER"]["USER_ID"] == 0:
            raise errors.DeezerLoginError
        self._csrf_token = user["checkForm"]
        self._session_expires = time.time() + 3600

    async def _find_albums(self, name: str):
        async with self._session.get(
            consts.LEGACY_API_URL + "search/album", params={"q": name}
        ) as response:
            albums = await response.json()
            return albums["data"]

    async def _find_tracks(self, name: str):
        async with self._session.get(
            consts.LEGACY_API_URL + "search", params={"q": name}
        ) as response:
            tracks = await response.json()
            return tracks["data"]

    async def search_songs(
        self, name: str, albums_count: int = 3, songs_limit: int = 50
    ):
        await self.update_requests_session()
        albums, tracks = await asyncio.gather(
            self._find_albums(name), self._find_tracks(name)
        )
        albums = albums[:albums_count]
        tracks = tracks[: songs_limit - albums_count]

        albums = [
            {
                "album_title": element["title"],
                "singer_name": element["artist"]["name"],
                "album_photo_medium": element["cover_medium"],
                "link": element["link"],
            }
            for element in albums
        ]

        tracks = [
            {
                "music_title": element["title"],
                "singer_name": element["artist"]["name"],
                "album_title": element["album"]["title"],
                "album_photo_medium": element["album"]["cover_medium"],
                "link": element["link"],
            }
            for element in tracks
        ]
        return albums, tracks

    async def get_api(self, method: str, json: dict = None) -> dict:
        if not method == consts.METHOD_GET_USER and (
            not self._csrf_token or self._session_expires > time.time()
        ):
            await self._refresh_session()

        params = {
            "api_version": "1.0",
            "api_token": self._csrf_token,
            "input": "3",
            "method": method,
        }
        await self.update_requests_session()
        async with self._session.post(
            consts.API_URL, params=params, json=json, cookies=self._cookies
        ) as response:
            response = await response.json()
            return response["results"]

    async def download(
        self,
        url: str,
        bitrate: str = "FLAC",
        progress_callback: Optional[Callable] = None,
    ):
        """
        Downloads the given Deezer url if possible.

        Args:
            url: The URL of the track or album to download.
            bitrate: The preferred bitrate to download
                (`FLAC`, `MP3_320`, `MP3_256`, `MP3_128`).
            progress_callback (callable): A callable that accepts
                `current` and `bytes` arguments.

        Raises:
            ActionNotSupported: The specified URL is not (yet)
                supported for download.
            InvalidUrlError: The specified URL is not a valid deezer link.
        """
        match = re.match(r"https?://(?:www\.)?deezer\.com/(?:\w+/)?(\w+)/(\d+)", url)
        if match:
            mode = match.group(1)
            content_id = int(match.group(2))
            if mode == "track":
                return await self.download_track(
                    await types.Track.init_via_track_id(content_id),
                    bitrate,
                    progress_callback,
                )
            if mode == "album":
                return await self.download_album(
                    await types.Album.init_via_album_id(content_id), bitrate
                )
            raise errors.ActionNotSupported(mode)
        raise errors.InvalidUrlError(url)

    async def download_track(
        self,
        track: types.Track,
        bitrate: str = "FLAC",
        progress_callback: Optional[Callable] = None,
    ) -> bytes:
        """
        Downloads the given [Track][async_deethon.types.Track] object.

        Args:
            track: A [Track][async_deethon.types.Track] instance.
            bitrate: The preferred bitrate to download
                (`FLAC`, `MP3_320`, `MP3_256`, `MP3_128`).
            progress_callback: A callable that accepts
                `current` and `bytes` arguments.

        Returns:
            The file path of the downloaded track.

        Raises:
            DownloadError: The track is not downloadable.
        """
        await self.update_requests_session()
        quality = utils.get_quality(bitrate)
        await track.add_more_tags(self)
        download_url = utils.get_stream_url(track, quality)

        async with self._session.get(download_url) as response:
            total = int(response.headers["Content-Length"])
            if not total:
                if bitrate == "FLAC":
                    fallback_bitrate = "MP3_320"
                elif bitrate == "MP3_320":
                    fallback_bitrate = "MP3_256"
                elif bitrate == "MP3_256":
                    fallback_bitrate = "MP3_128"
                else:
                    raise errors.DownloadError(track.id)
                return await self.download_track(
                    track, fallback_bitrate, progress_callback
                )

            current = 0
            buffer = b""
            async for data, _ in response.content.iter_chunks():
                current += len(data)
                buffer += data
                if progress_callback:
                    asyncio.create_task(progress_callback(current, total))

            return buffer

    async def download_track_via_id(
        self,
        track_id: int,
        bitrate: str = "FLAC",
        progress_callback: Optional[Callable] = None,
    ) -> bytes:
        track = await types.Track.init_via_track_id(track_id)
        return await self.download_track(track, bitrate, progress_callback)

    async def download_album(
        self, album: types.Album, bitrate: str = None, stream: bool = False
    ) -> tuple:
        """
        Downloads an album from Deezer using the specified Album object.

        Args:
            album: An [Album][async_deethon.types.Album] instance.
            bitrate: The preferred bitrate to download
                (`FLAC`, `MP3_320`, `MP3_256`, `MP3_128`).
            stream: If `true`, this method returns a generator object,
                otherwise the downloaded files are returned as a tuple
                that contains the file paths.

        Returns:
            The file paths.
        """
        download_coros = [
            self.download_track(track, bitrate) for track in album.fetch_tracks()
        ]
        tracks = await asyncio.gather(*download_coros)
        return tracks

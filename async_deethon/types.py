"""This module contains all available type classes."""
from __future__ import annotations

import typing as ty
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Dict, Any, ClassVar

import aiohttp

from . import consts, errors


async def _bytes_get_request(
    session: ty.Optional[aiohttp.ClientSession] = None, *args, **kwargs
) -> bytes:
    close_session = session is None
    if close_session:
        session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False),
            skip_auto_headers={"User-Agent"},
            raise_for_status=True,
        )
    async with session.get(*args, **kwargs) as response:
        response = await response.read()
        if close_session:
            await session.close()
        return response


async def _json_get_request(
    session: ty.Optional[aiohttp.ClientSession] = None, *args, **kwargs
) -> dict:
    close_session = session is None
    if close_session:
        session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False),
            skip_auto_headers={"User-Agent"},
            raise_for_status=True,
        )
    async with session.get(*args, **kwargs) as response:
        response = await response.json()
        if close_session:
            await session.close()
        return response


class Album:
    """
    The Album class contains several information about an album.

    Attributes:
        artist: The main artist of the album.
        basic_tracks_data: A list that contains basic tracks data.
        cover_small_link: The link for the album cover in small size.
        cover_medium_link: The link for the album cover in medium size.
        cover_big_link: The link for the album cover in big size.
        cover_xl_link: The link for the album cover in xl size.
        duration: The duration in seconds of the album.
        genres:A list of genres of the album.
        id: int The ID of the album.
        label: The label of the album.
        link: The Deezer link of the album.
        record_type: The record type of the album.
        release_date: The release date of the album.
        title: The title of the album.
        total_tracks: The total number of tracks in the album.
        upc: The Universal Product Code (UPC) of the album.

    """

    _cache: ClassVar[Dict[int, Album]] = {}

    artist: str
    basic_tracks_data: List[Dict[str, Any]]
    cover_small_link: str
    cover_medium_link: str
    cover_big_link: str
    cover_xl_link: str
    duration: int
    genres: List[str]
    id: int
    label: str
    link: str
    record_type: str
    release_date: datetime
    title: str
    total_tracks: int
    upc: str

    _cover_small: Optional[bytes] = None
    _cover_medium: Optional[bytes] = None
    _cover_big: Optional[bytes] = None
    _cover_xl: Optional[bytes] = None

    def __new__(cls, album_info: dict):
        """
        If an album instance with the specified album ID already exists,
        this method returns the cached instance, otherwise a new album
        instance is created.

        Args:
            album_id: The Deezer album ID.

        """
        album_id = album_info["id"]
        if album_id not in cls._cache.keys():
            cls._cache[album_id] = super(Album, cls).__new__(cls)
        return cls._cache[album_id]

    def __init__(self, album_info: dict):
        """
        Create a new album instance with the specified album ID.

        Args:
            album_id: The Deezer album ID.

        Raises:
            DeezerApiError: The Deezer API request replied with an error.

        """
        if "error" in album_info:
            raise errors.DeezerApiError(
                album_info["error"]["type"],
                album_info["error"]["message"],
                album_info["error"]["code"],
            )

        self.artist = album_info["artist"]["name"]
        self.basic_tracks_data = album_info["tracks"]["data"]
        self.cover_small_link = album_info["cover_small"]
        self.cover_medium_link = album_info["cover_medium"]
        self.cover_big_link = album_info["cover_big"]
        self.cover_xl_link = album_info["cover_xl"]
        self.duration = album_info["duration"]
        self.genres = [genre["name"] for genre in album_info["genres"]["data"]]
        self.id = album_info["id"]
        self.label = album_info["label"]
        self.link = album_info["link"]
        self.record_type = album_info["record_type"]
        self.release_date = datetime.strptime(album_info["release_date"], "%Y-%m-%d")
        self.title = album_info["title"]
        self.total_tracks = album_info["nb_tracks"]
        self.upc = album_info["upc"]

    @classmethod
    async def init_via_album_id(
        cls, album_id: int, session: ty.Optional[aiohttp.ClientSession] = None
    ) -> Album:
        info = await _json_get_request(
            session, f"https://api.deezer.com/album/{album_id}"
        )
        return cls(info)

    async def fetch_cover_small(self) -> bytes:
        """The album cover in small size."""
        if not self._cover_small:
            self._cover_small = await _bytes_get_request(None, self.cover_small_link)
        return self._cover_small

    async def fetch_cover_medium(self) -> bytes:
        """The album cover in medium size."""
        if not self._cover_medium:
            self._cover_medium = await _bytes_get_request(None, self.cover_medium_link)
        return self._cover_medium

    async def fetch_cover_big(self) -> bytes:
        """The album cover in big size."""
        if not self._cover_big:
            self._cover_big = await _bytes_get_request(None, self.cover_big_link)
        return self._cover_big

    async def fetch_cover_xl(self) -> bytes:
        """The album cover in xl size."""
        if not self._cover_xl:
            self._cover_xl = await _bytes_get_request(None, self.cover_xl_link)
        return self._cover_xl

    def fetch_tracks(self) -> list:
        """
        A list of [Track][async_deethon.types.Track] objects for each
        track in the album.
        """
        tracks = [Track(track_scheme) for track_scheme in self.basic_tracks_data]
        return tracks


class Track:
    """
    The Track class contains several information about a track.

    Attributes:
        album_id: The Deezer album ID to which the track belongs.
        artist: The main artist of the track.
        artists: A list of artists featured in the track.
        bpm: Beats per minute of the track.
        disk_number: The disc number of the track.
        duration: The duration of the track.
        id: The Deezer ID of the track.
        isrc: The International Standard Recording Code (ISRC) of the track.
        link: The Deezer link of the track.
        number: The position of the track.
        preview_link: The link to a 30 second preview of the track.
        rank: The rank of the track on Deezer
        replaygain_track_gain: The Replay Gain value of the track.
        release_date: The release date of the track.
        title: The title of the track.
        title_short: The short title of the track.

        md5_origin: The md5 origin of the track.
        media_version: The media version of the track.
        composer: The author of the track.
        author: A list of one or more authors of the track.
        lyrics: The lyrics of the track.
        lyrics_sync: The synchronized lyrics of the track.
        lyrics_copyrights: Copyright information of the lyrics.
        lyrics_writers: A list of writers of the lyrics.

    !!! Info
        `md5_origin`, `media_version`, `composer`, `author` and all
        `lyrics*` tags are only set after
        [add_more_tags()][async_deethon.types.Track.add_more_tags] is called.
        Defaults to `None`.
    """

    _cache: ClassVar[Dict[int, Track]] = {}

    album_id: int
    artist: str
    artists: List[str]
    bpm: int
    disk_number: int
    duration: int
    id: int
    isrc: str
    link: str
    number: int
    preview_link: str
    rank: int
    replaygain_track_gain: str
    release_date: datetime
    title: str
    title_short: str

    md5_origin: Optional[str]
    media_version: Optional[str]
    composer: Optional[List[str]]
    author: Optional[List[str]]
    copyright: Optional[str]
    lyrics: Optional[str]
    lyrics_sync: Optional[List[Dict[str, str]]]
    lyrics_copyrights: Optional[str]
    lyrics_writers: Optional[List[str]]

    def __new__(cls, track_info: dict):
        """
        If a track instance with the specified track ID already exists,
        this method returns the cached instance, otherwise a new track
        instance is created and cached.

        Args:
            track_id: The Deezer album ID.

        """
        track_id = track_info["id"]
        if track_id not in cls._cache.keys():
            cls._cache[track_id] = super(Track, cls).__new__(cls)
        return cls._cache[track_id]

    def __init__(self, track_info: dict):
        """
        Create a new track instance with the specified track ID.

        Args:
            track_id: The Deezer track ID.

        Raises:
            DeezerApiError: The Deezer API request replied with an error.

        """
        if "error" in track_info:
            raise errors.DeezerApiError(
                track_info["error"]["type"],
                track_info["error"]["message"],
                track_info["error"]["code"],
            )

        self.album_id: int = track_info["album"]["id"]
        self.artist = track_info["artist"]["name"]
        self.artists = [artist["name"] for artist in track_info["contributors"]]
        self.bpm = track_info["bpm"]
        self.disk_number = track_info["disk_number"]
        self.duration = track_info["duration"]
        self.id = track_info["id"]
        self.isrc = track_info["isrc"]
        self.link = track_info["link"]
        self.number = track_info["track_position"]
        self.preview_link = track_info["preview"]
        self.rank = track_info["rank"]
        self.replaygain_track_gain = f"{((track_info['gain'] + 18.4) * -1):.2f} dB"
        self.release_date = datetime.strptime(track_info["release_date"], "%Y-%m-%d")
        self.title = track_info["title"]
        self.title_short = track_info["title_short"]

    @classmethod
    async def init_via_track_id(
        cls, track_id: int, session: ty.Optional[aiohttp.ClientSession] = None
    ) -> Track:
        info = await _json_get_request(
            session, f"https://api.deezer.com/track/{track_id}"
        )
        return cls(info)

    async def fetch_album(self) -> Album:
        """Return an Album instance."""
        return await Album.init_via_album_id(self.album_id)

    async def add_more_tags(self, session) -> None:
        """
        Adds more tags using Deezer's unofficial API.

        Args:
            session: A [Session][deethon.session.Session] object is required to connect
                to the Deezer API.

        """
        r = await session.get_api(consts.METHOD_PAGE_TRACK, {"sng_id": self.id})
        self.md5_origin = r["DATA"]["MD5_ORIGIN"]
        self.media_version = r["DATA"]["MEDIA_VERSION"]

        if isinstance(r["DATA"]["SNG_CONTRIBUTORS"], list):
            self.composer = None
            self.author = None
        else:
            self.composer = r["DATA"]["SNG_CONTRIBUTORS"].get("composer")
            self.author = r["DATA"]["SNG_CONTRIBUTORS"].get("author")

        self.copyright = r["DATA"]["COPYRIGHT"]

        if "LYRICS" in r.keys():
            self.lyrics = r["LYRICS"].get("LYRICS_TEXT")
            self.lyrics_sync = r["LYRICS"].get("LYRICS_SYNC_JSON")
            self.lyrics_copyrights = r["LYRICS"].get("LYRICS_COPYRIGHTS")
            self.lyrics_writers = r["LYRICS"].get("LYRICS_WRITERS").split(", ")
        else:
            self.lyrics = None
            self.lyrics_sync = None
            self.lyrics_copyrights = None
            self.lyrics_writers = None

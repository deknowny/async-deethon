"""
🎵 Async-deethon is a Python3 library made on `aiohttp` to easily async download music from Deezer and a
wrapper for the Deezer API with some extra features. 🎵

Unfortunately, I can't find the original repo of `deethon` project
which is the base for this library so it's not a fork.
"""
import importlib.metadata

from . import types, utils, consts, errors, session
from .session import Session
from .types import Album, Track


__version__ = importlib.metadata.version(__name__)
__all__ = ["Session", "Album", "Track", "errors", "utils", "consts", "types", "session"]

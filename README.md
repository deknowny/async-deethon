# async-deethon
This library allows you download songs and albums from [deezer.com](https://deezer.com) in async style via __aiohttp__ and __asyncio__

> Actually, it's adaptive of __deethon__ library in async style made specially for the bot [@MusicFlacBot](https://telegram.im/@MusicFlacBot) in telegram


## Installation
Using pip (poetry as build system):
```shell
python -m pip install -U https://github.com/deknowny/async-deethon/archive/master.zip
```

## Usage
Download track by its ID:
```python
import asyncio

import async_deethon as deethon


async def main():
    downloader = deethon.Session("arl token from cookies")
    result = await downloader.download_track_via_id(1043317462, bitrate="MP3")
    
    # Optional save the music
    with open("file.mp3", "wb") as file:
        file.write(result)


asyncio.run(main())
```
***
Find tracks and albums
```python

import asyncio

import async_deethon as deethon


async def main():
    downloader = deethon.Session("arl token from cookies")
    result = await downloader.search_songs("Cyberpunk")
    print(result)


asyncio.run(main())
```
***
Check source for other abilities


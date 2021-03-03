import asyncio

import async_deethon as deethon


async def download():
    downloader = deethon.Session(
        "205e3b518df04fe4fccfd1cc47df"
        "811ccb5d5dc533c717e9aabab6cac"
        "25ff8f90f602078edc0586c7232897"
        "a30d6e65b0c83114d5be18148a4ae49"
        "b07ef75d904c50163a594ccaca3849eb"
        "e7bb0b4f5b783726bcf5a602e4957545d"
        "ed0d3a0b4"
    )
    result = await downloader.download_track_via_id(1043317462, bitrate="MP3")
    with open("file.mp3", "wb") as file:
        file.write(result)


async def search():
    downloader = deethon.Session(
        "205e3b518df04fe4fccfd1cc47df811ccb5"
        "d5dc533c717e9aabab6cac25ff8f90f60207"
        "8edc0586c7232897a30d6e65b0c83114d5be"
        "18148a4ae49b07ef75d904c50163a594ccac"
        "a3849ebe7bb0b4f5b783726bcf5a602e49575"
        "45ded0d3a0b4"
    )
    result = await downloader.search_songs("Cyberpunk")
    print(result)


asyncio.run(search())



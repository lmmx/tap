import asyncio
import httpx
from aiostream import stream
import aiofiles
from functools import partial
from pathlib import Path


async def fetch(session, url):
    response = await session.get(str(url))
    #response.raise_for_status()
    return response


async def process(data, download_dir):
    if not download_dir.exists():
        download_dir.mkdir()
    filename = Path(str(data.url)).name
    download_filepath = download_dir / filename
    async with aiofiles.open(download_filepath, "wb") as f:
        await f.write(data.content)
    print({data.url: data})


async def async_fetch_urlset(urls, download_dir):
    async with httpx.AsyncClient(http2=True) as session:
        #await asyncio.gather(*[fetch(session, url) for url in urls])
        ws = stream.repeat(session)
        xs = stream.zip(ws, stream.iterate(urls))
        ys = stream.starmap(xs, fetch, ordered=False, task_limit=10)
        process_download = partial(process, download_dir=download_dir)
        zs = stream.map(ys, process_download)
        return await zs

def fetch_urls(urls, download_dir):
    return asyncio.run(async_fetch_urlset(urls, download_dir))


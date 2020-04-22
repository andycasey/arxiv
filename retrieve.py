import asyncio
import aiohttp
import warnings
import logging
import json
import time
import os
import xmltodict as xml

from aiohttp import web

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

overwrite = False
_records_path = "records"

async def get_record(session, identifier, max_attempts=5):
    logger.debug(f"Searching for arXiv identifier {identifier}")

    params = dict(
        verb="GetRecord",
        identifier=f"oai:arXiv.org:{identifier}",
        metadataPrefix="arXiv"
    )
    uri = "http://export.arxiv.org/oai2"

    for attempt in range(1, 1 + max_attempts):
            
        try:
            async with session.get(uri, params=params) as response:
                content = await response.text()

        except asyncio.TimeoutError:
            logger.debug(f"asyncio.TimeoutError on {identifier} search (attempt {attempt} of {1 + max_attempts})")
            continue

        except:
            logger.exception(f"Exception occurred on identifier {identifier} ({attempt} of {1 + max_attempts})")
            continue
            
        else:
            break
    
    else:
        # Totally failed after max attempts.
        raise

    return content


def get_identifier(year, month, suffix):
    return f"{year % 2000:0>2.0f}{month:0>2.0f}.{suffix:0>5.0f}"


async def get_monthly_records(year, month, maximum=10000):

    year, month = (int(year), int(month))

    get_path = lambda suffix: os.path.join(
            _records_path,
            f"{year % 2000:0>2.0f}",
            f"{month:0>2.0f}",
            get_identifier(year, month, suffix)
        )

    os.makedirs(
        os.path.dirname(get_path(1)),
        exist_ok=True
    )

    async with aiohttp.ClientSession() as session:

        coroutines = []

        for suffix in range(1, 1 + maximum):
            path = get_path(suffix)
            identifier = get_identifier(year, month, suffix)

            if os.path.exists(path) and not overwrite:
                logger.info(f"Skipping {identifier} because {path} exists")
                continue
            
            coroutines.append(get_record(session, identifier))

            if (suffix % 4) == 0:
                while len(coroutines) > 0:
                    coroutine = coroutines.pop()
                    metadata = await coroutine
                    record = parse_arxiv_response(metadata)

                    prefix, suffix = record["id"].split(".")
                    path = get_path(int(suffix))

                    with open(path, "w") as fp:
                        json.dump(dict(record), fp)


def parse_arxiv_response(content):
        
    parsed_content = xml.parse(content)
    record = parsed_content["OAI-PMH"]["GetRecord"]["record"]
    
    metadata = record["metadata"]["arXiv"]
    for k in ('@xmlns', '@xmlns:xsi', '@xsi:schemaLocation', "license"):
        del metadata[k]
    
    assert len(metadata["authors"]) == 1

    authors = []
    _author = metadata["authors"]["author"]
    if not isinstance(_author, list):
        _author = [_author]
    
    for author in _author:
        authors.append((author.get("forenames", ""), author.get("keyname", "")))
    
    metadata["authors"] = authors
    
    return metadata




if __name__ == "__main__":

    from astropy.table import Table

    submissions = Table.read("arxiv_monthly_submissions.csv")



    async def get_jan_to_apr(year):

        tasks = []
        for month in (1, 2, 3, 4):
            maximum = submissions["submissions"][submissions["month"] == f"{year:.0f}-{month:0>2.0f}"][0]

            logger.info(f"Searching {year}-{month:0>2.0f} up to {maximum} articles")
            tasks.append(
                asyncio.ensure_future(
                    get_monthly_records(
                        year, 
                        month,
                        maximum=maximum
                    )
                )
            )

        for task in tasks:
            await task
        
        return None


    async def main():
        
        response = await get_jan_to_apr(2019)
        return response

        


    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(main())
    finally:
        event_loop.close()

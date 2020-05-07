import asyncio
import aiohttp
import warnings
import logging
import json
import time
import os
import xmltodict as xml
from numpy import ceil
from tqdm import tqdm

from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

overwrite = False
_records_path = "records"


def get_path(year, month, suffix):
    return os.path.join(
        _records_path,
        f"{year % 2000:0>2.0f}",
        f"{month:0>2.0f}",
        get_identifier(year, month, suffix)
    )

def get_identifier(year, month, suffix):
    return f"{year % 2000:0>2.0f}{month:0>2.0f}.{suffix:0>5.0f}"


async def get_record(session, identifier, max_attempts=5):
    logger.debug(f"Searching for arXiv identifier {identifier}")

    connection_error_timeout = 60

    params = dict(
        verb="GetRecord",
        identifier=f"oai:arXiv.org:{identifier}",
        metadataPrefix="arXiv"
    )
    uri = "http://export.arxiv.org/oai2"

    for attempt in range(1, 1 + max_attempts):
            
        try:
            async with session.get(uri, params=params) as response:
                content = await response.read()
                if isinstance(content, bytes):                
                    content = content.decode("utf-8")

        except asyncio.TimeoutError:
            logger.debug(f"asyncio.TimeoutError on {identifier} search (attempt {attempt} of {1 + max_attempts})")
            await asyncio.sleep(connection_error_timeout)
            continue

        except aiohttp.ServerDisconnectedError:
            logger.debug(f"aiohttp.ServerDisconnectedError on {identifier}")
            await asyncio.sleep(connection_error_timeout)
            continue

        except:
            logger.exception(f"Unexpected exception occurred on identifier {identifier} ({attempt} of {1 + max_attempts})")
            await asyncio.sleep(connection_error_timeout)
            
        else:
            try:
                record = parse_arxiv_response(content)
                
            except:
                logger.exception(f"Failed to parse arXiv {identifier}:")

                if "<h1>Retry after 600 seconds</h1>" in content:
                    logger.exception(f"Content: {content}")
                    logger.info("Waiting 600 seconds to retry")
                    await asyncio.sleep(600)
                    continue

                else:
                    raise
                
            else:
                break
    
    else:
        # Totally failed after max attempts.
        raise

    if record is None:
        return record

    prefix, suffix = record["id"].split(".")
    year, month = (int(f'20{prefix[:2]}'), int(prefix[2:]))
    
    path = get_path(year, month, int(suffix))

    with open(path, "w") as fp:
        json.dump(dict(record), fp)

    return record



async def get_monthly_records(session, year, month, maximum, max_attempts=5):

    year, month = (int(year), int(month))

    os.makedirs(
        os.path.dirname(get_path(year, month, 1)),
        exist_ok=True
    )

    for suffix in range(1, 1 + maximum):
        path = get_path(year, month, suffix)
        identifier = get_identifier(year, month, suffix)

        if os.path.exists(path) and not overwrite:
            logger.info(f"Skipping {identifier} because {path} exists")
            continue
        
        yield get_record(session, identifier, max_attempts=max_attempts)


        
def parse_arxiv_response(content):
        
    parsed_content = xml.parse(content)
    oai_pmh = parsed_content["OAI-PMH"]
    if "error" in oai_pmh:
        logger.warn(f"Error received: {oai_pmh['error'].get('#text', None)}")
        return None
    
    record = oai_pmh["GetRecord"]["record"]
    
    if "metadata" not in record:
        return None

    metadata = record["metadata"]["arXiv"]
    for k in ('@xmlns', '@xmlns:xsi', '@xsi:schemaLocation', "license"):
        metadata.pop(k, None)
    
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

    max_attempts = 50


    async def get_yearly(year, months=None, concurrency=10):

        if months is None:
            months = range(1, 13)

        tasks = []
        async with aiohttp.ClientSession() as session:
                
            for month in months:
                maximum = submissions["submissions"][submissions["month"] == f"{year:.0f}-{month:0>2.0f}"][0]

                logger.info(f"Searching {year}-{month:0>2.0f} up to {maximum} articles")

                async for coroutine in get_monthly_records(
                        session,
                        year, 
                        month, 
                        maximum=maximum,
                        max_attempts=max_attempts
                    ):
                    tasks.append(coroutine)

            B = len(tasks)
            num_batches = int(ceil(B / concurrency))
            with tqdm(total=B, desc=f"Querying {year} identifiers") as pbar:
                for i in range(num_batches):                
                    si, ei = (i * concurrency, (i + 1) * concurrency)
                    await asyncio.gather(*tasks[si:ei])
                    pbar.update(concurrency)
        
        return None


    async def main():

        #response = await get_yearly(2018)

        concurrency = 10
        months = None

        for year in list(range(2008, 2020 + 1)):
            if year == 2020:
                months = (1, 2, 3, 4)
            else:
                months = None
            response = await get_yearly(
                    year, 
                    months=months,
                    concurrency=concurrency
                )

        return response

        


    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(main())
    finally:
        event_loop.close()

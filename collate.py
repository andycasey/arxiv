""" Collate results into a table. """

import logging
import json
import gender_guesser.detector as gender
from collections import Counter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

overwrite = False
_records_path = "records"

gd = gender.Detector()

def process_record(path, all_authors=True, drop_mostly=True):
    with open(path, "r") as fp:
        record = json.load(fp)

    meta = record.copy()


    authors = meta["authors"]
    meta["num_authors"] = len(authors)

    # Category stuff.
    categories = meta["categories"].split(" ")
    primary_category = categories[0]
    meta.update(
        num_categories=len(categories),
        primary_category=primary_category,
        primary_parent_category=primary_category.split(".")[0]
    )

    # Speculate on gender.
    meta.update(
        first_author=", ".join(authors[0][::-1]),
        last_author=", ".join(authors[-1][::-1]),
        first_author_gender=gd.get_gender(authors[0][0]),
        last_author_gender=gd.get_gender(authors[-1][0])
    )
    
    # Infer gender for all authors?
    if all_authors:
            
        genders = []
        for first_name, last_name in authors:
            genders.append(gd.get_gender(first_name))
        
        counts = Counter(genders)

        possible_responses = ('andy', 'female', 'male', 'mostly_female', 'mostly_male', 'unknown')
        for pr in possible_responses:
            counts.setdefault(pr, 0)

        if drop_mostly:
            counts["male"] += counts.pop("mostly_male")
            counts["female"] += counts.pop("mostly_female")

        for gender, count in counts.items():
            meta[f"num_{gender}_gender"] = count

    # Drop unnecessary keys
    drop_keys = (
        "title", "abstract", "comments", "authors", "doi", "updated", "acm-class",
        "journal-ref",
        "msc-class",
        "proxy",
        "report-no"
    )
    for key in drop_keys:
        meta.pop(key, None)

    return meta




if __name__ == "__main__":

    from astropy.table import Table
    from glob import glob
    from tqdm import tqdm

    paths = glob("records/*/*/*")

    kwds = dict(
        all_authors=True, 
        drop_mostly=True
    )

    rows = []
    failures = []
    for path in tqdm(paths):
        try:
            row = process_record(
                path,
                **kwds
            )

        except:
            failures.append(path)
        
        else:
            rows.append(row)
    
    if failures:
        logger.warning(f"Failures on the following paths:")
        for failure in failures:
            logger.warning(f"\t{failure}")
    
    # Order the columns because it hurts my autism otherwise.
    names = [
        'id',
        'created',
        'primary_parent_category',
        'primary_category',
        'num_categories',
        'categories',
        'num_authors',
        'first_author',
        'first_author_gender',
        'last_author',
        'last_author_gender',
        'num_andy_gender',
        'num_female_gender',
        'num_male_gender',
        'num_unknown_gender',
    ]

    table = Table(rows=rows)
    if len(table.dtype.names) > len(names):
        logger.warning(f"Table has more columns than expected: {set(table.dtype.names).diffence(names)}")

    table = table[names]
    table.write(
        "records.csv",
        overwrite=True
    )

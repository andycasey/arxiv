""" Collate results into a table. """

import logging
import json
import gender_guesser.detector as gender
from collections import Counter
from unicodedata import normalize

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

overwrite = False
_records_path = "records"

gd = gender.Detector()
with open("gender_dictionary.json", "r") as fp:
    genderize_results = json.load(fp)


def normalize_name(name):
    return normalize("NFKD", name).encode("ASCII", "ignore").title().strip()

def sanitize_gender(gender):
    return gender or "unknown"

def speculate_gender(first_name):
    first_name = first_name.strip().title().split(" ")[0]
    
    for trial in (first_name, normalize_name(first_name)):
        try:
            r = genderize_results[trial]
            
        except KeyError:
            continue
        
        else:
            r["gender"] = sanitize_gender(r["gender"])
            return r


    gd_gender = gd.get_gender(first_name)
    if gd_gender.startswith("mostly_"):
        _, gd_gender = gd_gender.split("_")
        probability = 0.5
    
    elif gd_gender in ("andy", "unknown"):
        gd_gender = None
        probability = 0
    
    else:
        probability = 1.0
    
    return dict(
        gender=sanitize_gender(gd_gender),
        probability=probability,
        count=0
    )



def process_record(path, all_authors=True):
    with open(path, "r") as fp:
        record = json.load(fp)

    meta = record.copy()


    authors = meta["authors"]
    meta["num_authors"] = len(authors)

    # Category stuff.
    categories = meta["categories"].split(" ")
    primary_category = categories[0]

    meta.update(
        words_in_abstract=len(meta["abstract"].split(" ")),
        first_10_authors="; ".join([", ".join(author[::-1]) for author in authors[:10]]),
        num_categories=len(categories),
        primary_category=primary_category,
        primary_parent_category=primary_category.split(".")[0]
    )

    # Speculate on gender.
    meta.update(
        first_author=", ".join(authors[0][::-1]),
        last_author=", ".join(authors[-1][::-1]),
        first_author_gender=speculate_gender(authors[0][0])["gender"],
        last_author_gender=speculate_gender(authors[-1][0])["gender"]
    )
    
    # Infer gender for all authors?
    if all_authors:
            
        genders = []
        for first_name, last_name in authors:
            genders.append(speculate_gender(first_name)["gender"])
        
        counts = Counter(genders)

        #possible_responses = ('andy', 'female', 'male', 'mostly_female', 'mostly_male', 'unknown')
        for pr in (None, "male", "female"):
            counts.setdefault(pr, 0)

        for gender, count in counts.items():
            meta[f"num_{gender or 'unknown'}_gender"] = count

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
    from collections import Counter

    paths = glob("records/*/*/*")



    kwds = dict(
        all_authors=True, 
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
            raise 
        
        else:
            if row is not None:
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
        'num_female_gender',
        'num_male_gender',
        'num_unknown_gender',
        'first_10_authors',
        'words_in_abstract'
    ]

    table = Table(rows=rows)
    #if len(table.dtype.names) > len(names):
    #    logger.warning(f"Table has more columns than expected: {set(table.dtype.names).diffence(names)}")
   
    #v = table[["id", "created", "categories", "num_authors", "first_10_authors", "words_in_abstract"]]
    v = table[names]
    v.sort("id")
    v.write("metadata.csv")
    print("done")
    raise a
    table = table[names]
    table.write(
        "records.v1.csv",
        overwrite=True
    )

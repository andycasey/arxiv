
import json

def process_record(path, include_authors=False):

    with open(path, "r") as fp:
        record = json.load(fp)

    meta = record.copy()

    authors = meta["authors"]

    # Category stuff.
    categories = meta["categories"].split(" ")
    primary_category = categories[0]

    meta.update(
        words_in_abstract=len(meta["abstract"].split(" ")),
        num_categories=len(categories),
        num_authors=len(authors),
        primary_category=primary_category,
        primary_parent_category=primary_category.split(".")[0],
        first_author=authors[0]
    )

    if include_authors:
        meta.update(
            #first_10_authors="; ".join([", ".join(author[::-1]) for author in authors[:10]]),
            all_authors="; ".join([", ".join(author) for author in authors]),
            #first_author=", ".join(authors[0][::-1]),
            #last_author=", ".join(authors[-1][::-1]),
        )
    
    # Drop unnecessary keys
    drop_keys = (
        "title", 
        "abstract", 
        "comments", 
        "authors",
        "doi",
        "updated",
        "acm-class",
        "journal-ref",
        "msc-class",
        "proxy",
        "report-no"
    )
    for key in drop_keys:
        meta.pop(key, None)

    return meta




if __name__ == "__main__":

    from glob import glob
    from tqdm import tqdm
    from astropy.table import Table

    debug = False
    max_records = None
    include_authors = True
    output_records_path = "records.csv"
    output_authors_path = "authors.json"

    paths = glob("records/*/*/*")

    rows = []
    failures = []
    for i, path in enumerate(tqdm(paths), start=1):
        try:
            row = process_record(path, include_authors=include_authors)
            
        except:
            failures.append(path)
            if debug:
                raise 
        
        else:
            if row is not None:
                rows.append(row)
    
        if max_records is not None and i >= max_records:
            break

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
        'words_in_abstract'
    ]
    if include_authors:
        authors = {
            record["id"]: record["all_authors"].split("; ") for record in records
        }

        with open(output_authors_path, "w") as fp:
            fp.write(json.dumps(authors, indent=1))


    records = Table(rows=rows, names=names)
    records.sort("id")
    records.write(output_records_path)
    
    
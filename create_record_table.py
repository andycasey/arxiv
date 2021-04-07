
ifmport json



def process_record(path):

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
        all_authors="; ".join([", ".join(author[::-1]) for author in authors]),
        num_categories=len(categories),
        primary_category=primary_category,
        primary_parent_category=primary_category.split(".")[0]
    )

    meta.update(
        first_author=", ".join(authors[0][::-1]),
        last_author=", ".join(authors[-1][::-1]),
    )
    
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

    from glob import glob
    from tqdm import tqdm
    from astropy.table import Table

    DEBUG = False

    paths = glob("records/*/*/*")

    rows = []
    failures = []
    for path in tqdm(paths):
        try:
            row = process_record(path)
            
        except:
            failures.append(path)
            if DEBUG:
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
        'last_author',
        'first_10_authors',
        'words_in_abstract'
    ]

    raise a
    #table = Table(rows=rows)

    #if len(table.dtype.names) > len(names):
    #    logger.warning(f"Table has more columns than expected: {set(table.dtype.names).diffence(names)}")
   
    #v = table[["id", "created", "categories", "num_authors", "first_10_authors", "words_in_abstract"]]
    v = table[names]
    v.sort("id")
    v.write("metadata.csv")
    
    names.pop('first_10_authors')
    names.append('all_authors')
    v2 = table[names]
    v2.write("metadata-all-authors.csv")
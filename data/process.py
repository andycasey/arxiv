
import json
import os
from tqdm import tqdm
from astropy.table import Table
from subprocess import getoutput

arxiv_dataset_path = "arxiv-metadata-oai-snapshot.json"
# Don't process any preprints from 1 June 2022 onwards.
end_date = (2022, 6)

dirname = os.path.dirname(os.path.abspath(__file__))
relative_path = lambda basename: os.path.join(dirname, basename)

with open(relative_path(arxiv_dataset_path), "r") as fp:
    preprints = map(json.loads, fp.readlines())

output = getoutput(f"wc {relative_path(arxiv_dataset_path)}")
total = int(output.strip().split()[0])

records = []
# Add dummy line.
records.append({
    "id": "dummy",
    "primary_parent_category": "",
    "primary_category": "",
    "num_categories": 0, 
    "categories": "",
    "num_authors": 0,
    "num_affiliations": 0,
    "words_in_abstract": 0
})

metadata = {}
authors = {}
for preprint in tqdm(preprints, total=total):
    if end_date is not None:
        yymm = preprint["id"].split(".")[0]
        yy, mm = (int(f"20{yymm[:2]}"), int(yymm[2:]))
        end_year, end_month = end_date
        if yy >= end_year and mm >= end_month:
            print(f"Reached {preprint['id']} stopping because end date is {end_date}")
            break

    affiliations = [author[-1] for author in preprint["authors_parsed"]]
    metadata[preprint["id"]] = {
        "title": preprint["title"],
        "abstract": preprint["abstract"],
        "affiliations": affiliations
    }

    these_authors = []
    for author in preprint["authors_parsed"]:
        keep = [name for name in author if name != "" and " and " not in name and list(set(name)) != ["I"]]
        these_authors.append(keep[:2])

    authors[preprint["id"]] = these_authors

    created = preprint['versions'][0]["created"]
    categories = preprint["categories"].split()
    primary_parent_category = categories[0].split(".")[0]

    record = {
        "id": preprint["id"],
        "primary_parent_category": primary_parent_category,
        "primary_category": categories[0],
        "num_categories": len(categories),
        "categories": preprint["categories"],
        "num_authors": len(preprint["authors_parsed"]),
        "num_affiliations": sum([ea != "" for ea in affiliations]),
        "words_in_abstract": len(preprint["abstract"].strip().split()),
    }

    records.append(record)
    
records_table = Table(data=records)

metadata_path = relative_path("metadata.json")
authors_path = relative_path("authors.json")
records_path = relative_path("records.csv")

print(f"Writing metadata to {metadata_path}")
with open(metadata_path, "w") as fp:
    json.dump(metadata, fp, indent=2)

print(f"Writing authors to {authors_path}")
with open(authors_path, "w") as fp:
    json.dump(authors, fp, indent=2)

print(f"Writing records to {records_path}")
records_table.write(records_path, overwrite=True)
print("Done")

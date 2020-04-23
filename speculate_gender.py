import json

import numpy as np


def process_names(path, categories=None):
    with open(path, "r") as fp:
        record = json.load(fp)

    # Category stuff.
    primary_category, *_ = record["categories"].split(" ")
    primary_parent_category = primary_category.split(".")[0]
    if categories is not None and primary_parent_category not in categories:
        return None

    # Get author names.
    for given_names, last_name in record["authors"]:
        first_name = given_names.split(" ")[0].replace(".", "").strip()

        if len(first_name) > 1:
            yield first_name

    return None


def query_batch(names, batch_size=10):

    num_batches = int(ceil(len(names) / batch_size))
    for i in tqdm(range(num_batches), desc="Querying genderize.io"):        
        si, ei = (i * batch_size, (i + 1) * batch_size)

        yield genderize.get(names[si:ei])

    return None
        





if __name__ == "__main__":

    from astropy.table import Table
    from glob import glob
    from tqdm import tqdm
    from collections import Counter
    from genderize import Genderize
    from numpy import ceil
    import os

    paths = glob("records/*/*/*")

    # First pass to get all the names that we need to process.
    names = []
    for path in tqdm(paths, desc="Collecting names"):
        for name in process_names(
            path, 
            categories=("astro-ph", )
        ):
            names.append(name)

    unique_names = list(set(names))

    print(f"{len(names)} names ({len(unique_names)} unique)")

    with open("genderize.json", "r") as fp:
        api_key = json.load(fp)["api_key"]

    genderize = Genderize(
        api_key=api_key
    )

    overwrite = False
    tmp_dir = "tmp"
    os.makedirs(tmp_dir, exist_ok=True)

    batch_size = 10
    num_batches = int(ceil(len(unique_names) / 10))

    print(f"Need to make {num_batches} API calls")

    for i in tqdm(range(num_batches), desc="Querying genderize.io"):
        batch_path = os.path.join(tmp_dir, f"batch_{i}.json")
        if os.path.exists(batch_path) and not overwrite:
            continue

        si, ei = (i * batch_size, (i + 1) * batch_size)

        results = genderize.get(unique_names[si:ei])

        with open(batch_path, "w") as fp:
            json.dump(results, fp)
        
    
    results = []
    for i in tqdm(range(num_batches), desc="Collecting results"):
        batch_path = os.path.join(tmp_dir, f"batch_{i}.json")

        with open(batch_path, "r") as fp:
            results.extend(json.load(fp))

    # Let's check for special characters.
    from unicodedata import normalize

    additional_requests = []
    for result in tqdm(results):
        if result["gender"] is None:
            # Any special chars?
            normalized_name = normalize(
                "NFKD",
                result["name"]
            ).encode("ASCII", "ignore").title()

            if normalized_name != result["name"].encode("utf-8"):
                additional_requests.append(normalized_name)

    num_batches = int(ceil(len(additional_requests) / batch_size))
    for i in tqdm(range(num_batches), desc="Querying genderize.io for encoded names"):
        batch_path = os.path.join(tmp_dir, f"encoded_batch_{i}.json")
        if os.path.exists(batch_path) and not overwrite:
            continue
        
        si, ei = (i * batch_size, (i + 1) * batch_size)

        r = genderize.get(additional_requests[si:ei])
        
        with open(batch_path, "w") as fp:
            json.dump(r, fp)
    

    for i in range(num_batches):
        batch_path = os.path.join(tmp_dir, f"encoded_batch_{i}.json")
        with open(batch_path, "r") as fp:
            results.extend(json.load(fp))
    
    f = np.sum([ea["probability"] > 0 for ea in results])
    print(f"Gender guesses for {100 * f/len(results):.0f}% names")


    # Create a big ass dictionary.
    parsed_results = dict()
    for result in results:
        v = result.copy()
        v.pop("name")
        #assert result["name"] not in parsed_results
        parsed_results[result["name"]] = v

    print(f"Len results: {len(results)} and len parsed results {len(parsed_results)}")

    
    missed = list(set(names).difference(parsed_results))
    for result_ in query_batch(missed):
        for result in result_:
            v = result.copy()
            v.pop("name")
            parsed_results[result["name"]] = v

    for name in names:
        assert name in parsed_results

    with open("gender_dictionary.json", "w") as fp:
        json.dump(parsed_results, fp, indent=2)



    


    
import numpy as np
import matplotlib.pyplot as plt
import json
from astropy.table import Table
from astropy.time import Time
from collections import OrderedDict
from tqdm import tqdm

def load_metadata(path="data/metadata.json"):
    with open(path, "r") as fp:
        metadata = json.load(fp)
    return metadata


def load_records(path="data/records.csv"):

    records = Table.read(path)
    # Ignore the dummy line, if it exists.
    if records["id"][0] == "dummy":
        records = records[1:]

    # Exclude old-style
    #mask = np.array(["/" in id_ for id_ in records["id"]])
    #records = records[~mask]

    # Let's add some useful columns.
    if "created" in records.dtype.names:
        records["created_decimal_year"] = Time(records["created"]).decimalyear
    else:
        records["created_decimal_year"] = list(map(get_decimal_date, records["id"]))

    return records


def pad_edges(bin_edges, counts):
    if bin_edges.size == (counts.size + 1):
        x = np.hstack([
            bin_edges[0],
            bin_edges[:-1] + 0.5 * np.diff(bin_edges),
            bin_edges[-1] 
        ])
        y = np.hstack([
            counts[0],
            counts,
            counts[-1]
        ])

    else:
        x = np.hstack([
            bin_edges[0] - 0.5 * np.diff(bin_edges[:2]),
            bin_edges,
            bin_edges[-1] + 0.5 * np.diff(bin_edges[-2:])
        ])
        y = np.hstack([
            counts[0],
            counts,
            counts[-1]
        ])

    return (x, y)


def load_authors(path="data/authors.json"):
    with open(path, "r") as fp:
        authors = json.load(fp)
    return authors
    

# How we will define a 'unique' author.
def unique_ify(author_name, debug=False):
    try:
        last, given = author_name
    except:
        try:
            response = author_name[0]
        except:
            response = ""

        if debug: print(response)
        return response

    
    if last.count(".") > 0 and given.count(" ") == 1:
        if debug: print(author_name, given, last)
        #0704.1276 Pavlenko Elena P.
        
        given, last = given.split()
        # Concatnate the second initial
        given += f" {author_name[0]}"

        if debug: print(f"\tnow {given} {last}")
    try:
        first_initial = f"{given[0].strip()[:1]}."
    except IndexError:
        response = f"{last.strip()}"
    else:
        response = f"{last.strip()}, {first_initial}"

    if debug: print(response)
    return response
    
# Get date (to ~month granularity) from an arxiv ID
get_date = lambda arxiv_id: (int(f"20{arxiv_id[:2]}"), int(arxiv_id[2:4]))
def get_decimal_date(arxiv_id):
    year, month = get_date(arxiv_id)
    return year + (month - 1)/12


## Number of papers with N given authors as a function of time.
def get_number_of_authors_with_time(
        records,
        author_bins,
        primary_parent_category
    ):

    if primary_parent_category is not None:
        parent_mask = (records["primary_parent_category"] == primary_parent_category)
    else:
        parent_mask = np.ones(len(records), dtype=bool)

    idx = np.digitize(records["num_authors"], bins=author_bins) - 1
    
    # Ignore things that are outside the bounds of the bins.
    ignore = records["num_authors"] > max(author_bins)
    idx[ignore] = -1

    data = OrderedDict()
    for i, value in enumerate(author_bins):        
        mask = parent_mask * (idx == i)
        data[value] = np.array(records["created_decimal_year"][mask])
         
    return data
    
def get_time_bins(year_min=2007, year_max=2021, n_bins_per_year=12):
    n_bins = n_bins_per_year * (year_max - year_min) + 1
    return np.linspace(year_min, year_max, n_bins)
    
def in_a_not_appeared_before_in_b(
        subset_a_ids, 
        subset_b_ids, 
        all_author_records,
        func=None,
        bins=np.arange(2008, 2021, 1/12),
        pre_computed_subset_b_sets=None,
        full_output=False
    ):

    if func is None:
        func = lambda N_new, N_authors: N_new == N_authors

    if isinstance(subset_a_ids, (tuple, list)):
        subset_a_ids = np.array(subset_a_ids)

    a_dates = np.array(list(map(get_decimal_date, subset_a_ids)))
    a_idx = np.digitize(a_dates, bins)
    
    if pre_computed_subset_b_sets is None:
        b_dates = np.array(list(map(get_decimal_date, subset_b_ids)))
        b_idx = np.digitize(b_dates, bins)

    count = np.zeros(bins.size - 1)
    a_count = np.zeros(bins.size - 1)
    b_count = np.zeros(bins.size - 1)
    compute_b_sets = []
    
    has_appeared = []
    for i, bin_edge in enumerate(tqdm(bins[:-1])):
        a_mask = (a_idx == (i + 1))

        for arxiv_id in subset_a_ids[a_mask]:

            these_authors = list(map(unique_ify, all_author_records[arxiv_id]))

            new_names = set(these_authors).difference(has_appeared)
            has_appeared.extend(list(new_names))

            N_new = len(new_names)
            N_authors = len(set(these_authors))

            if func(N_new, N_authors, arxiv_id, these_authors, new_names):
                count[i] += 1

        a_count[i] = sum(a_mask)

        if pre_computed_subset_b_sets is None:
            # Now add names that have appeared in the b-subset so future bins are right.
            b_mask = (b_idx == (i + 1))
            this_set = []
            for arxiv_id in subset_b_ids[b_mask]:
                new_names = set(map(unique_ify, all_author_records[arxiv_id])).difference(has_appeared)
                this_set.extend(list(new_names))

            b_count[i] = sum(b_mask)

            has_appeared.extend(this_set)

            if full_output:
                compute_b_sets.append(this_set)

        else:
            has_appeared.extend(pre_computed_subset_b_sets[i])
            b_count[i] = len(pre_computed_subset_b_sets[i])

    if full_output:
        return (bins, count, a_count, b_count, compute_b_sets)

    else:
        return (bins, count, a_count, b_count)



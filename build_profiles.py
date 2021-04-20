
import numpy as np
import matplotlib.pyplot as plt

import json
from tqdm import tqdm
from datetime import datetime
from collections import OrderedDict

from astropy.time import Time

date_format = "%Y-%M-%d"

with open('records.json', 'r') as fp:
    records = json.load(fp)

# Restrict to astro-ph, and sort.
records = filter(lambda record: record["primary_category"].startswith("astro-ph"), records)
records = sorted(records, key=lambda record: record["id"])

# Dict-ify.
records = OrderedDict([(record.pop("id"), record) for record in records])

# 'Unique-ify' authors.
def unique_ify(author_name):
    *given, last = author_name.split(",")
    initials = " ".join([f"{name[:1]}." for name in given])
    return f"{last.strip()}, {initials}"

# Build a quick profile on each unique name.

any_author_profiles = {}
for arxiv_id, record in tqdm(records.items()):

    # TODO: Build profile on first author names only?
    for author in map(unique_ify, record["all_authors"].split("; ")):
        any_author_profiles.setdefault(author, [])
        any_author_profiles[author].append((arxiv_id, record["created"]))

# How can we find 'dead' profiles?
dead_author_names = []
for author_name, profile in tqdm(any_author_profiles.items()):

    # If they haven't published a first author paper in 3 years, and their total career span is less than 5 years,
    # then let's say dead.
    if len(profile) > 1 and (Time("2021-04-15") - Time(profile[-1][1])).value >= 3 * 365 \
    and (Time(profile[-1][1]) - Time(profile[0][1])).value <= (5 * 365):
        dead_author_names.append(author_name)



# We need to calculate summary statistics for every author so that we can test predictors.
Ns = (3, 5, 10) # years
metrics = {}
for author_name, profile in tqdm(any_author_profiles.items()):
    times = Time([date for arxiv_id, date in profile])

    # career longevity
    t_s, t_e = (times.min(), times.max())
    metrics[author_name] = dict(longevity=(t_e - t_s).value)
    
    # Calculate number of papers within N years.
    for N in Ns:
        key = f"first_author_paper_within_{N}_years"

        metrics[author_name][key] = 0

        for arxiv_id, date in profile:
            first_author_name = unique_ify(records[arxiv_id]["all_authors"].split("; ")[0])
            if first_author_name == author_name and ((Time(date) - t_s).value / 365) <= N:
                metrics[author_name][key] += 1


# Let's look at the metrics for dead profiles, and let's just say you need to do better than that.

fig, axes = plt.subplots(3)
for N, ax in zip(Ns, axes):
    x = np.array([metrics[name][f"first_author_paper_within_{N}_years"] for name in dead_author_names])

    ax.hist(x, bins=np.linspace(0, 10, 21))
    ax.set_title(N)

fig.savefig("tmp.png", dpi=300)


y = []
xs = { N: [] for N in Ns }
for author_name in dead_author_names:
    values = metrics[author_name]
    for N in Ns:
        xs[N].append(values[f"first_author_paper_within_{N}_years"])
    y.append(values["longevity"])

y = np.array(y)




fig, axes = plt.subplots(3)

for i, (ax, N) in enumerate(zip(axes, Ns)):
    ax.scatter(
        xs[N],
        y / 365.25,
        s=1,
        alpha=0.1
    )
    ax.set_title(f"N = {N}")


fig.tight_layout()
fig.savefig("tmp.png", dpi=300)
    

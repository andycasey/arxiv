from http.client import NOT_ACCEPTABLE
from sysconfig import is_python_build
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from tqdm import tqdm

from plot_utils import (load_records, load_authors, load_metadata, get_decimal_date, pad_edges, unique_ify)

matplotlib.style.use("matplotlibrc.paper")

try:
    (records, authors, metadata)
except NameError:
    records = load_records()
    authors = load_authors()
    metadata = load_metadata()
else:
    print("WARNING: Using pre-loaded data.")


xlim = (2014, 2023)
key = "primary_category"
is_physics = (records["primary_parent_category"] == "physics")

categories = set(records[key][is_physics])
N_categories = len(categories)

bin_width = 1/12
bins = np.arange(2010, max(records["created_decimal_year"]) + bin_width, bin_width)
t = bins[:-1] + 0.5 * np.diff(bins)[0]


fig, ax = plt.subplots()
H, bin_edges = np.histogram(records["created_decimal_year"][is_physics], bins)
ax.plot(
    t,
    H,
    drawstyle="steps-mid",
    c="k"
)

# show top most N
show_top_most_N = 22

K = 4
L = int(show_top_most_N/K)

fig, axes = plt.subplots(L, K, figsize=(10, 10))

#for j, group in enumerate(records[is_physics].group_by([key]).groups):
from collections import Counter
for j, (category, count) in enumerate(Counter(records[key][is_physics]).most_common(show_top_most_N)):

    group = records[is_physics * (records[key] == category)]
    try:
        ax = axes.flat[j]
    except IndexError:
        break
    sub_cat = category.split(".")[1]
    ax.set_title(r"$\textrm{{{0}}}$".format(sub_cat))

    ys = group["created_decimal_year"]
    
    H, bin_edges = np.histogram(group["created_decimal_year"], bins)
    
    # Build a model.

    ax.plot(
        t,
        H,
        drawstyle="steps-mid",
        c="k"
    )

for j, ax in enumerate(axes.flat[:show_top_most_N]):
    ax.set_xlim(xlim)
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.xaxis.set_major_locator(MaxNLocator(3))
    ax.xaxis.grid(True, linestyle="--")

    if ax.is_last_row():
        ax.set_xlabel(r"Year")
    else:
        ax.set_xticklabels([])
        ax.set_xlabel("")


for ax in axes.flat[show_top_most_N:]:
    ax.set_visible(False)

fig.tight_layout()

fig.savefig("article/physics-declines.png", dpi=300)


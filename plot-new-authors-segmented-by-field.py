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


# Hmm. Let's see how many 'new' names entered a field with time.
# That is to say: the name had never appeared in the literature until then.

bins = np.arange(2007, max(records["created_decimal_year"]) + 1/12, 1/12)

xlim = (bins[0], bins[-1])
xlim = (2017, 2023)


def get_new_authors(arxiv_ids, authors, callback=None):
    d = np.array(list(map(get_decimal_date, arxiv_ids)))
    idx = np.digitize(d, bins)
    
    y = np.zeros(bins.size - 1)
    z = np.zeros(bins.size - 1)
    has_appeared = []
    for i, bin_edge in enumerate(tqdm(bins[:-1])):
        mask = (idx == (i + 1))
        authors_in_bin = []
        for arxiv_id in arxiv_ids[mask]:
            authors_on_this = list(map(unique_ify, authors[arxiv_id]))
            authors_in_bin.extend(authors_on_this)
            z[np.digitize(get_decimal_date(arxiv_id), bins) - 1] += 1
            if callback is not None:
                N = len(set(authors_on_this).difference(has_appeared))
                if callback(bins[i], bins[i+1], N):
                    md = metadata[arxiv_id]
                    print(arxiv_id, N, md["title"])

        new_names = set(authors_in_bin).difference(has_appeared)
        y[i] = len(new_names)
        
        has_appeared.extend(list(new_names))

    return (y, z)


ignore_ppcs = ("econ", "eess")
ppcs = sorted(list(set(records["primary_parent_category"]).difference(ignore_ppcs)))

try:
    data_new_authors
    if len(data_new_authors) == 0:
        raise NameError

except NameError:
    # Build field-specific profiles
    data_new_authors = []
    for ppc in ppcs:
        mask = (records["primary_parent_category"] == ppc)

        kwds = dict()
        if ppc == "gr-qc":
            kwds.update(
                callback=lambda bin_left, bin_right, n: bin_left > 2012 and n > 100
            )
        
        elif ppc == "hep-lat":
            kwds.update(
                callback=lambda bl, br, n: bl > 2010 and n > 50
            )
        elif ppc == "hep-ex":
            kwds.update(
                callback=lambda bl, br, n: bl > 2010 and n > 50
            )
        elif ppc == "stat":
            kwds.update(
                callback=lambda bl, br, n: bl > 2020 and n > 1
            )

        y, z = get_new_authors(records["id"][mask], authors, **kwds)
        data_new_authors.append((ppc, y, z))
else:
    print("WARNING: Using pre-loaded data_new_authors")

"""
fig, axes = plt.subplots(6, 3, figsize=(6, 8))

for ppc, y, z in data_new_authors:
    try:
        i = ppcs.index(ppc)
    except ValueError:
        continue
    
    ax = axes.flat[i]
    ax.text(
        0.03, 
        0.95, 
        r"$\textrm{{{0}}}$".format(ppc), 
        transform=ax.transAxes, 
        verticalalignment="top",
        zorder=1000
    )

    ax.plot(
        bins[:-1],
        y,
        drawstyle="steps-mid",
        c="k",
        zorder=100
    )
    
    ax.set_xlim(*xlim)

for ax in axes.flat:
    ax.set_xlim(*xlim)
    ax.xaxis.set_major_locator(MaxNLocator(3))
    
    if ax.is_last_row():
        ax.set_xlabel(r"$\textrm{Year}$")
        ax.set_xticklabels([r"${:.0f}$".format(tick) for tick in ax.get_xticks()])
    else:
        ax.set_xticks([])

    ''' 
    ax.axvspan(
        2020, 
        2021,
        facecolor="#DDDDDD", 
        edgecolor=None,
        zorder=-1
    )
    '''
    ax.axvline(
        2020,
        c="#666666",
        lw=0.5,
        ls=":", zorder=-1
    )
        
# Add a common y-label.
fig.text(
    0.03, 
    0.5, 
    r"$\mathrm{Number~of~new~authors~appearing~on~arXiv~per~month~by~category}$",
    va="center", 
    rotation="vertical"
)
fig.tight_layout()
fig.subplots_adjust(left=0.13)#


fig.savefig("article/new-authors-segmented-by-field.pdf", dpi=300)    



fig, axes = plt.subplots(6, 3, figsize=(6, 8))

for ppc, y, z in data_new_authors:
    try:
        i = ppcs.index(ppc)
    except ValueError:
        continue
    
    ax = axes.flat[i]
    ax.text(
        0.03, 
        0.95, 
        r"$\textrm{{{0}}}$".format(ppc), 
        transform=ax.transAxes, 
        verticalalignment="top",
        zorder=100
    )

    ax.plot(
        bins[:-1],
        y/z,
        drawstyle="steps-mid",
        c="k"
    )
    
    ax.set_xlim(*xlim)

for ax in axes.flat:
    #ax.set_ylim(0, 10)
    ax.set_xlim(*xlim)
    ax.xaxis.set_major_locator(MaxNLocator(3))
    
    if ax.is_last_row():
        ax.set_xlabel(r"$\textrm{Year}$")
        ax.set_xticklabels([r"${:.0f}$".format(tick) for tick in ax.get_xticks()])
    else:
        ax.set_xticks([])

    ''' 
    ax.axvspan(
        2020, 
        2021,
        facecolor="#DDDDDD", 
        edgecolor=None,
        zorder=-1
    )
    '''
    ax.axvline(
        2020,
        c="#666666",
        lw=0.5,
        ls=":", zorder=-1
    )
        
# Add a common y-label.
fig.text(
    0.03, 
    0.5, 
    r"$\mathrm{Number~of~new~authors~appearing~on~arXiv~per~paper~per~month~by~category}$",
    va="center", 
    rotation="vertical"
)
fig.tight_layout()
fig.subplots_adjust(left=0.13)#

fig.savefig("article/new-authors-segmented-by-field-normalised.pdf", dpi=300)    
"""

year_lines = None


fig, axes = plt.subplots(6, 3, figsize=(6, 8))

for ppc, y, z in data_new_authors:
    try:
        i = ppcs.index(ppc)
    except ValueError:
        continue
    
    ax = axes.flat[i]
    ax.text(
        0.03, 
        0.95, 
        r"$\textrm{{{0}}}$".format(ppc), 
        transform=ax.transAxes, 
        verticalalignment="top",
        zorder=100
    )

    idx = bins.searchsorted(xlim[0])

    tax = ax.twinx()
    ax.patch.set_visible(False)
    ax.set_zorder(1)
    tax.set_zorder(0)
    lines = tax.plot(
        *pad_edges(bins[idx:], (y/z)[idx:]),
        drawstyle="steps-mid",
        c="tab:blue",
        lw=2, zorder=0
    )
    ax.plot(
        *pad_edges(bins[idx:], y[idx:]),
        drawstyle="steps-mid",
        c="k",
        alpha=0.75,
        zorder=100
    )
    tax.set_xlim(*xlim)
    tax.set_ylim(0, 6)
    tax.yaxis.set_major_locator(MaxNLocator(3))

    ax.set_xlim(*xlim)
    #tax.axis["right"].label.set_color(_.get_color())
    tax.yaxis.label.set_color(lines[0].get_color())
    

    tax.spines["right"].set_edgecolor(lines[0].get_color())
    tax.tick_params(axis='y', colors=lines[0].get_color())


    if not ax.is_last_col():
        tax.set_yticklabels([])


for ax in axes.flat:
    ax.xaxis.grid(True, ls="--")
    #ax.set_ylim(0, 10)
    ax.set_xlim(*xlim)
    ax.xaxis.set_major_locator(MaxNLocator(3))
    
    if ax.is_last_row():
        ax.set_xlabel(r"$\textrm{Year}$")
        ax.set_xticklabels([r"${:.0f}$".format(tick) for tick in ax.get_xticks()])
    else:
        ax.set_xticklabels([])


    ''' 
    ax.axvspan(
        2020, 
        2021,
        facecolor="#DDDDDD", 
        edgecolor=None,
        zorder=-1
    )
    '''
    
    if year_lines:
        for year in year_lines:
            ax.axvline(
                year,
                c="#666666",
                lw=0.5,
                ls=":", zorder=-1
            )
        
# Add a common y-label.
fig.text(
    0.03, 
    0.5, 
    r"$\mathrm{Number~of~new~authors~appearing~on~arXiv~per~month~by~category}$",
    va="center", 
    ha="center",
    rotation="vertical"
)
fig.text(
    0.97, 
    0.5, 
    r"$\mathrm{Number~of~new~authors~appearing~on~arXiv~per~pre}$-$\mathrm{print~per~month~by~category}$",
    color=lines[0].get_color(),
    va="center", 
    ha="center",
    rotation="vertical"
)
fig.tight_layout()
fig.subplots_adjust(left=0.11, right=0.90, wspace=0.40)

fig.savefig("article/new-authors-segmented-by-field-combined.pdf", dpi=300)    

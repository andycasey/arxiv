
import numpy as np
import matplotlib.pyplot as plt
from astropy.table import Table
from astropy.time import Time
from datetime import (datetime, timedelta)
from matplotlib import cm
from collections import Counter

records = Table.read("records.v2.csv")

# Calculate some things that will be useful.
if "week_number" not in records.dtype.names:
        
    t = Time(records["created"])
    dt = [each.datetime for each in t]

    records["year"] = [each.year for each in dt]
    records["month"] = [each.month for each in dt]
    records["week_number"] = [int(each.strftime("%V")) for each in dt]

    records.write("records.v2.csv", overwrite=True)


# Exclude 2007.
mask = (records["year"] != 2007)
records = records[mask]



# Now let's plot by year for each field.
fig, axes = plt.subplots(5, 4, figsize=(5 * 4, 4 * 4))
u = set(records["primary_parent_category"])
cmap = cm.get_cmap('tab20', len(u))
colors = { v: cmap(i) for i, v in enumerate(sorted(list(set(records["primary_parent_category"])))) }

for i, group in enumerate(records.group_by(["primary_parent_category"]).groups):

    ppc = group["primary_parent_category"][0]

    ax = axes.flatten()[i]
    ax.set_title(ppc)

    counts = Counter(group["year"])

    x = np.array(list(counts.keys()))
    y = np.array([counts[xi] for xi in x])

    # Normalize?
    #y = y / counts.get(2019, y[-1])

    ax.plot(
        x,
        y,
        c=colors[ppc],
        label=ppc,
    )

#ax.legend()
#ax.set_yscale("log")
#ax.set_ylim(1e2, ax.get_ylim()[-1])

fig.savefig("plot-all-fields.png", dpi=300)








for by_week_number in (True, False):
    
        

    # Let us group by primary parent category and plot number of submissions by month.

    fig, axes = plt.subplots(5, 4, figsize=(5 * 4, 4 * 4))

    cmap = cm.get_cmap('viridis', len(set(records["year"])))
    colors = { year: cmap(i) for i, year in enumerate(sorted(list(set(records["year"])))) }

    for i, group in enumerate(records.group_by(["primary_parent_category"]).groups):

        ppc = group["primary_parent_category"][0]

        ax = axes.flatten()[i]
        ax.set_title(ppc)

        print(ppc, len(group))

        for j, year_group in enumerate(group.group_by(["year"]).groups):

            year = year_group["year"][0]

            print(ppc, year, len(year_group))
            
            if by_week_number: # by week number.        
                bins = 0.5 + np.arange(0, 53)
                H, _ = np.histogram(
                    year_group["week_number"],
                    bins=bins
                )
            
            else:
                bins = 0.5 + np.arange(0, 13)
                H, _ = np.histogram(
                    year_group["month"],
                    bins=bins
                )
                
            ax.plot(
                bins[:-1],
                H,
                label=year,
                c=colors[year],
            )



    sm = plt.cm.ScalarMappable(
        cmap=cmap, 
        norm=plt.Normalize(
            vmin=records["year"][0],
            vmax=records["year"][-1]
        )
    )

    cbar = plt.colorbar(sm)

    if by_week_number:
        fig.savefig("plot-all-by-week-number.png")
    else:
        fig.savefig("plot-all-by-month.png")



if False:
    """

    # Plot each year-by-year (for each week).

    


    # Plot as a function of year (across all time).
    # Already sorted by ID.
    t_s, t_e = (t[0].datetime, t[-1].datetime)
    
    # Get monthly intervals.
    edges = [datetime(t_s.year, t_s.month, 1)]
    while True:
        n = edges[-1] + timedelta(days=32)
        edges.append(datetime(n.year, n.month, 1))
        if edges[-1] > t_e:
            break

    bins = [Time(edge).mjd for edge in edges]

    ppc = group["primary_parent_category"][0]

    mjd = t.mjd

    fig, ax = plt.subplots()
    ax.hist(mjd, bins=bins)

    fig.savefig(f"plot-{ppc}.png")


    raise a
    """
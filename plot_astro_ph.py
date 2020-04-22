
"""
What is the fraction of male-lead papers in astro-ph as a function of time?
"""

import matplotlib.pyplot as plt
import numpy as np
from astropy.table import Table
from astropy.time import Time

data = Table.read("records.csv")

# Restrict to astro-ph only.
mask = (table["primary_parent_category"] == "astro-ph")
data = data[mask]

# Deal with time nicely.
mjd = Time(data["created"]).mjd


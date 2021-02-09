
"""
What is the fraction of male-lead papers in astro-ph as a function of time?
"""

import matplotlib.pyplot as plt
import numpy as np
from astropy.table import Table
from astropy.time import Time
from tqdm import tqdm

data = Table.read("records.csv")

# Restrict to astro-ph only.
mask = (data["primary_parent_category"] == "astro-ph")
data = data[mask]

# Deal with time nicely.
mjds = Time(data["created"]).mjd


# Various statistics per day.
unique_mjd = np.arange(mjd.min(), 1 + mjd.max())
num_preprints = np.zeros_like(unique_mjd)
num_preprints_led_by_male = np.zeros_like(unique_mjd)
num_preprints_led_by_female = np.zeros_like(unique_mjd)
num_preprints_led_by_unknown_gender = np.zeros_like(unique_mjd)

raise a


for i, (mjd, preprint) in tqdm(enumerate(zip(mjds, data))):

    mask = (unique_mjd == mjd)
    num_preprints[mask] += 1
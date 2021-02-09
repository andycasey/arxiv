import numpy as np
import matplotlib.pyplot as plt
from astropy.table import Table
from astropy.time import Time

arxiv_downloads = Table.read("arxiv_monthly_downloads.csv")
arxiv_submissions = Table.read("arxiv_monthly_submissions.csv")


def year_fraction(string_months):
    return np.sum(
        [(np.array(ea.split("-"), dtype=int) - [0, 1])/[1, 12] for ea in string_months],
        axis=1
    )

arxiv_downloads["x"] = year_fraction(arxiv_downloads["month"])
arxiv_submissions["x"] = year_fraction(arxiv_submissions["month"])

fig, axes = plt.subplots(2, 1, sharex=True)
axes[0].plot(
    arxiv_downloads["x"],
    arxiv_downloads["downloads"],
    c="tab:red"
)
axes[0].set_ylabel(r"Downloads")
#axes[0].set_yscale("log")

axes[1].plot(
    arxiv_submissions["x"],
    arxiv_submissions["submissions"],
    c="tab:blue"
)
axes[1].set_ylabel(r"Submissions")
#axes[1].set_yscale("log")

fig.tight_layout()
raise a

s = np.interp(
    arxiv_downloads["x"],
    arxiv_submissions["x"],
    arxiv_submissions["submissions"]
)
x = arxiv_downloads["x"]
dts_ratio = arxiv_downloads["dts_ratio"] = arxiv_downloads["downloads"] / s



fig, axes = plt.subplots(1, 2)
axes[0].plot(
    x,
    dts_ratio,
    drawstyle="steps-mid"
)

for year in np.unique(x.astype(int)):
    if year < 2015:
        continue
    mask = x.astype(int) == year
    axes[1].plot(
        (x % 1)[mask],
        dts_ratio[mask],
        label=year
    )

fig.legend()

d = np.array(arxiv_downloads["downloads"])
year = x.astype(int)

fig, ax = plt.subplots()
scat = ax.scatter(s, 1 + d, c=year)
cbar = plt.colorbar(scat)
ax.set_yscale("log")


fig, ax = plt.subplots()
scat = ax.scatter(
    x,
    1 + d,
    c=s
)
plt.colorbar(scat)
ax.set_yscale("log")


pp = 2020
use_for_pred = (x >= 2000) * (x < pp)

t_ = x
y_ = np.log10(1 + d)
#y_ = 1 + d

import george
from george import kernels

t = t_[use_for_pred]
y = y_[use_for_pred]

var_y = np.var(y)
k1 = var_y * kernels.ExpSquaredKernel(metric=1)
k2 = var_y * kernels.ExpSquaredKernel(metric=1) \
           * kernels.ExpSine2Kernel(gamma=100, log_period=0.0)
kernel = k1 + k2
#kernel = k1

gp = george.GP(
    kernel, 
    white_noise=np.log(var_y),
    fit_white_noise=True
)
gp.compute(t)
pn = 'kernel:k2:k2:log_period'
if pn in gp.get_parameter_names():
    gp.freeze_parameter(pn)

#gp.freeze_parameter('kernel:k2:k2:log_period')

import scipy.optimize as op

def nll(p):
    gp.set_parameter_vector(p)
    ll = gp.log_likelihood(y, quiet=True)
    return -ll if np.isfinite(ll) else 1e25

def grad_nll(p):
    gp.set_parameter_vector(p)
    return -gp.grad_log_likelihood(y, quiet=True)

gp.compute(t)

# Print the initial ln-likelihood.
print(gp.log_likelihood(y))

# Run the optimization routine.
p0 = gp.get_parameter_vector()
results = op.minimize(nll, p0, jac=grad_nll, method="L-BFGS-B")

t_s = 2000
t_e = 2021
t_pred = np.linspace(t_s, t_e, 12 * (t_e - t_s) + 1)
y_pred, y_pred_var = gp.predict(y, t_pred, return_var=True)


descale = lambda _: 10**_ - 1

fig, ax = plt.subplots()
ax.scatter(t_, descale(y_))
ax.scatter(t, descale(y), c="tab:red")
ax.plot(t_pred, descale(y_pred), c="k")

ax.fill_between(
    t_pred,
    descale(y_pred - 2 * np.sqrt(y_pred_var)),
    descale(y_pred + 2 * np.sqrt(y_pred_var)),
    color="k", alpha=0.2
)

ax.set_yscale("log")


y_seasonal = gp.predict(
    y,
    t,
    return_cov=False,
    kernel=k1
)
y_yearly = gp.predict(
    y,
    t,
    return_cov=False,
    kernel=k2
)

fig, ax = plt.subplots()
ax.scatter(
    t % 1,
    y_yearly
)

from matplotlib import cm

fig, ax = plt.subplots()
ts = np.linspace(0, 1, 13)[:-1]
ys = np.zeros((ts.size, np.unique(t.astype(int)).size))

vmin, vmax = (np.min(t), np.max(t))
for i, year in enumerate(np.unique(t.astype(int))):
    mask = t.astype(int) == year

    col = cm.coolwarm((year - vmin)/(vmax - vmin))

    ax.plot(
        (t % 1)[mask],
        (y / y_seasonal)[mask],
        c=col,
    )

    ys[:, i] = np.interp(
        ts,
        (t % 1)[mask],
        (y / y_seasonal)[mask]
    )




fig, ax = plt.subplots()
ax.plot(
    ts,
    np.percentile(ys, 50, axis=1)
)
ax.fill_between(
    ts,
    *np.percentile(ys, [5, 95], axis=1),
    facecolor="k",
    alpha=0.2
)

# How many fewer downloads after COVID?
post_covid = (t_ >= 2020)
t_pc = t_[post_covid]
y_pred_pc, y_pred_pc_var = gp.predict(y, t_pc, return_var=True)

diff = descale(y_pred_pc) - descale(y_[post_covid])
print(f"There are {np.sum(diff):1.2e} fewer arXiv downloads in 2020 than expected.")

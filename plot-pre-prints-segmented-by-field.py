
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import george
import scipy.optimize as op
from george import kernels
from george.modeling import Model
from plot_utils import load_records, load_metadata, get_decimal_date, pad_edges
from statsmodels.tsa.arima.model import ARIMA
from matplotlib.ticker import MaxNLocator

matplotlib.style.use("matplotlibrc.paper")

try:
    records, metadata
except NameError:
    records = load_records()
    metadata = load_metadata()

else:
    print("WARNING: Using pre-loaded records.")


show_arima = True

bin_width = 1/12
try:
    counts
except NameError:
        
    # Plot submissions by time for each field.
    ignore_ppcs = ("econ", "eess")

    ppcs = sorted(list(set(records["primary_parent_category"]).difference(ignore_ppcs)))

    counts = {}
    totals = {}

    bins = np.arange(2010, max(records["created_decimal_year"]) + bin_width, bin_width)

    xlim = (bins[0], int(np.ceil(bins[-1])))
    patterns = ("pandemic", "covid", "sars-cov-2", "lockdown")

    for ppc in ppcs:
        print(ppc)

        counts[ppc] = np.zeros_like(bins)
        totals[ppc] = np.zeros_like(bins)
        
        mask = (records["primary_parent_category"] == ppc)

        for arxiv_id in records["id"][mask]:
            date = get_decimal_date(arxiv_id)
            if date < bins[0] or date > bins[-1]:
                continue

            idx = np.digitize(date, bins)
            totals[ppc][idx] += 1

            md = metadata[arxiv_id]
            context = f"{md['title']} {md['abstract']}".lower()
            for pattern in patterns:
                if pattern in context:
                    counts[ppc][idx] += 1
                    break

else:
    print("WARNING: Using pre-determined counts")


xlim = (2010, 2023)

class LineModel(Model):
    parameter_names = ("m", "b")
    
    def get_value(self, t):
        t = t.flatten()
        return t * self.m + self.b


shape = (len(ppcs), len(bins) - 1)
num_preprints = np.zeros(shape)
num_preprints_pred = np.zeros(shape)
num_preprints_var = np.zeros(shape)
statistics = {}

reports = []

fig, axes = plt.subplots(6, 3, figsize=(6, 8))
assert len(axes.flat) >= len(ppcs)

for j, group in enumerate(records.group_by(["primary_parent_category"]).groups):
    
    ppc = group["primary_parent_category"][0]

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
    )

    ys = group["created_decimal_year"]
    
    H, bin_edges = np.histogram(group["created_decimal_year"], bins)
    
    num_preprints[i] = H

    # Build a model.
    t = bins[:-1] + 0.5 * np.diff(bins)[0]
    use_for_pred = (t < 2020) * (t >= 2015)

    t = t[use_for_pred]
    y = H[use_for_pred].astype(float)


    #k1 = np.var(y) * kernels.ExpSquaredKernel(10**2)
    #k2 = 0.1 * np.var(y) * kernels.ExpSquaredKernel(metric=20**2, metric_bounds=[(np.log(5), np.inf)]) \
    #         * kernels.ExpSine2Kernel(gamma=1.0, log_period=0)
    
    kernel = np.var(y) * kernels.ExpSine2Kernel(gamma=1, log_period=0) \
           * kernels.ExpSquaredKernel(metric=10.0, metric_bounds=[(np.log(5), np.inf)])

    A = np.vstack([
        np.ones_like(t),
        t
    ]).T
    Y = y.reshape((-1, 1))

    X_hat = np.linalg.inv(A.T @ A) @ (A.T @ Y)
    b, m = X_hat.T[0]

    gp = george.GP(
        kernel, 
        mean=LineModel(b=b, m=m), 
        fit_mean=True,
        white_noise=np.log(np.var(y)),
        fit_white_noise=True
    )
    gp.compute(t)


    for pn in gp.get_parameter_names():
        if "log_period" in pn:
            gp.freeze_parameter(pn)


    def nll(p):
        gp.set_parameter_vector(p)
        ll = gp.log_likelihood(y, quiet=True)
        return -ll if np.isfinite(ll) else 1e25

    def grad_nll(p):
        gp.set_parameter_vector(p)
        return -gp.grad_log_likelihood(y, quiet=True)

    gp.compute(t)

    # Run the optimization routine.
    p0 = gp.get_parameter_vector()
    results = op.minimize(
        nll, 
        p0, 
        #jac=grad_nll, # Doesn't work with LineModel() for some reason
        method="L-BFGS-B",
        options=dict(ftol=1e-2)
    )

    pred_as_bins = True
    t_s, t_e = (2020, 2022.5)

    if pred_as_bins:
        t_pred = np.arange(t_s + 0.5 * bin_width, t_e + 0.5 * bin_width, bin_width)
        y_pred, y_pred_var = gp.predict(y, t_pred, return_var=True)

        tx = np.arange(t_s, t_e + bin_width, bin_width)
        ax.plot(
            *pad_edges(tx, y_pred),
            c="tab:red",
            drawstyle="steps-mid",
            zorder=-1
        )

        _, lo = pad_edges(tx, y_pred - np.sqrt(y_pred_var))
        _, up = pad_edges(tx, y_pred + np.sqrt(y_pred_var))

        ax.fill_between(
            _,
            lo,
            up,
            step="mid",
            facecolor="tab:red",
            edgecolor=None,
            zorder=0,
            alpha=1,
            lw=0
        )


    else:
            
        t_pred = np.arange(t_s, t_e + npy, npy)
        y_pred, y_pred_var = gp.predict(y, t_pred, return_var=True)

        ax.plot(
            t_pred, y_pred,
            c="tab:red",
            drawstyle="steps-mid",
            zorder=1
        )

        ax.fill_between(
            t_pred,
            y_pred - np.sqrt(y_pred_var),
            y_pred + np.sqrt(y_pred_var),
            step="mid",
            facecolor="tab:red",
            edgecolor=None,
            zorder=0,
            alpha=0.75,
            lw=0
        )


    '''
    ax.plot(
        bins,
        counts[ppc],
        c="k",
        drawstyle="steps-mid",
        lw=1,
        alpha=0.5
    )
    '''

    ax.plot(
        *pad_edges(bins, H),
        c="k",
        alpha=0.95,
        drawstyle="steps-mid",
        label=ppc,
        zorder=10
    )

    if show_arima:
        arima_model = ARIMA(y, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12)).fit()
        y_pred_arima = arima_model.predict(start=y.size, end=y.size + t_pred.size - 1, dynamic=True)
        ax.plot(
            t_pred,
            y_pred_arima,
            c="#666666",
            lw=1,         
            ls="-.",  
            zorder=2
        )

    
    # Let's calculate some statistics.
    N_preprints_in_2020 = np.sum(H[(2021 > bins[:-1]) * (bins[:-1] >= 2020)])
    pred_mask = (2021 > t_pred) * (t_pred >= 2020)
    N_predicted_in_2020 = np.sum(y_pred[pred_mask])
    
    u_pred_in_2020 = np.sum((y_pred + np.sqrt(y_pred_var))[pred_mask]) - N_predicted_in_2020
    
    diff = (N_preprints_in_2020 - N_predicted_in_2020)/u_pred_in_2020


    N_preprints_in_2019 = np.sum(H[(2020 > bins[:-1]) * (bins[:-1] >= 2019)])
    percent_change = 100 * (N_preprints_in_2020/N_preprints_in_2019 - 1)
    print(f"{ppc} had {N_preprints_in_2020} pre-prints in 2020 (expected {N_predicted_in_2020:.0f}; {u_pred_in_2020:+.0f}, {u_pred_in_2020:.0f}), a {diff:+.1f} sigma deviation or {percent_change:+.1f}% change)")
    
    reports.append(f"\\texttt{{{ppc: >50}}}  & {N_predicted_in_2020:,.0f} $\pm$ {u_pred_in_2020:,.0f} & {diff:+.1f}")

    statistics[ppc] = dict(
        N_preprints_in_2020=N_preprints_in_2020,
        N_preprints_in_2019=N_preprints_in_2019,
        yoy_change_2019_2020=percent_change,
        N_predicted_in_2020=N_predicted_in_2020,
        u_N_predicted_in_2020=u_pred_in_2020,
        pv=y_pred_var[pred_mask],
        sigma_deviation=diff
    )


    
for ax in axes.flat:
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
        xlim[1],
        facecolor="#DDDDDD", 
        edgecolor=None,
        zorder=-1
    )
    '''
    '''
    ax.axvline(
        2020,
        c="#666666",
        lw=0.5,
        ls=":", zorder=-1
    )
    ax.axvline(
        2021,
        c="#666666",
        lw=0.5,
        ls=":", zorder=-1
    )
    '''

# Adjust y-limits so that they all start at zero, but we keep a nice aspect ratio.
if True:#True:
    for ax in axes.flat:
        lims = ax.get_ylim()
        ptp = np.ptp(lims)
        ax.set_ylim(0, lims[0] + ptp + lims[0])

for ax in axes.flat:
    ax.xaxis.grid(True, linestyle="--")

# Add a common y-label.
fig.text(
    0.03, 
    0.5, 
    r"$\mathrm{Number~of~pre}$-$\mathrm{prints~posted~to~arXiv~per~month~by~category}$",
    va="center", 
    rotation="vertical"
)
fig.tight_layout()
fig.subplots_adjust(left=0.13)

plt.show()

fig.savefig("article/pre-prints-segmented-by-field.pdf", dpi=300)

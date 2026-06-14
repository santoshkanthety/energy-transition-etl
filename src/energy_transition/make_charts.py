"""Render the gold-layer charts used in the README.

Reads two small JSON extracts from the gold tables and writes PNGs to assets/.
Kept dependency-light (matplotlib only) so it runs anywhere the repo is cloned.
Regenerate after a pipeline run by re-exporting the JSON and running this file.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, DateFormatter
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)

INK = "#0b1f3a"
GREEN = "#2e8b57"
BLUE = "#3a7ca5"
GREY = "#9aa0a6"
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#d0d4d9",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "#eef1f4",
    "figure.dpi": 160,
})

# ---- 1. National transition trend -----------------------------------------
nat = json.load(open("/tmp/national.json"))
dates = [datetime.strptime(r[0], "%Y-%m-%d") for r in nat]
ren = [float(r[1]) * 100 for r in nat]
clean = [float(r[2]) * 100 for r in nat]
fossil = [float(r[3]) * 100 for r in nat]

fig, ax = plt.subplots(figsize=(9, 4.2))
ax.fill_between(dates, ren, color=GREEN, alpha=0.12)
ax.plot(dates, fossil, color=GREY, lw=2, label="Fossil")
ax.plot(dates, clean, color=BLUE, lw=2, label="Clean (renewable + nuclear)")
ax.plot(dates, ren, color=GREEN, lw=2.4, label="Renewable")
ax.set_title("US electricity generation mix, 2015–present", color=INK, fontsize=13, weight="bold", loc="left")
ax.set_ylabel("Share of generation (%)", color=INK)
ax.set_ylim(0, 75)
ax.xaxis.set_major_locator(YearLocator())
ax.xaxis.set_major_formatter(DateFormatter("%Y"))
ax.legend(frameon=False, loc="center left", fontsize=9)
ax.annotate(f"{ren[-1]:.0f}%", (dates[-1], ren[-1]), color=GREEN, fontsize=10, weight="bold",
            xytext=(6, -2), textcoords="offset points")
fig.tight_layout()
fig.savefig(os.path.join(ASSETS, "transition_trend.png"), bbox_inches="tight")
print("wrote assets/transition_trend.png")

# ---- 2. Top renewable states ----------------------------------------------
US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH",
    "NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT",
    "VT","VA","WA","WV","WI","WY",
}
rows = [r for r in json.load(open("/tmp/states.json")) if r[0] in US_STATES][:10]
rows.reverse()
labels = [r[0] for r in rows]
vals = [float(r[1]) for r in rows]

fig, ax = plt.subplots(figsize=(9, 4.2))
bars = ax.barh(labels, vals, color=GREEN, alpha=0.85)
ax.set_title("Top 10 states by renewable share of generation (2024)", color=INK, fontsize=13, weight="bold", loc="left")
ax.set_xlabel("Renewable share (%)", color=INK)
ax.set_xlim(0, 105)
for b, v in zip(bars, vals):
    ax.text(v + 1, b.get_y() + b.get_height() / 2, f"{v:.0f}%", va="center", fontsize=9, color=INK)
ax.grid(axis="y", visible=False)
fig.tight_layout()
fig.savefig(os.path.join(ASSETS, "top_states.png"), bbox_inches="tight")
print("wrote assets/top_states.png")

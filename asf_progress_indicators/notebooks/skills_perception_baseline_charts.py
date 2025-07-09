# %%
import matplotlib
import matplotlib.pyplot as pyplot
import pandas as pd

pyplot.rcParams["font.family"] = "averta"

# %% [markdown]
# ### Skills Indicator

# %%
year = range(2021, 2031)
counterfactual = [2_226, 2_502, 3_112, 4_761, 5_984, 7_804, 10_225, 13_397, 17_554, 23_003]
active_heat_pump_installers = [2_226, 2_502, 3_112, 4_761, 9_521, 19_043, 38_086, 66_650, 103_307, 129_134]

installers = pd.DataFrame({"year": year, "asf_target": active_heat_pump_installers, "counterfactual": counterfactual})

# %%
f, ax = pyplot.subplots(figsize=(6, 5), layout="constrained")

ax.bar(installers["year"][:4], installers["asf_target"][:4], width=0.95, color="#0000ff", label="Installers (estimate)")
ax.bar(
    installers["year"][4:] - 0.225,
    installers["counterfactual"][4:],
    width=0.48,
    color="#bdbdbd",
    alpha=0.85,
    label="Counterfactual",
)
ax.bar(
    installers["year"][4:] + 0.25, installers["asf_target"][4:], width=0.48, color="#74c8ba", alpha=0.85, label="Target"
)

ax.set_xticks(range(2021, 2031))
ax.ticklabel_format(useOffset=False, style="plain")
ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ",")))
ax.tick_params(axis="both", which="both", length=0)
# ax.set_ylabel("Annual Heat Pump Installations")
# ax.set_xlabel("Year")

ax.grid(axis="y")
ax.set_axisbelow(True)
ax.set_frame_on(False)

ax.legend(loc="upper center", frameon=False, ncol=3, bbox_to_anchor=(0.41, 1.02))

ax.set_title("Number of annual active heat pump installers", loc="left", y=1.02)

# create labels for bars
observed = [
    "2,200",
    "2,500",
    "3,100",
    "4,800",
]
for year, label in zip(range(2021, 2025), observed, strict=True):
    # get height of bar
    y = installers.loc[installers["year"] == year, "asf_target"]
    ax.text(x=year, y=y + 3000, s=label, ha="center", fontsize=9)

modelled = ["9,500", "19,000", "38,100", "66,700", "103,300", "129,100"]
for year, label in zip(range(2025, 2031), modelled, strict=True):
    # get height of bar
    y = installers.loc[installers["year"] == year, "asf_target"]
    ax.text(x=year + 0.1, y=y + 3500, s=label, ha="center", fontsize=9)

f.savefig("./Skills_Progress_indicator.png", dpi=300)

# %% [markdown]
# ### Perception Indicator

# %%
year = range(2021, 2031)
counterfactual = [18, 18, 21, 23, 25, 29, 33, 38, 43, 50]
perception = [18, 18, 21, 23, 33, 46, 66, 82, 90, 80]

perception = pd.DataFrame({"year": year, "asf_target": perception, "counterfactual": counterfactual})

# %%
f, ax = pyplot.subplots(figsize=(6, 5), layout="constrained")

ax.bar(perception["year"][:4], perception["asf_target"][:4], width=0.95, color="#0000ff", label="Surveyed")
ax.bar(
    perception["year"][4:] - 0.225,
    perception["counterfactual"][4:],
    width=0.48,
    color="#bdbdbd",
    alpha=0.85,
    label="Counterfactual",
)
ax.bar(
    perception["year"][4:] + 0.25, perception["asf_target"][4:], width=0.48, color="#74c8ba", alpha=0.85, label="Target"
)

ax.set_xticks(range(2021, 2031))
ax.ticklabel_format(useOffset=False, style="plain")
ax.set_yticks(range(0, 110, 10))
ax.tick_params(axis="both", which="both", length=0)
# ax.set_ylabel("Annual Heat Pump Installations")
# ax.set_xlabel("Year")

ax.grid(axis="y")
ax.set_axisbelow(True)
ax.set_frame_on(False)

ax.legend(loc="upper center", frameon=False, ncol=3, bbox_to_anchor=(0.33, 1.11))

ax.set_title(
    """Annual % of owner occupiers who state that they would install
a heat pump when they next need to change their heating system""",
    loc="left",
    y=1.12,
)

# create labels for bars
observed = [
    "18",
    "18",
    "21",
    "23",
]
for year, label in zip(range(2021, 2025), observed, strict=True):
    # get height of bar
    y = perception.loc[perception["year"] == year, "asf_target"]
    ax.text(x=year, y=y + 1, s=label, ha="center", fontsize=9)

modelled = ["33", "46", "66", "82", "90", "80"]
for year, label in zip(range(2025, 2031), modelled, strict=True):
    # get height of bar
    y = perception.loc[perception["year"] == year, "asf_target"]
    ax.text(x=year + 0.25, y=y + 1, s=label, ha="center", fontsize=9)

f.savefig("./Perception_Progress_indicator.png", dpi=300)

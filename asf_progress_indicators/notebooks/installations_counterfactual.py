# %%
import re

import matplotlib
import matplotlib.pyplot as pyplot
import pandas as pd
import statsmodels.api as sm

from asf_progress_indicators.getters import data_getters

pyplot.rcParams["font.family"] = "averta"

# %% [markdown]
# ### **Measuring the number of heat pump installations**
#
# Firstly, we'll construct the MCS heat pump data extract we use for the indicator.

# %%
# MCS installations with matching EPC records
mcs_x_epc = data_getters.get_mcs_epc_data()

# %%
mcs_x_epc["INSPECTION_DATE"] = pd.to_datetime(mcs_x_epc["INSPECTION_DATE"])

# %%
# Domestic installations only
domestic_installations = mcs_x_epc[mcs_x_epc["installation_type"] == "Domestic"]

# %%
# Retrofits only, exclude new builds


# Helper function to add label
def _installation_label_row(row: pd.Series) -> str:
    # Extract year and check for heat pump
    inspection_year = row["INSPECTION_DATE"].year if pd.notnull(row["INSPECTION_DATE"]) else None
    is_heat_pump = bool(re.search("heat pump", str(row["MAINHEAT_DESCRIPTION"]), flags=re.IGNORECASE))

    if (
        row["commission_year"] == inspection_year  # Installation year is the same as EPC inspection year
        and row["TRANSACTION_TYPE"] == "new dwelling"  # EPC transaction type
        and is_heat_pump  # EPC main heating system is heat pump
    ):
        return "New build"
    else:
        return "Retrofit"


# Add label to dataframe
retrofit_domestic_installations = domestic_installations.copy()
retrofit_domestic_installations["New build or retrofit"] = retrofit_domestic_installations.apply(
    _installation_label_row, axis=1
)

retrofit_domestic_installations = retrofit_domestic_installations[
    retrofit_domestic_installations["New build or retrofit"] == "Retrofit"
]

# %% [markdown]
# ### Binning data for forecasting
#
# To create a model of the historical data, we need to bin the data so that we get \
# counts of installations for some useful period of time. Because we have the exact \
# date of commissioning, I don't want to lose too much information by applying a very \
# coarse binning, I also want to be able to capture the data's sensitivity to seasons, \
# while avoiding a binning so fine it introduces zero counts.
#
# For the period post 2016, monthly binning looks like a reasonable choice, pre-2016 \
# data is quite sparse and a comparison based on the full time series versus the \
# post-2015 time series reveals little difference in the forecasts.
#
# ### Model Selection
#
# I've chosen an exponential smoothing model with a multiplicative trend to represent \
# non-linear growth in heat pump uptake and a seasonal component to represent the clear \
# seasonality in installations. Note that 'exponential' in the model name reflects the \
# weighting strategy for data points where the influence of older points gets exponentially \
# less, rather than an expectation for the kind of model produced. This is a simple model in \
# the context of time series forecasting, a more complex model like ARIMA could be used in \
# future, but you'd have to assess the stationarity of the time series.

# %%
# time ranges for binning installations
bins_dt = pd.date_range(start="2009-12-31", end="2025-04-01", freq="ME")

# %%
# Bin installs monthly by commission date
retrofit_domestic_installations["commission_month"] = pd.cut(
    retrofit_domestic_installations["commission_date"],
    bins=bins_dt,
)

# %%
# get monthly counts
monthly_retrofit_domestic_installations = (
    retrofit_domestic_installations["commission_month"].value_counts(sort=False).to_frame()
)

# %%
monthly_retrofit_domestic_installations["month_end"] = monthly_retrofit_domestic_installations.index.map(
    lambda x: x.right
)

# %%
# As data is very patchy pre 2016, let's fit a model that starts from then.
monthly_retrofit_domestic_installations_post_2015 = monthly_retrofit_domestic_installations[
    monthly_retrofit_domestic_installations["month_end"] > "2015-12-31"
]


# %%
# Perform exponential smoothing with a multiplicative trend and an additive seasonal adjustment
# There are 4 periods in a seasonal cycle, 2 periods is also plausible (e.g. heating and non-heating season).
model_post_2015 = sm.tsa.ExponentialSmoothing(
    monthly_retrofit_domestic_installations_post_2015["count"],
    trend="mul",
    seasonal="add",
    seasonal_periods=4,
    use_boxcox=False,
    initialization_method="estimated",
)
model_post_2015 = model_post_2015.fit()
monthly_retrofit_domestic_installations_post_2015["fitted_post_2015_ses"] = model_post_2015.fittedvalues

# %%
# Time bins for forecasted data
bins_dt_forecast = pd.date_range(start="2025-04-01", end="2030-12-31", freq="ME")

# %%
forecasts = pd.concat(
    [model_post_2015.forecast(69).reset_index(drop=True)],
    axis=1,
).rename(columns={0: "forecast_post_2015"})

forecasts.index = bins_dt_forecast

# %%
f, ax = pyplot.subplots(figsize=(10, 6))

ax.plot(monthly_retrofit_domestic_installations["month_end"], monthly_retrofit_domestic_installations["count"])
ax.plot(
    monthly_retrofit_domestic_installations_post_2015["month_end"],
    monthly_retrofit_domestic_installations_post_2015["fitted_post_2015_ses"],
)

ax.plot(forecasts.index, forecasts["forecast_post_2015"])

# %%
forecast_monthly = pd.concat([monthly_retrofit_domestic_installations_post_2015.set_index("month_end"), forecasts])

# %%
# Update forecast for first 3 months of 2025 with fitted estimates
forecast_monthly.loc[
    (forecast_monthly.index > "2025-01-01") & (forecast_monthly.index <= "2025-03-31"), "forecast_post_2015"
] = forecast_monthly.loc[
    (forecast_monthly.index > "2025-01-01") & (forecast_monthly.index <= "2025-03-31"), "fitted_post_2015_ses"
]

# %%
# Create year column
forecast_monthly["year"] = forecast_monthly.index.year

# %%
forecast_annual = forecast_monthly.groupby("year").agg(
    {"count": "sum", "fitted_post_2015_ses": "sum", "forecast_post_2015": "sum"}
)

# %%
asf_pathway = pd.Series(
    [111_466, 222_932, 423_571, 741_249, 1_148_936, 1_436_170],
    index=[2025, 2026, 2027, 2028, 2029, 2030],
    name="asf_pathway",
)

# %%
forecast_annual = forecast_annual.merge(asf_pathway, how="left", left_index=True, right_index=True)

# %%
# remove first quarter results for count and fitted
forecast_annual.loc[2025, "count"] = None
forecast_annual.loc[2025, "fitted_post_2015_ses"] = None

# %%
f, ax = pyplot.subplots(figsize=(9, 5), layout="constrained")

ax.bar(
    forecast_annual.index,
    forecast_annual["count"],
    width=0.95,
    color="#0000ff",
    label="MCS-certified installations in the UK",
)
ax.bar(
    forecast_annual.index[-6:] - 0.225,
    forecast_annual["forecast_post_2015"][-6:],
    width=0.48,
    color="#bdbdbd",
    alpha=0.85,
    label="Counterfactual",
)
ax.bar(
    forecast_annual.index[-6:] + 0.25,
    forecast_annual["asf_pathway"][-6:],
    width=0.48,
    color="#74c8ba",
    alpha=0.85,
    label="Target",
)

ax.set_xticks(range(2016, 2031))
ax.ticklabel_format(useOffset=False, style="plain")
ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ",")))
ax.tick_params(axis="both", which="both", length=0)
# ax.set_ylabel("Annual Heat Pump Installations")
# ax.set_xlabel("Year")

ax.grid(axis="y")
ax.set_axisbelow(True)
ax.set_frame_on(False)

ax.legend(loc="upper center", frameon=False, ncol=3, bbox_to_anchor=(0.331, 1.05))

ax.set_title("Number of annual retrofit heat pump installations", loc="left", y=1.05)

# create labels for bars
observed = ["6,500", "7,300", "8,000", "11,000", "12,200", "24,900", "28,000", "34,800", "53,200"]
for year, label in zip(range(start=2016, stop=2025), observed, strict=True):
    # get height of bar
    y = forecast_annual.loc[year, "count"]
    ax.text(x=year, y=y + 15000, s=label, ha="center", fontsize=7)

modelled = ["111,500", "222,900", "423,600", "741,200", "1,148,900", "1,436,200"]
for year, label in zip(range(start=2025, stop=2031), modelled, strict=True):
    # get height of bar
    y = forecast_annual.loc[year, "asf_pathway"]
    ax.text(x=year + 0.2, y=y + 17500, s=label, ha="center", fontsize=7)

# f.savefig("./Headline_Progress_indicator.png", dpi=300)

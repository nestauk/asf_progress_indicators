# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: asf-progress-indicators (3.13.2)
#     language: python
#     name: python3
# ---

# %%
from datetime import datetime

import pandas as pd

from asf_progress_indicators import PROJECT_DIR
from asf_progress_indicators.getters import data_getters

# %% [markdown]
# ### **Measuring the number of heat pump installations**

# %% [markdown]
# ### MCS Installations Database

# %% [markdown]
# **MCS EPC dataset - last update: 2025 Q1**

# %%
# MCS installations with matching EPC records
mcs_x_epc = data_getters.get_mcs_epc_data()

# %%
# Check temporal coverage of datasets
print(mcs_x_epc["commission_date"].min(), mcs_x_epc["commission_date"].max())
mcs_x_epc["INSPECTION_DATE"] = pd.to_datetime(mcs_x_epc["INSPECTION_DATE"])
print(mcs_x_epc["INSPECTION_DATE"].min(), mcs_x_epc["INSPECTION_DATE"].max())

# %%
# Domestic installations only
mcs_epc_domestic_installations = mcs_x_epc[mcs_x_epc["installation_type"] == "Domestic"]

# %%
# Technology type breakdown
mcs_epc_domestic_installations_by_technology = (
    mcs_epc_domestic_installations.groupby(["commission_year", "tech_type"]).size().unstack(fill_value=0)
)
mcs_epc_domestic_installations_by_technology["Dataset"] = "MCS Installations (domestic only)"

# Only include years of interest
current_year = datetime.now().year
years = list(range(2018, current_year + 1))

mcs_epc_domestic_installations_by_technology = mcs_epc_domestic_installations_by_technology[
    mcs_epc_domestic_installations_by_technology.index.isin(years)
].reset_index()

# Re-order columns
mcs_epc_domestic_installations_by_technology = mcs_epc_domestic_installations_by_technology[
    [
        "Dataset",
        "commission_year",
        "Air Source Heat Pump",
        "Ground/Water Source Heat Pump",
        "Exhaust Air Heat Pump",
    ]
]

# Rename columns
mcs_epc_domestic_installations_by_technology = mcs_epc_domestic_installations_by_technology.rename(
    columns={
        "commission_year": "Year",
        "Air Source Heat Pump": "Air source heat pumps",
        "Ground/Water Source Heat Pump": "Ground/Water source heat pumps",
        "Exhaust Air Heat Pump": "Exhaust air heat pumps",
    }
)

# %%
mcs_epc_domestic_installations_by_technology

# %%
# Retrofits only, exclude new builds (heat pumps being installed when built)


# Helper function to add label
def _installation_label_row(row: pd.Series, threshold_int: int) -> str:
    commission_date = pd.to_datetime(row["commission_date"], errors="raise")
    inspection_date = pd.to_datetime(row["INSPECTION_DATE"], errors="raise")

    days_diff_below_threshold = (
        pd.notnull(commission_date)
        and pd.notnull(inspection_date)
        and abs((commission_date - inspection_date).days) < threshold_int
    )

    if days_diff_below_threshold and row["TRANSACTION_TYPE"] == "new dwelling":
        return "New build"
    else:
        return "Retrofit"


# Add retrofit label to dataframe
mcs_epc_retrofit_domestic_installations = mcs_epc_domestic_installations.copy()
mcs_epc_retrofit_domestic_installations["New build or retrofit"] = mcs_epc_retrofit_domestic_installations.apply(
    _installation_label_row, threshold_int=365, axis=1
)

mcs_epc_retrofit_domestic_installations = mcs_epc_retrofit_domestic_installations[
    mcs_epc_retrofit_domestic_installations["New build or retrofit"] == "Retrofit"
]

# %%
# Technology type breakdown
mcs_epc_retrofit_domestic_installations = (
    mcs_epc_retrofit_domestic_installations.groupby(["commission_year", "tech_type"]).size().unstack(fill_value=0)
)
mcs_epc_retrofit_domestic_installations["Dataset"] = "MCS Installations (retrofits only)"

# %%
# Only include years of interest
current_year = datetime.now().year
years = list(range(2018, current_year + 1))

mcs_epc_retrofit_domestic_installations = mcs_epc_retrofit_domestic_installations[
    mcs_epc_retrofit_domestic_installations.index.isin(years)
].reset_index()

# Re-order columns
mcs_epc_retrofit_domestic_installations = mcs_epc_retrofit_domestic_installations[
    [
        "Dataset",
        "commission_year",
        "Air Source Heat Pump",
        "Ground/Water Source Heat Pump",
        "Exhaust Air Heat Pump",
    ]
]

# Rename columns
mcs_epc_retrofit_domestic_installations = mcs_epc_retrofit_domestic_installations.rename(
    columns={
        "commission_year": "Year",
        "Air Source Heat Pump": "Air source heat pumps",
        "Ground/Water Source Heat Pump": "Ground/Water source heat pumps",
        "Exhaust Air Heat Pump": "Exhaust air heat pumps",
    }
)

# %%
mcs_epc_retrofit_domestic_installations

# %%
# Percentage of domestic installs that are retrofits

retrofit_domestic_pct_ashp = list(
    mcs_epc_retrofit_domestic_installations["Air source heat pumps"]
    / mcs_epc_domestic_installations_by_technology["Air source heat pumps"]
)


retrofit_domestic_pct_gshp = list(
    mcs_epc_retrofit_domestic_installations["Ground/Water source heat pumps"]
    / mcs_epc_domestic_installations_by_technology["Ground/Water source heat pumps"]
)


retrofit_domestic_pct_exhaust = list(
    mcs_epc_retrofit_domestic_installations["Exhaust air heat pumps"]
    / mcs_epc_domestic_installations_by_technology["Exhaust air heat pumps"]
)

# %% [markdown]
# **MCS dataset - last update: 2025 Q3**

# %%
# MCS installations
mcs = data_getters.get_mcs_data()

# %%
# Check temporal coverage of datasets
print(mcs["commission_date"].min(), mcs["commission_date"].max())

# %%
# Domestic installations only
mcs_domestic_installations = mcs[mcs["installation_type"] == "Domestic"]

# %%
# Technology type breakdown
mcs_domestic_installations_by_technology = (
    mcs_domestic_installations.groupby(["commission_year", "tech_type"]).size().unstack(fill_value=0)
)
mcs_domestic_installations_by_technology["Dataset"] = "MCS Installations (domestic)"

# %%
# Only include years of interest
current_year = datetime.now().year
years = list(range(2018, current_year + 1))

mcs_domestic_installations_by_technology = mcs_domestic_installations_by_technology[
    mcs_domestic_installations_by_technology.index.isin(years)
].reset_index()

# Re-order columns
mcs_domestic_installations_by_technology = mcs_domestic_installations_by_technology[
    [
        "Dataset",
        "commission_year",
        "Air Source Heat Pump",
        "Ground/Water Source Heat Pump",
        "Exhaust Air Heat Pump",
    ]
]

# Rename columns
mcs_domestic_installations_by_technology = mcs_domestic_installations_by_technology.rename(
    columns={
        "commission_year": "Year",
        "Air Source Heat Pump": "Air source heat pumps",
        "Ground/Water Source Heat Pump": "Ground/Water source heat pumps",
        "Exhaust Air Heat Pump": "Exhaust air heat pumps",
    }
)

# %%
mcs_domestic_installations_by_technology

# %% [markdown]
# In the absence of MCS-EPC combined data for 2025 Q3 (EPC data field is needed to label retrofit/new-build), use historical % of domestic installs that are retrofits to estimate retrofit numbers

# %%
mcs_domestic_installations_by_technology["Air source heat pumps"] * retrofit_domestic_pct_ashp

# %%
mcs_domestic_installations_by_technology["Ground/Water source heat pumps"] * retrofit_domestic_pct_gshp

# %%
mcs_domestic_installations_by_technology["Exhaust air heat pumps"] * retrofit_domestic_pct_exhaust

# %% [markdown]
# ### Heat Pump Association factory gate sales

# %%
# Read Heat Pump Association factory gate sales
# https://www.heatpumps.org.uk/resources/statistics/

# To be manually updated when new data is released
years = list(range(2019, 2025))
hpa_sales_data = {
    "Year": years,
    "Other heat pumps": [1_242, 1_004, 2_315, 4_177, 6_945, 1_673],
    "Domestic hot water heat pumps": [0, 0, 0, 0, 0, 12_265],
    "Ground/Water source heat pumps": [2_020, 3_197, 4_207, 4_664, 5_91, 3_087],
    "Air-to-water (monobloc units) heat pumps": [
        19_606,
        22_310,
        37_362,
        47_489,
        47_399,
        78_060,
    ],
    "Air-to-water (split units) heat pumps": [2_859, 2_715, 3_815, 4_731, 3_471, 3_260],
}

# Create dataframe
hpa_sales = pd.DataFrame(hpa_sales_data)
hpa_sales.name = "Year"
hpa_sales["Dataset"] = "Factory gate sales (Heat Pump Association)"

# %% [markdown]
# ### DESNZ Heat Pump Deployment Statistics

# %%
# Update file URL in config when new release is published
# Read Excel sheet
heat_pump_deployment_statistics = data_getters.get_heat_pump_deployment_statistics()

# Select table of interest
deployment_df = heat_pump_deployment_statistics["Table 1.2"]

# %%
# Set correct row as header
new_header = deployment_df.iloc[4].values
deployment_df = deployment_df.iloc[5:].copy()
deployment_df.columns = new_header
deployment_df.reset_index(drop=True, inplace=True)

# Add year column
deployment_df["Year"] = deployment_df["Installation quarter [note 4]"].str.extract(r"^(\d{4})").astype(int)

# %%
# Specify columns of interest
columns = [
    "Year",
    "Government-supported heat pump installations:\nair source heat pumps \n[note 13]",
    "Government-supported heat pump installations:\nground/water source heat pumps \n[note 13]",
    "Government-supported heat pump installations:\nUnknown technology [note 14]",
]

# Aggregate by year
deployment_yearly_df = deployment_df[columns].groupby("Year").sum()

# Rename columns
deployment_yearly_df = deployment_yearly_df.rename(
    columns={
        "Government-supported heat pump installations:\nair source heat pumps \n[note 13]": ("Air source heat pumps"),
        "Government-supported heat pump installations:\nground/water source heat pumps \n[note 13]": (
            "Ground/Water source heat pumps"
        ),
        "Government-supported heat pump installations:\nUnknown technology [note 14]": ("Unknown technology"),
    }
)

# Transform to be compatible with other dataframes
deployment_yearly_df["Dataset"] = "UK Government Supported Installations (DESNZ)"
deployment_yearly_df = deployment_yearly_df.reset_index()

# %% [markdown]
# ### Combining all datasets

# %%
# Combine into a Flourish-compatible table
flourish_table = pd.concat([mcs_installations_by_technology, hpa_sales, deployment_yearly_df]).fillna(value=0)

# Create total column
columns_to_sum = [col for col in flourish_table.columns.to_list() if col not in ["Dataset", "Year"]]
flourish_table["Total"] = flourish_table[columns_to_sum].sum(axis=1)

# %%
# Export to .csv for importing into Flourish
flourish_table.to_csv(
    f"{PROJECT_DIR}/outputs/data/{datetime.now().strftime('%Y%m%d')}_installations_for_flourish.csv",
    index=False,
)

# %%
# Pickle dataframe
flourish_table.to_pickle(
    f"{PROJECT_DIR}/outputs/data/{datetime.now().strftime('%Y%m%d')}_historical_installations.pkl",
)

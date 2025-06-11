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
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %%
import re

import pandas as pd

from asf_progress_indicators import PROJECT_DIR
from asf_progress_indicators.getters import data_getters

# %% [markdown]
# ### **Measuring the number of heat pump installations**

# %% [markdown]
# ### MCS Installations Database

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
domestic_installations = mcs_x_epc[mcs_x_epc["installation_type"] == "Domestic"]

# %%
# Technology type breakdown
mcs_installations_by_technology = (
    domestic_installations.groupby(["commission_year", "tech_type"]).size().unstack(fill_value=0)
)
mcs_installations_by_technology["Dataset"] = "MCS Installations (by technology)"

# %%
# New build or retrofit breakdown


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
domestic_installations = domestic_installations.copy()
domestic_installations["New build or retrofit"] = domestic_installations.apply(_installation_label_row, axis=1)

# %%
# New build or retrofit breakdown table
mcs_installations_by_new_build = (
    domestic_installations.groupby(["commission_year", "New build or retrofit"]).size().unstack(fill_value=0)
)
mcs_installations_by_new_build["Dataset"] = "MCS Installations (by new build or retrofit)"

# %%
# Combine MCS installations tables
mcs_installations = pd.concat([mcs_installations_by_technology, mcs_installations_by_new_build]).fillna(value=0)
mcs_installations = mcs_installations[
    mcs_installations.index.isin([2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025])
].reset_index()

# Re-order columns
mcs_installations = mcs_installations[
    [
        "Dataset",
        "commission_year",
        "Air Source Heat Pump",
        "Ground/Water Source Heat Pump",
        "Exhaust Air Heat Pump",
        "New build",
        "Retrofit",
    ]
]

# Rename columns
mcs_installations = mcs_installations.rename(
    columns={
        "commission_year": "Year",
        "Air Source Heat Pump": "Air source heat pumps",
        "Ground/Water Source Heat Pump": "Ground/Water source heat pumps",
        "Exhaust Air Heat Pump": "Exhaust air heat pumps",
    }
)

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
flourish_table = pd.concat([mcs_installations, hpa_sales, deployment_yearly_df]).fillna(value=0)

# %%
# Export to .csv for importing into Flourish
flourish_table.to_csv(f"{PROJECT_DIR}/outputs/data/installations_for_flourish.csv", index=False)

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
import pandas as pd

from asf_progress_indicators import PROJECT_DIR
from asf_progress_indicators.getters import data_getters

# %% [markdown]
# ### **Measuring the number of active heat pump installers**

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

# %% [markdown]
# ### Contractors that installed at least one heat pump in each year

# %%
# Assumption https://mcscertified.com/research-highlights-heat-pump-business-size/
installers_per_contractor = 4.8

# %%
# Count number of unique installation companies that installed at least one heat pump in each year
years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

active_installers_time_series = []
active_companies_time_series = []

for year in years:
    mcs_annual = mcs_x_epc[mcs_x_epc["commission_year"] == year]
    active_installers_time_series.append(
        round(
            len(mcs_annual["installation_company_mcs_number"].value_counts()) * installers_per_contractor,
            0,
        )
    )
    active_companies_time_series.append(len(mcs_annual["installation_company_mcs_number"].value_counts()))

# %%
# Create dataframe
active_mcs_installers = {
    "Year": years,
    "Active MCS-certified firms": active_companies_time_series,
    "Installers working for active MCS-certified firms": active_installers_time_series,
}

active_mcs_installers_df = pd.DataFrame(active_mcs_installers)
active_mcs_installers_df["Installers working for active MCS-certified firms"] = pd.to_numeric(
    active_mcs_installers_df["Installers working for active MCS-certified firms"],
    downcast="integer",
)

# %%
# Export to .csv for importing into Flourish
active_mcs_installers_df.to_csv(f"{PROJECT_DIR}/outputs/data/installers_for_flourish.csv", index=False)

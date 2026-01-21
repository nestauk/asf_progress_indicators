# -*- coding: utf-8 -*-
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
from asf_progress_indicators.utils import utils

# %% [markdown]
# ### **Modelling the lifetime costs of a heat pump and gas boiler**

# %% [markdown]
# ### General assumptions

# %%
# Lifetime duration
boiler_lifetime = 15  # years
heat_pump_lifetime = 15  # years

## Not using this as we want to show nominal out-of-pocket spend for consumer
# # Future discounting assumptions (£1 today is worth more to society than a £1 in the future)
# discount_rate = (
#     3.5 / 100
# )  # %; social time preference rate, as provided by HMT Green Book guidance


# Energy consumption - Medium TDCV
gas_tdcv = 11.5  # MWh
electricity_tdcv = 2.7  # MWh

# %% [markdown]
# ### Installation costs

# %%
# Average cost of boiler install
boiler_install_cost = 3_000

# %%
# Average cost of heat pump install
# Median cost of BUS ASHP installs 2025 Q3
heat_pump_install_cost = 13_000

# %% [markdown]
# Government subsidies and loans

# %%
## Government support

# England and Wales
bus_subsidy = 7_500

# Scotland
scotland_grant = 7_500

# %% [markdown]
# Financing

# %%
# Home Energy Scotland (interest-free)
scotland_interest_free_loan = min(heat_pump_install_cost - scotland_grant, 7_500)
scotland_loan_term = 5  # years

# Standard loan England and Wales
loan_apr_options = {"low": 3 / 100, "medium": 5 / 100, "high": 10 / 100}
loan_term = 15  # years
loan_amount = heat_pump_install_cost - bus_subsidy

annual_loan_payment = {}
for key, rate in loan_apr_options.items():
    annual_loan_payment[key] = (loan_amount * rate) / (1 - ((1 + rate) ** -loan_term))

# %% [markdown]
# ### Operation

# %% [markdown]
# Energy price cap

# %%
# Load historical price cap values for "Other Payment Method"
price_cap_periods = [
    "2023-01-01",
    "2023-04-01",
    "2023-07-01",
    "2023-10-01",
    "2024-01-01",
    "2024-04-01",
    "2024-07-01",
    "2024-10-01",
    "2025-01-01",
    "2025-04-01",
    "2025-07-01",
    "2025-10-01",
    "2026-01-01",
    "2026-04-01",
]

gas_tariffs = {}
gas_standing_charges = {}
gas_unit_costs = {}
electricity_tariffs = {}
electricity_standing_charges = {}
electricity_unit_costs = {}
for period in price_cap_periods:

    if period == "2026-04-01":
        continue  # skip this period

    # Instantiate tariff
    gas_tariff, electricity_tariff = data_getters.instantiate_tariffs(
        payment_method="Other Payment Method", price_cap=period
    )
    gas_tariffs[period] = gas_tariff
    electricity_tariffs[period] = electricity_tariff

    # Extract gas costs
    gas_standing_charges[period] = (
        gas_tariff.calculate_nil_consumption()
    )  # £ per customer per year
    gas_unit_costs[period] = gas_tariff.calculate_variable_consumption(1)  # £ per MWh

    # Extract electricity costs
    electricity_standing_charges[period] = (
        electricity_tariff.calculate_nil_consumption()
    )  # £ per customer per year
    electricity_unit_costs[period] = electricity_tariff.calculate_variable_consumption(
        1
    )  # £ per MWh

# %%
# For Warm Homes Plan analysis ONLY

# April 2026 price cap estimate with budget changes including VAT
electricity_unit_cost_apr_26 = 23.46 / 100 * 1000  # p/kWh conversion to £/MWh
electricity_standing_charge_apr_26 = 66.68 / 100 * 365  # p/meter/day to £/meter/year
gas_unit_cost_apr_26 = 5.74 / 100 * 1000  # p/kWh conversion to £/MWh
gas_standing_charge_apr_26 = 35.89 / 100 * 365  # p/meter/day to £/meter/year

# Add these to dictionaries
gas_standing_charges["2026-04-01"] = gas_standing_charge_apr_26 / 1.05  # exclude VAT
gas_unit_costs["2026-04-01"] = gas_unit_cost_apr_26 / 1.05
electricity_standing_charges["2026-04-01"] = electricity_standing_charge_apr_26 / 1.05
electricity_unit_costs["2026-04-01"] = electricity_unit_cost_apr_26 / 1.05

# %%
# Calculating year averages

# electricity unit cost
electricity_unit_cost_2023_average = (
    electricity_unit_costs["2023-10-01"]
    + electricity_unit_costs["2023-07-01"]
    + electricity_unit_costs["2023-04-01"]
    + electricity_unit_costs["2023-01-01"]
) / 4
electricity_unit_cost_2024_average = (
    electricity_unit_costs["2024-10-01"]
    + electricity_unit_costs["2024-07-01"]
    + electricity_unit_costs["2024-04-01"]
    + electricity_unit_costs["2024-01-01"]
) / 4
electricity_unit_cost_2025_average = (
    electricity_unit_costs["2025-10-01"]
    + electricity_unit_costs["2025-07-01"]
    + electricity_unit_costs["2025-04-01"]
    + electricity_unit_costs["2025-01-01"]
) / 4
electricity_unit_cost_2026_average = (
    electricity_unit_costs["2026-04-01"]  # estimated from budget changes
    + electricity_unit_costs["2026-01-01"]
) / 2

# gas unit cost
gas_unit_cost_2023_average = (
    gas_unit_costs["2023-10-01"]
    + gas_unit_costs["2023-07-01"]
    + gas_unit_costs["2023-04-01"]
    + gas_unit_costs["2023-01-01"]
) / 4
gas_unit_cost_2024_average = (
    gas_unit_costs["2024-10-01"]
    + gas_unit_costs["2024-07-01"]
    + gas_unit_costs["2024-04-01"]
    + gas_unit_costs["2024-01-01"]
) / 4
gas_unit_cost_2025_average = (
    gas_unit_costs["2025-10-01"]
    + gas_unit_costs["2025-07-01"]
    + gas_unit_costs["2025-04-01"]
    + gas_unit_costs["2025-01-01"]
) / 4
gas_unit_cost_2026_average = (
    gas_unit_costs["2026-01-01"]
    + gas_unit_costs["2026-04-01"]  # estimated from budget changes
) / 2

# gas standing charge
gas_standing_charge_2023_average = (
    gas_standing_charges["2023-10-01"]
    + gas_standing_charges["2023-07-01"]
    + gas_standing_charges["2023-04-01"]
    + gas_standing_charges["2023-01-01"]
) / 4
gas_standing_charge_2024_average = (
    gas_standing_charges["2024-10-01"]
    + gas_standing_charges["2024-07-01"]
    + gas_standing_charges["2024-04-01"]
    + gas_standing_charges["2024-01-01"]
) / 4
gas_standing_charge_2025_average = (
    gas_standing_charges["2025-10-01"]
    + gas_standing_charges["2025-07-01"]
    + gas_standing_charges["2025-04-01"]
    + gas_standing_charges["2025-01-01"]
) / 4
gas_standing_charge_2026_average = (
    gas_standing_charges["2026-01-01"]
    + gas_standing_charges["2026-04-01"]  # estimated from budget changes
) / 2

# %%
## Electricity and gas price projections
# Seventh Carbon Budget baseline scenario
# https://www.theccc.org.uk/publication/methodology-report-uk-northern-ireland-wales-and-scotland-carbon-budget-advice/
# Accompanying data file, M9 tab, Energy retail prices in the baseline scenario (includes VAT)

# £/MWh
electricity_unit_cost_time_series = {
    2023: electricity_unit_cost_2023_average * 1.05,
    2024: electricity_unit_cost_2024_average * 1.05,
    2025: electricity_unit_cost_2025_average * 1.05,
    2026: electricity_unit_cost_2026_average * 1.05,
    # 2026: 233,
    2027: 214,
    2028: 203,
    2029: 193,
    2030: 182,
    2031: 179,
    2032: 174,
    2033: 169,
    2034: 164,
    2035: 161,
    2036: 160,
    2037: 158,
    2038: 156,
    2039: 156,
    2040: 155,
    2041: 155,
    2042: 154,
    2043: 154,
    2044: 153,
    2045: 153,
    2046: 153,
    2047: 153,
    2048: 153,
    2049: 153,
    2050: 153,
}

# £/household/year
gas_standing_charge_time_series = {
    2023: gas_standing_charge_2023_average * 1.05,
    2024: gas_standing_charge_2024_average * 1.05,
    2025: gas_standing_charge_2025_average * 1.05,
    2026: gas_standing_charge_2026_average * 1.05,
    # 2026: 110,
    2027: 110,
    2028: 108,
    2029: 108,
    2030: 108,
    2031: 108,
    2032: 108,
    2033: 107,
    2034: 107,
    2035: 102,
    2036: 103,
    2037: 103,
    2038: 103,
    2039: 104,
    2040: 104,
    2041: 104,
    2042: 105,
    2043: 105,
    2044: 106,
    2045: 106,
    2046: 106,
    2047: 107,
    2048: 107,
    2049: 107,
    2050: 107,
}

# £/MWh
gas_unit_cost_time_series = {
    2023: gas_unit_cost_2023_average * 1.05,
    2024: gas_unit_cost_2024_average * 1.05,
    2025: gas_unit_cost_2025_average * 1.05,
    2026: gas_unit_cost_2026_average * 1.05,
    # 2026: 63,
    2027: 59,
    2028: 56,
    2029: 54,
    2030: 50,
    2031: 50,
    2032: 50,
    2033: 50,
    2034: 50,
    2035: 50,
    2036: 50,
    2037: 50,
    2038: 50,
    2039: 50,
    2040: 50,
    2041: 50,
    2042: 50,
    2043: 50,
    2044: 50,
    2045: 50,
    2046: 50,
    2047: 50,
    2048: 50,
    2049: 50,
    2050: 50,
}

# %%
# Lifetime running cost of a gas boiler purchased in each price cap period

heating_gas_share = 0.97
annual_boiler_gas_consumption = gas_tdcv * heating_gas_share  # MWh per year

annual_boiler_running_costs_dict = {}
lifetime_boiler_running_costs = {}

# for a boiler purchased in each price cap period
for period in price_cap_periods:
    start_year = int(period.split("-")[0])

    # years it is operational
    lifetime_years = [start_year + i for i in range(boiler_lifetime)]

    annual_boiler_running_costs = {}
    for year in lifetime_years:
        if year == start_year:  # in start year, use actual price cap period prices
            annual_boiler_running_costs[year] = float(
                gas_unit_costs[period] * annual_boiler_gas_consumption * 1.05
            ) + float(
                gas_standing_charges[period] * 1.05
            )  # £ per year, including VAT
        else:  # in all other years, use annual average prices (average of price caps in each year)
            annual_boiler_running_costs[year] = float(
                gas_unit_cost_time_series[year] * annual_boiler_gas_consumption
            ) + float(
                gas_standing_charge_time_series[year]
            )  # £ per year, including VAT

    annual_boiler_running_costs_dict[period] = annual_boiler_running_costs
    lifetime_boiler_running_costs[period] = sum(annual_boiler_running_costs.values())

# %%
# Lifetime running cost of a heat pump purchased in each price cap period

boiler_efficiency = 0.85
annual_heat_demand = annual_boiler_gas_consumption * boiler_efficiency  # MWh per year

heat_pump_efficiency = 3.0
annual_heat_pump_electricity_consumption = (
    annual_heat_demand / heat_pump_efficiency
)  # MWh per year

annual_heat_pump_running_costs_dict = {}
lifetime_heat_pump_running_costs = {}

# for a heat pump purchased in each price cap period
for period in price_cap_periods:
    start_year = int(period.split("-")[0])

    # years it is operational
    lifetime_years = [start_year + i for i in range(heat_pump_lifetime)]

    annual_heat_pump_running_costs = {}
    for year in lifetime_years:
        if year == start_year:  # in start year, use actual price cap period prices
            annual_heat_pump_running_costs[year] = float(
                electricity_unit_costs[period]
                * annual_heat_pump_electricity_consumption
                * 1.05
            )  # £ per year, including VAT
        else:  # in all other years, use annual average prices (average of price caps in each year)
            annual_heat_pump_running_costs[year] = float(
                electricity_unit_cost_time_series[year]
                * annual_heat_pump_electricity_consumption
            )  # £ per year, including VAT

    annual_heat_pump_running_costs_dict[period] = annual_heat_pump_running_costs
    lifetime_heat_pump_running_costs[period] = sum(
        annual_heat_pump_running_costs.values()
    )

# %%
annual_heat_pump_running_costs_dict["2026-04-01"]

# %% [markdown]
# ### Maintenance

# %%
# Cost of boiler maintenance
boiler_maintenance_frequency = 1  # times per year
boiler_maintenance_cost = 80  # £ per maintenenance session

# %%
# Cost of heat pump maintenance
heat_pump_maintenance_frequency = 1  # times per year
heat_pump_maintenance_cost = 80  # £ per maintenenance session

# %% [markdown]
# ### **Comparing total lifetime costs**

# %% [markdown]
# Boiler
#
# - Assume no financing for upfront cost

# %%
boiler_lifetime_costs = {}
for period in price_cap_periods:
    boiler_lifetime_costs[period] = (
        boiler_install_cost
        + lifetime_boiler_running_costs[period]
        + (boiler_maintenance_cost * boiler_maintenance_frequency * boiler_lifetime)
    )

# %% [markdown]
# Heat pump
#
# - Assume no financing for upfront cost

# %%
heat_pump_lifetime_costs = {}
for period in price_cap_periods:
    heat_pump_lifetime_costs[period] = (
        (heat_pump_install_cost - bus_subsidy)
        + lifetime_heat_pump_running_costs[period]
        + (
            heat_pump_maintenance_cost
            * heat_pump_maintenance_frequency
            * heat_pump_lifetime
        )
    )

# %% [markdown]
# Heat pump
#
# - Assume 3% interest rate loan over 15 years

# %%
heat_pump_3pct_financed_lifetime_costs = {}
for period in price_cap_periods:
    heat_pump_3pct_financed_lifetime_costs[period] = (
        (heat_pump_install_cost - bus_subsidy)
        + lifetime_heat_pump_running_costs[period]
        + (
            heat_pump_maintenance_cost
            * heat_pump_maintenance_frequency
            * heat_pump_lifetime
        )
        + (
            (annual_loan_payment["low"] * loan_term)
            - (heat_pump_install_cost - bus_subsidy)
        )
    )

# %% [markdown]
# Heat pump
#
# - Assume 5% interest rate loan over 15 years

# %%
heat_pump_5pct_financed_lifetime_costs = {}
for period in price_cap_periods:
    heat_pump_5pct_financed_lifetime_costs[period] = (
        (heat_pump_install_cost - bus_subsidy)
        + lifetime_heat_pump_running_costs[period]
        + (
            heat_pump_maintenance_cost
            * heat_pump_maintenance_frequency
            * heat_pump_lifetime
        )
        + (
            (annual_loan_payment["medium"] * loan_term)
            - (heat_pump_install_cost - bus_subsidy)
        )
    )

# %% [markdown]
# Heat pump
#
# - Assume 10% interest rate loan over 15 years

# %%
heat_pump_10pct_financed_lifetime_costs = {}
for period in price_cap_periods:
    heat_pump_10pct_financed_lifetime_costs[period] = (
        (heat_pump_install_cost - bus_subsidy)
        + lifetime_heat_pump_running_costs[period]
        + (
            heat_pump_maintenance_cost
            * heat_pump_maintenance_frequency
            * heat_pump_lifetime
        )
        + (
            (annual_loan_payment["high"] * loan_term)
            - (heat_pump_install_cost - bus_subsidy)
        )
    )

# %% [markdown]
# All heating systems

# %%
# Annualised lifetime cost breakdown table
rows = []

for period in price_cap_periods:
    rows.append(
        {
            "Heating system": "Gas boiler",
            "Price cap period": period,
            "Upfront costs": boiler_install_cost / boiler_lifetime,
            "Loan interest": 0,
            "Running costs": lifetime_boiler_running_costs[period] / boiler_lifetime,
            "Maintenance costs": (
                boiler_maintenance_cost * boiler_maintenance_frequency * boiler_lifetime
            )
            / boiler_lifetime,
            "Subsidy": 0,
            "Total": boiler_lifetime_costs[period] / boiler_lifetime,
        }
    )

    rows.append(
        {
            "Heating system": "Heat pump (no financing)",
            "Price cap period": period,
            "Upfront costs": (heat_pump_install_cost - bus_subsidy)
            / heat_pump_lifetime,
            "Loan interest": 0,
            "Running costs": lifetime_heat_pump_running_costs[period]
            / heat_pump_lifetime,
            "Maintenance costs": (
                heat_pump_maintenance_cost
                * heat_pump_maintenance_frequency
                * heat_pump_lifetime
            )
            / heat_pump_lifetime,
            "Subsidy": bus_subsidy / heat_pump_lifetime,
            "Total": heat_pump_lifetime_costs[period] / heat_pump_lifetime,
        }
    )

    rows.append(
        {
            "Heating system": "Heat pump (3% loan)",
            "Price cap period": period,
            "Upfront costs": (heat_pump_install_cost - bus_subsidy)
            / heat_pump_lifetime,
            "Loan interest": (
                (annual_loan_payment["low"] * loan_term)
                - (heat_pump_install_cost - bus_subsidy)
            )
            / heat_pump_lifetime,
            "Running costs": lifetime_heat_pump_running_costs[period]
            / heat_pump_lifetime,
            "Maintenance costs": (
                heat_pump_maintenance_cost
                * heat_pump_maintenance_frequency
                * heat_pump_lifetime
            )
            / heat_pump_lifetime,
            "Subsidy": bus_subsidy / heat_pump_lifetime,
            "Total": heat_pump_3pct_financed_lifetime_costs[period]
            / heat_pump_lifetime,
        }
    )

    rows.append(
        {
            "Heating system": "Heat pump (5% loan)",
            "Price cap period": period,
            "Upfront costs": (heat_pump_install_cost - bus_subsidy)
            / heat_pump_lifetime,
            "Loan interest": (
                (annual_loan_payment["medium"] * loan_term)
                - (heat_pump_install_cost - bus_subsidy)
            )
            / heat_pump_lifetime,
            "Running costs": lifetime_heat_pump_running_costs[period]
            / heat_pump_lifetime,
            "Maintenance costs": (
                heat_pump_maintenance_cost
                * heat_pump_maintenance_frequency
                * heat_pump_lifetime
            )
            / heat_pump_lifetime,
            "Subsidy": bus_subsidy / heat_pump_lifetime,
            "Total": heat_pump_5pct_financed_lifetime_costs[period]
            / heat_pump_lifetime,
        }
    )

    rows.append(
        {
            "Heating system": "Heat pump (10% loan)",
            "Price cap period": period,
            "Upfront costs": (heat_pump_install_cost - bus_subsidy)
            / heat_pump_lifetime,
            "Loan interest": (
                (annual_loan_payment["high"] * loan_term)
                - (heat_pump_install_cost - bus_subsidy)
            )
            / heat_pump_lifetime,
            "Running costs": lifetime_heat_pump_running_costs[period]
            / heat_pump_lifetime,
            "Maintenance costs": (
                heat_pump_maintenance_cost
                * heat_pump_maintenance_frequency
                * heat_pump_lifetime
            )
            / heat_pump_lifetime,
            "Subsidy": bus_subsidy / heat_pump_lifetime,
            "Total": heat_pump_10pct_financed_lifetime_costs[period]
            / heat_pump_lifetime,
        }
    )

summary_df = pd.DataFrame(rows)
summary_df = summary_df[
    [
        "Heating system",
        "Price cap period",
        "Upfront costs",
        "Loan interest",
        "Maintenance costs",
        "Running costs",
        "Subsidy",
        "Total",
    ]
]

# %%
summary_df.to_csv(
    f"{PROJECT_DIR}/outputs/data/{datetime.now().strftime('%Y%m%d')}_affordability_for_flourish_WarmHomesPlan.csv",
    index=False,
)

# %%
summary_df_difference = summary_df.pivot_table(
    columns="Heating system", index="Price cap period", values="Total", sort=False
)
summary_df_difference["Cost difference: Heat pump (no financing)"] = (
    summary_df_difference["Heat pump (no financing)"]
    - summary_df_difference["Gas boiler"]
)
summary_df_difference["Cost difference: Heat pump (3% loan)"] = (
    summary_df_difference["Heat pump (5% loan)"] - summary_df_difference["Gas boiler"]
)
summary_df_difference["Cost difference: Heat pump (5% loan)"] = (
    summary_df_difference["Heat pump (5% loan)"] - summary_df_difference["Gas boiler"]
)
summary_df_difference["Cost difference: Heat pump (10% loan)"] = (
    summary_df_difference["Heat pump (10% loan)"] - summary_df_difference["Gas boiler"]
)

# %%
summary_df_difference.to_csv(
    f"{PROJECT_DIR}/outputs/data/{datetime.now().strftime('%Y%m%d')}_affordability_for_flourish_2_WarmHomesPlan.csv",
    index=True,
)

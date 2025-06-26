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
#     display_name: asf-progress-indicators
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

# Future discounting assumptions (£1 today is worth more to society than a £1 in the future)
discount_rate = 3.5 / 100  # %; social time preference rate, as provided by HMT Green Book guidance

# %% [markdown]
# ### Installation costs and financing

# %%
# Average cost of boiler install
boiler_install_cost = 3_000

# %%
# Average cost of heat pump install
heat_pump_install_cost = 12_000

# %%
## Government support

# England and Wales
bus_subsidy = 7_500

# Scotland
scotland_grant = 7_500
scotland_interest_free_loan = min(heat_pump_install_cost - scotland_grant, 7_500)
scotland_loan_term = 5  # years

# Northern Ireland
# N/A

# %%
# Loan assumptions
loan_apr_high = 9.9 / 100  # as provided by Octopus and Aira
loan_term_high = 5  # years; as provided by Octopus and Aira

loan_apr_low = 0  # as provided by E.ON Next, British Gas
loan_term_low = 2  # years; as provided by E.ON Next, British Gas

# %%
# England and Wales

england_wales_loan_amount = heat_pump_install_cost - bus_subsidy

# High interest rate, longer repayment term scenario with duture discounting
annual_payment_high = (england_wales_loan_amount * loan_apr_high) / (1 - ((1 + loan_apr_high) ** -loan_term_high))
total_loan_payment_high = annual_payment_high * loan_term_high

discounted_total_loan_payment_high = utils.discounted_sum(annual_payment_high, loan_term_high, discount_rate)

# 0% interest rate, shorter repayment term scenario with future discounting
annual_payment_low = england_wales_loan_amount / loan_term_low
total_loan_payment_low = england_wales_loan_amount

discounted_total_loan_payment_low = utils.discounted_sum(annual_payment_low, loan_term_low, discount_rate)

# %%
# Scotland
scotland_annual_payment = scotland_interest_free_loan / scotland_loan_term

scotland_discounted_loan_payment = utils.discounted_sum(scotland_annual_payment, scotland_loan_term, discount_rate)

# %%
# Northern Ireland
ni_loan_amount = heat_pump_install_cost

# High interest rate, longer repayment term scenario with duture discounting
ni_annual_payment_high = (ni_loan_amount * loan_apr_high) / (1 - ((1 + loan_apr_high) ** -loan_term_high))
ni_total_loan_payment_high = ni_annual_payment_high * loan_term_high

ni_discounted_total_loan_payment_high = utils.discounted_sum(ni_annual_payment_high, loan_term_high, discount_rate)

# 0% interest rate, shorter repayment term scenario with future discounting
ni_annual_payment_low = ni_loan_amount / loan_term_low
ni_total_loan_payment_low = ni_loan_amount

ni_discounted_total_loan_payment_low = utils.discounted_sum(ni_annual_payment_low, loan_term_low, discount_rate)

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
]

gas_tariffs = {}
gas_standing_charges = {}
gas_unit_costs = {}
electricity_tariffs = {}
electricity_standing_charges = {}
electricity_unit_costs = {}
for period in price_cap_periods:
    # Instantiate tariff
    gas_tariff, electricity_tariff = data_getters.instantiate_tariffs(
        payment_method="Other Payment Method", price_cap=period
    )
    gas_tariffs[period] = gas_tariff
    electricity_tariffs[period] = electricity_tariff

    # Extract gas costs
    gas_standing_charges[period] = gas_tariff.calculate_nil_consumption()  # £ per customer per year
    gas_unit_costs[period] = gas_tariff.calculate_variable_consumption(1)  # £ per MWh

    # Extract electricity costs
    electricity_standing_charges[period] = electricity_tariff.calculate_nil_consumption()  # £ per customer per year
    electricity_unit_costs[period] = electricity_tariff.calculate_variable_consumption(1)  # £ per MWh

# %%
# Medium TDCV
gas_tdcv = 11.5  # MWh
electricity_tdcv = 2.7  # MWh

# %%
# Cost of boiler gas consumption (annual)
heating_gas_share = 0.97
annual_boiler_gas_consumption = gas_tdcv * heating_gas_share  # MWh per year

annual_boiler_running_costs = {}
discounted_total_boiler_running_costs = {}
for period in price_cap_periods:
    annual_boiler_running_costs[period] = (
        gas_tariffs[period].calculate_variable_consumption(annual_boiler_gas_consumption) * 1.05
    )  # £ per year, including VAT
    discounted_total_boiler_running_costs[period] = utils.discounted_sum(
        annual_boiler_running_costs[period], boiler_lifetime, discount_rate
    )

# %%
# Cost of heat pump electricity consumption (annual)
boiler_efficiency = 0.85
annual_heat_demand = annual_boiler_gas_consumption * boiler_efficiency  # MWh per year

heat_pump_efficiency = 3.0

annual_heat_pump_electricity_consumption = annual_heat_demand / heat_pump_efficiency  # MWh per year

annual_heat_pump_running_costs = {}
discounted_total_heat_pump_running_costs = {}
for period in price_cap_periods:
    annual_heat_pump_running_costs[period] = (
        electricity_tariffs[period].calculate_variable_consumption(annual_heat_pump_electricity_consumption) * 1.05
    )  # £ per year, including VAT
    discounted_total_heat_pump_running_costs[period] = utils.discounted_sum(
        annual_heat_pump_running_costs[period], heat_pump_lifetime, discount_rate
    )

# %% [markdown]
# ### Maintenance

# %%
# Cost of boiler maintenance
boiler_maintenance_frequency = 1  # times per year
boiler_maintenance_cost = 130  # £ per maintenenace session

discounted_total_boiler_maintenance_cost = utils.discounted_sum(boiler_maintenance_cost, boiler_lifetime, discount_rate)

# %%
# Cost of heat pump maintenance
heat_pump_maintenance_frequency = 1  # times per year
heat_pump_maintenance_cost = 210  # £ per maintenenace session

discounted_total_heat_pump_maintenance_cost = utils.discounted_sum(
    heat_pump_maintenance_cost, heat_pump_lifetime, discount_rate
)

# %% [markdown]
# ### **Comparing total lifetime costs**

# %% [markdown]
# Boiler
#
# - Assume no financing for upfront cost

# %%
# With discounting
discounted_boiler_lifetime_costs = {}
for period in price_cap_periods:
    discounted_boiler_lifetime_costs[period] = (
        boiler_install_cost  # assume no financing
        + discounted_total_boiler_running_costs[period]
        + discounted_total_boiler_maintenance_cost
    )

# Without discounting
boiler_lifetime_costs = {}
for period in price_cap_periods:
    boiler_lifetime_costs[period] = (
        boiler_install_cost
        + (annual_boiler_running_costs[period] * boiler_lifetime)
        + (boiler_maintenance_cost * boiler_maintenance_frequency * boiler_lifetime)
    )

# %% [markdown]
# Heat pump

# %%
# With discounting
discounted_heat_pump_lifetime_costs = {}

# England and Wales
discounted_heat_pump_lifetime_costs["England Wales low"] = {}
discounted_heat_pump_lifetime_costs["England Wales high"] = {}
for period in price_cap_periods:
    discounted_heat_pump_lifetime_costs["England Wales low"][period] = (
        discounted_total_loan_payment_low
        + discounted_total_heat_pump_running_costs[period]
        + discounted_total_heat_pump_maintenance_cost
    )
    discounted_heat_pump_lifetime_costs["England Wales high"][period] = (
        discounted_total_loan_payment_high
        + discounted_total_heat_pump_running_costs[period]
        + discounted_total_heat_pump_maintenance_cost
    )

# Scotland
discounted_heat_pump_lifetime_costs["Scotland"] = {}
for period in price_cap_periods:
    discounted_heat_pump_lifetime_costs["Scotland"][period] = (
        scotland_discounted_loan_payment
        + discounted_total_heat_pump_running_costs[period]
        + discounted_total_heat_pump_maintenance_cost
    )

# Northern Ireland
discounted_heat_pump_lifetime_costs["Northern Ireland low"] = {}
discounted_heat_pump_lifetime_costs["Northern Ireland high"] = {}
for period in price_cap_periods:
    discounted_heat_pump_lifetime_costs["Northern Ireland low"][period] = (
        ni_discounted_total_loan_payment_low
        + discounted_total_heat_pump_running_costs[period]
        + discounted_total_heat_pump_maintenance_cost
    )
    discounted_heat_pump_lifetime_costs["Northern Ireland high"][period] = (
        ni_discounted_total_loan_payment_high
        + discounted_total_heat_pump_running_costs[period]
        + discounted_total_heat_pump_maintenance_cost
    )

# %%
# Without discounting
heat_pump_lifetime_costs = {}

# England and Wales
heat_pump_lifetime_costs["England Wales low"] = {}
heat_pump_lifetime_costs["England Wales high"] = {}
for period in price_cap_periods:
    heat_pump_lifetime_costs["England Wales low"][period] = (
        total_loan_payment_low
        + (annual_heat_pump_running_costs[period] * heat_pump_lifetime)
        + (heat_pump_maintenance_cost * heat_pump_maintenance_frequency * heat_pump_lifetime)
    )
    heat_pump_lifetime_costs["England Wales high"][period] = (
        total_loan_payment_high
        + (annual_heat_pump_running_costs[period] * heat_pump_lifetime)
        + (heat_pump_maintenance_cost * heat_pump_maintenance_frequency * heat_pump_lifetime)
    )

# Scotland
heat_pump_lifetime_costs["Scotland"] = {}
for period in price_cap_periods:
    heat_pump_lifetime_costs["Scotland"][period] = (
        scotland_interest_free_loan
        + (annual_heat_pump_running_costs[period] * heat_pump_lifetime)
        + (heat_pump_maintenance_cost * heat_pump_maintenance_frequency * heat_pump_lifetime)
    )

# Northern Ireland
heat_pump_lifetime_costs["Northern Ireland low"] = {}
heat_pump_lifetime_costs["Northern Ireland high"] = {}
for period in price_cap_periods:
    heat_pump_lifetime_costs["Northern Ireland low"][period] = (
        ni_total_loan_payment_low
        + (annual_heat_pump_running_costs[period] * heat_pump_lifetime)
        + (heat_pump_maintenance_cost * heat_pump_maintenance_frequency * heat_pump_lifetime)
    )
    heat_pump_lifetime_costs["Northern Ireland high"][period] = (
        ni_total_loan_payment_high
        + (annual_heat_pump_running_costs[period] * heat_pump_lifetime)
        + (heat_pump_maintenance_cost * heat_pump_maintenance_frequency * heat_pump_lifetime)
    )

# %% [markdown]
# Note: Discounting tells us how much future costs/bills is worth in today's money.

# %% [markdown]
# ### Summarising

# %%
rows = []

for period in price_cap_periods:
    rows.append(
        {
            "Heating system (region)": "Gas boiler (UK)",
            "Price cap period": utils.convert_period_to_string(gas_tariffs[period].price_cap_period),
            "Upfront costs": boiler_install_cost,
            "Running costs": discounted_total_boiler_running_costs[period],
            "Maintenance costs": discounted_total_boiler_maintenance_cost,
            "Total": discounted_boiler_lifetime_costs[period],
        }
    )

    rows.append(
        {
            "Heating system (region)": "Heat pump (England and Wales, low interest loan)",
            "Price cap period": utils.convert_period_to_string(gas_tariffs[period].price_cap_period),
            "Upfront costs": discounted_total_loan_payment_low,
            "Running costs": discounted_total_heat_pump_running_costs[period],
            "Maintenance costs": discounted_total_heat_pump_maintenance_cost,
            "Total": discounted_heat_pump_lifetime_costs["England Wales low"][period],
        }
    )

    rows.append(
        {
            "Heating system (region)": "Heat pump (England and Wales, high interest loan)",
            "Price cap period": utils.convert_period_to_string(gas_tariffs[period].price_cap_period),
            "Upfront costs": discounted_total_loan_payment_high,
            "Running costs": discounted_total_heat_pump_running_costs[period],
            "Maintenance costs": discounted_total_heat_pump_maintenance_cost,
            "Total": discounted_heat_pump_lifetime_costs["England Wales high"][period],
        }
    )

    rows.append(
        {
            "Heating system (region)": "Heat pump (Scotland)",
            "Price cap period": utils.convert_period_to_string(gas_tariffs[period].price_cap_period),
            "Upfront costs": scotland_discounted_loan_payment,
            "Running costs": discounted_total_heat_pump_running_costs[period],
            "Maintenance costs": discounted_total_heat_pump_maintenance_cost,
            "Total": discounted_heat_pump_lifetime_costs["Scotland"][period],
        }
    )

    rows.append(
        {
            "Heating system (region)": "Heat pump (Northern Ireland, low interest loan)",
            "Price cap period": utils.convert_period_to_string(gas_tariffs[period].price_cap_period),
            "Upfront costs": ni_discounted_total_loan_payment_low,
            "Running costs": discounted_total_heat_pump_running_costs[period],
            "Maintenance costs": discounted_total_heat_pump_maintenance_cost,
            "Total": discounted_heat_pump_lifetime_costs["Northern Ireland low"][period],
        }
    )

    rows.append(
        {
            "Heating system (region)": "Heat pump (Northern Ireland, high interest loan)",
            "Price cap period": utils.convert_period_to_string(gas_tariffs[period].price_cap_period),
            "Upfront costs": ni_discounted_total_loan_payment_high,
            "Running costs": discounted_total_heat_pump_running_costs[period],
            "Maintenance costs": discounted_total_heat_pump_maintenance_cost,
            "Total": discounted_heat_pump_lifetime_costs["Northern Ireland high"][period],
        }
    )

# %%
summary_df = pd.DataFrame(rows)
summary_df = summary_df[
    [
        "Heating system (region)",
        "Price cap period",
        "Upfront costs",
        "Maintenance costs",
        "Running costs",
        "Total",
    ]
]

columns_to_format = ["Upfront costs", "Running costs", "Maintenance costs", "Total"]
for col in columns_to_format:
    summary_df[col] = summary_df[col].apply(lambda x: f"{x:,.2f}")

# %%
summary_df.to_csv(
    f"{PROJECT_DIR}/outputs/data/{datetime.now().strftime('%Y%m%d')}_affordability_for_flourish.csv",
    index=False,
)

from typing import List

import pandas as pd

"""
Helper functions for lifetime cost indicator
"""


def discounted_sum(annual_value: float, years: int, discount_rate: float) -> float:
    """Calculate the present (discounted) value of a constant annual cost or benefit
    over a number of years using a given discount rate.

    Parameters
    ----------
    annual_value : float
        The recurring annual amount (e.g., cost or benefit).
    years : int
        The number of years over which the value recurs.
    discount_rate : float
        The annual discount rate (as a decimal, e.g., 0.035 for 3.5%).

    Returns:
    -------
    float
        The total discounted sum over the specified period.
    """
    return sum(annual_value / ((1 + discount_rate) ** t) for t in range(1, years + 1))


def convert_period_to_string(period: pd.Interval) -> str:
    """Convert a pandas Interval representing a date range into a readable string.

    Parameters
    ----------
    period : pd.Interval
        Interval object with datetime-like `.left` and `.right`.

    Returns:
    -------
    str
        A formatted string like 'Jan - Mar 2023'.
    """
    return f"{period.left.strftime('%b')} - {period.right.strftime('%b %Y')}"


"""
Helper functions for perception indicator
"""


def reformat_public_attitudes_tracking_survey_df(
    raw_data: pd.DataFrame, hp_type_lookup: dict, hp_type: str
) -> pd.DataFrame:
    """Reformat DESNZ Public Attitudes Tracker data for a selected heat pump type.

    Parameters
    ----------
    raw_data : pd.DataFrame
        Raw survey dataframe containing data for multiple heat pump types.
    hp_type_lookup : dict
        Dictionary mapping heat pump type keys to corresponding dataframe column names.
    hp_type : str
        Specific heat pump type to extract and reformat.

    Returns:
    -------
    pd.DataFrame
        Tidy dataframe with wave, year, variable, and heat pump type information.
    """
    df = raw_data[hp_type_lookup.get(hp_type)]

    # Drop redundant rows and set header row
    df = df.iloc[7:].reset_index(drop=True)
    df.columns = df.iloc[0]
    df = df.drop(index=0)
    df = df.reset_index(drop=True)

    # Drop column for Total across all historical waves
    df = df.drop("Total", axis=1)

    # Add column heat pump type label
    df["Heat pump type"] = hp_type

    # Melt
    df = df.melt(
        id_vars=[
            "Heat pump type",
            "Subgroup identifier row",
        ],
        var_name="Wave",
        value_name="Value",
    )

    # Rename columns
    df = df.rename(columns={"Subgroup identifier row": "Variable"})

    # Remove line break characters
    df["Wave"] = df["Wave"].replace(r"\n", " ", regex=True)

    # Create year column
    df["Year"] = df["Wave"].str.extract(r"(\d{4})")
    return df


def fill_low_cells(row: pd.Series, target_cols: List[str]) -> pd.Series:
    """Fills cells with the string 'low' (or any non-numeric) in specified columns of a DataFrame row,
    distributing the remaining proportion evenly among them so that the total sums to 1.0.

    Parameters
    ----------
    row : pd.Series
        A single row from a DataFrame.
    target_cols : List[str]
        List of column names in the row to check and fill.

    Returns:
    -------
    pd.Series
        The modified row with 'low' or missing values replaced by evenly distributed fill values.
    """
    selected = row[target_cols]

    # Convert to numeric, turning 'low' into NaN
    numeric = pd.to_numeric(selected, errors="coerce")

    low_count = numeric.isna().sum()
    known_sum = numeric.sum(skipna=True)
    remaining = 1.0 - known_sum

    fill_value = remaining / low_count if low_count > 0 else 0

    filled = numeric.fillna(fill_value)

    for col in target_cols:
        row[col] = filled[col]

    return row

# %%
from datetime import datetime

from asf_progress_indicators import PROJECT_DIR
from asf_progress_indicators.getters import data_getters
from asf_progress_indicators.utils import utils

# %%
# Read Excel sheet
winter_pat = data_getters.get_public_attitudes_tracking_survey()

# %%
# Select tables of interest
hp_type_lookup = {
    "Air source heat pump": "LCHEATINSTALL01",
    "Ground source heat pump": "LCHEATINSTALL02",
    "Hybrid heat pump": "LCHEATINSTALL03",
}

# %%
# Create tidy dataframes for each heat pump type
ashp_likelihood = utils.reformat_public_attitudes_tracking_survey_df(winter_pat, hp_type_lookup, "Air source heat pump")
gshp_likelihood = utils.reformat_public_attitudes_tracking_survey_df(
    winter_pat, hp_type_lookup, "Ground source heat pump"
)
hybrid_likelihood = utils.reformat_public_attitudes_tracking_survey_df(winter_pat, hp_type_lookup, "Hybrid heat pump")
master_likelihood = utils.pd.concat([ashp_likelihood, gshp_likelihood, hybrid_likelihood])

# %%
ashp_likelihood["Variable"].unique()

# %%
# Create new summary dataframe for import into Flourish
summary_data = master_likelihood.pivot(
    index=["Year", "Heat pump type"], columns="Variable", values="Value"
).reset_index()[
    [
        "Year",
        "Heat pump type",
        "Net: Total likely",
        "Net: Total not likely",
        "Not applicable – I already have this installed in my home",
        "Not applicable – not my decision",
        "I don’t know enough about this heating system to decide",
    ]
]

# Fill in "low" entries with numeric values
target_cols = [
    "Net: Total likely",
    "Net: Total not likely",
    "Not applicable – I already have this installed in my home",
    "Not applicable – not my decision",
    "I don’t know enough about this heating system to decide",
]

# Apply row-wise
summary_data = summary_data.apply(lambda row: utils.fill_low_cells(row, target_cols=target_cols), axis=1)

# Rename columns
summary_data = summary_data.rename(
    columns={
        "Net: Total likely": "Likely",
        "Net: Total not likely": "Not likely",
        "Not applicable – I already have this installed in my home": "Already have one",
        "Not applicable – not my decision": "Not my decision",
        "I don’t know enough about this heating system to decide": "Don't know enough about heating system to decide",
    }
)

# %%
summary_data.to_csv(
    f"{PROJECT_DIR}/outputs/data/{datetime.now().strftime('%Y%m%d')}_perception_for_flourish.csv",
    index=False,
)

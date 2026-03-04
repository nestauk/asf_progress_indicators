# %%
import pandas
import calendar
from datetime import date
import matplotlib.pyplot as pyplot
from scipy.stats import gaussian_kde
from statsmodels.api import OLS, QuantReg, qqplot_2samples
import numpy

# %%
# Get all vahp follow-up survey data
data = (pandas.read_csv("../../inputs/data/Your Heat pump journey (v1)_Submissions_2025-11-11.csv")
        .loc[lambda df: (df['By choosing “Yes, I agree”, I understand: \n'] == 'Yes, I agree')
             & (df["Please confirm that you have visited a heat pump in person, at the property of a host, as part of the 'Visit a Heat Pump' service.\n"] == 'Yes, I have visited a host')])
data.shape

# %%
# Subset of visitors who have bought a heat pump since visiting.
installs = data.loc[data['Which of the following most applies to you since you visited a heat pump?'] == "I have installed a heat pump in my home since visiting a heat pump"]
installs.shape

# %%
def _parse_day(day):
    if isinstance(day, str):
        day = day.strip()
        if day.isnumeric():
            return pandas.to_numeric(day)
        else:
            # Sometimes people put the whole date in the first box
           return None 
    elif isinstance(day, (int, float)) & (not pandas.isna(day)):
        if int(day) in range(1,32):
            return int(day)
        else:
            return None
    else:
        return None

def _parse_month(month):
    # Months can be tricky as they can be numeric or recognised strings
    if isinstance(month, (int, float)) & (not pandas.isna(month)):
        if int(month) in range(1,13):
            return int(month)
    elif isinstance(month, str):
        if month.isnumeric():
            if pandas.to_numeric(month) in range(1,13):
                return pandas.to_numeric(month)
            else:
                return None
        else:
            month = month.lower().strip()
            months = [m.lower() for m in calendar.month_name[1:]]
            month_abbr = [m.lower() for m in calendar.month_abbr[1:]]
            if month in months:
                return months.index(month) + 1
            elif month in month_abbr:
                return month_abbr.index(month) + 1
            else:
                return None
    else:
        return None

def _parse_year(year):
    # Years could be 4 digit or 2 digit.
    if isinstance(year, (int, float)) & (not pandas.isna(year)):
        if int(year) in range(2000, date.today().year + 1):
            return int(year)
        elif int(year) in range(0, date.today().year - 1999):
            return int(year) + 2000
        else:
            return None
    if isinstance(year, str):
        if len(year) == 4:
            try:
                if int(year) in range(2000, date.today().year + 1):
                    return int(year)
            except:
                pass
        elif len(year) == 2:
            try:
                if int(year) in range(0, date.today().year - 1999):
                    return int(year) + 2000
            except:
                pass
    else:
        return None

def clean_date(row, exact_column, day_column, month_column, year_column, use_calendar_column, calendar_column, approximate_date):
    if row[exact_column] == 'I know the exact date':
        # exact dates either use a calendar selector or day, month, year boxes.
        if row[use_calendar_column] in ['Use Calendar', 'Use calendar']:
            return (pandas.to_datetime(row[calendar_column]), 'exact')
        else: # use day, month, year boxes
            day = _parse_day(row[day_column])
            month = _parse_month(row[month_column])
            year = _parse_year(row[year_column])
            if bool(day) & bool(month) & bool(year):
                return (pandas.to_datetime(f"{year}-{month}-{day}"), 'exact')
            elif isinstance(row[day_column], str):
                if len(row[day_column].split(" ")) == 3:
                    # Special case in which people put the whole date in box 1
                    day, month, year = row[day_column].split(" ")
                    day = _parse_day(day)
                    month = _parse_month(month)
                    year = _parse_year(year)
                    if bool(day) & bool(month) & bool(year):
                        return (pandas.to_datetime(f"{year}-{month}-{day}"), 'exact')
                else:
                    return (None, "")
            else:
                return (None, "")
    elif row[exact_column] == 'I know the approximate date':
        return (pandas.to_datetime(row[approximate_date]), 'approx')
    else:
        return (None, "")
        

# %%
# Process final quote dates
installs.loc[:, ['final_quotation_date', 'final_quote_quality']] = installs.apply(lambda row:
                                              clean_date(
                                                  row,
                                                  'When did you receive your final quote?\n',
                                                  'Please enter the date you received your final quote',
                                                  'Month',
                                                  'Year',
                                                  'use_calendar_check_final_quote',
                                                  'final_quote_date',
                                                  'Please select the approximate date you received your final quote\n'),
                                                  axis=1).apply(pandas.Series).rename(columns={0: 'final_quotation_date', 1: 'final_quote_quality'})

# %%
# Process work start dates
installs.loc[:, ['start_work_date', 'start_work_quality']] = installs.apply(lambda row:
                                              clean_date(
                                                  row,
                                                  'When did the installation work start at your home?\n',
                                                  'Please enter the date the installation work started at your home\n',
                                                  'Month (2)',
                                                  'Year (2)',
                                                  'use_calendar_check_installation_start',
                                                  'installation_start_date',
                                                  'Please select the approximate date the installation work started at your home'),
                                                  axis=1).apply(pandas.Series).rename(columns={0: 'start_work_date', 1: 'start_work_quality'})

# %%
# process work end dates
installs.loc[:, ['end_work_date', 'end_work_quality']] = installs.apply(lambda row:
                                                  clean_date(
                                                  row,
                                                  'When was the installation completed at your home?\n',
                                                  'Please enter the date the installation work was completed at your home',
                                                  'Month (3)',
                                                  'Year (3)',
                                                  'use_calendar_check_installation_completed',
                                                  'Select a date',
                                                  'Please select the approximate date the installation work was completed at your home'),
                                                  axis=1).apply(pandas.Series).rename(columns={0: 'end_work_date', 1: 'end_work_quality'})

# %%
# check we got some dates
installs[['final_quotation_date', 'start_work_date', 'end_work_date']].head()

# %%
# get missingness patterns
installs.loc[:, 'patterns'] = installs.loc[:, ['final_quote_quality', 'start_work_quality', 'end_work_quality']].replace("", 'Unknown').agg("_".join, axis=1)

# %%
installs.loc[:, 'patterns'].value_counts().to_frame().reset_index(names='pattern').assign(prop = lambda x: x['count'] / x['count'].sum())

# %%
installs['final_quote_quality'].value_counts()

# %%
installs['start_work_quality'].value_counts()

# %%
installs['end_work_quality'].value_counts()

# %%
installs.groupby(['final_quote_quality', 'end_work_quality'])['Submission ID'].count().reset_index()

# %%
installs.groupby(['start_work_quality', 'end_work_quality'])['Submission ID'].count().reset_index()

# %% [markdown]
# ## Compute durations

# %%
def compute_duration(start_time, start_quality, end_time, end_quality):
    if pandas.isnull(start_time) or pandas.isnull(end_time):
        return (pandas.NA, "")
    elif (start_quality == 'exact') and (end_quality == 'exact'):
        return ((end_time - start_time).days, "exact")
    elif (start_quality == 'approx') or (end_quality == 'approx'):
        return ((end_time - start_time).days, "approx")
    else:
        raise AttributeError

# %%
installs.loc[:, ['quote_complete_duration', 'quote_complete_duration_quality']] = (
    installs
    .apply(lambda df: compute_duration(df['final_quotation_date'], df['final_quote_quality'], df['end_work_date'], df['end_work_quality']), axis=1)
    .apply(pandas.Series)
    .rename(columns={0: 'quote_complete_duration', 1: 'quote_complete_duration_quality'}))

# %%
def lower_quartile(x): return x.quantile(0.25)
def upper_quartile(x): return x.quantile(0.75)

# %%
(installs
 .loc[lambda df: df['quote_complete_duration'] > 0,:]
 .groupby('quote_complete_duration_quality')
 ['quote_complete_duration']
 .agg(['count', 'mean', 'std', 'median', lower_quartile, upper_quartile, 'min', 'max']))

# %%
model_data = (installs
              .loc[lambda df: df['quote_complete_duration'] > 0, ['quote_complete_duration', 'quote_complete_duration_quality']]
              .assign(quote_complete_duration = lambda x: x['quote_complete_duration'].astype(float)))

# %%
# exact/approx explains none the variation in quote duration.
model = OLS.from_formula('quote_complete_duration ~ quote_complete_duration_quality', data=model_data).fit()
model.summary()

# %%
# exact/approx explains none the variation in quote duration.
model = QuantReg.from_formula('quote_complete_duration ~ quote_complete_duration_quality', data=model_data).fit()
model.summary()

# %%
# exact/approx explains none the variation in quote duration.
model = QuantReg.from_formula('quote_complete_duration ~ quote_complete_duration_quality', data=model_data).fit(0.25)
model.summary()

# %%
f, ax = pyplot.subplots(figsize=(8,6))

qqplot_2samples(model_data.loc[lambda df: df['quote_complete_duration_quality'] == 'exact', 'quote_complete_duration'],
                model_data.loc[lambda df: df['quote_complete_duration_quality'] == 'approx', 'quote_complete_duration'],
                xlabel= 'exact durations (days)',
                ylabel= 'approx durations (days)',
                line='45',
                ax=ax)

ax.set_title("qqplot for duration between final quote and work completed.")

# %%
xs = numpy.arange(0,336, 7)
ys_full = gaussian_kde(installs.loc[lambda df: df['quote_complete_duration'] > 0, 'quote_complete_duration'].astype(float)).evaluate(xs)

exact = installs.loc[lambda df: (df['quote_complete_duration'] > 0) & (df['quote_complete_duration_quality'] == 'exact'), 'quote_complete_duration'].astype(float)
approx = installs.loc[lambda df: (df['quote_complete_duration'] > 0) & (df['quote_complete_duration_quality'] == 'approx'), 'quote_complete_duration'].astype(float)

ys_exact = gaussian_kde(exact).evaluate(xs)
ys_approx = gaussian_kde(approx).evaluate(xs)

# %%
f, ax = pyplot.subplots(figsize=(8,6))

ax.plot(xs, ys_full, color='0.75', linestyle='dashed', label='combined')
ax.plot(xs, ys_exact, color='dodgerblue', label='exact')
ax.plot(xs, ys_approx, color='indianred', label='approx')

ax.plot(exact, [0.0001]*len(exact), '|', color='dodgerblue')
ax.plot(approx, [0.0001]*len(approx), '|', color='indianred')

ax.set_title("Time from accepting final quote to completed installation", loc='left')
ax.set_xlabel('Duration (Days)')
ax.set_ylabel('Density')
ax.legend()

# %%
# modes (10-12 weeks)
xs[ys_exact.argmax()], xs[ys_approx.argmax()], xs[ys_full.argmax()]

# %%
model = gaussian_kde(installs.loc[lambda df: df['quote_complete_duration'] > 0, 'quote_complete_duration'].astype(float))

# %%
# Get value for integral of 0.25 - 49 days
model.integrate_box_1d(-numpy.inf, 49)

# %%
installs['How long, to the nearest week, was the period from receiving your final quote to the completion of the installation work at your home?'].dropna().mul(7).agg(['count', 'mean', 'std', 'median', lower_quartile, upper_quartile, 'min', 'max'])

# %% [markdown]
# ## Work Duration

# %%
installs.loc[:, ['work_duration', 'work_duration_quality']] = (
    installs
    .apply(lambda df: compute_duration(df['start_work_date'], df['start_work_quality'], df['end_work_date'], df['end_work_quality']), axis=1)
    .apply(pandas.Series)
    .rename(columns={0: 'work_duration', 1: 'work_duration_quality'}))

# %%
(installs
 .loc[lambda df: (df['work_duration'] > 0) & (df['work_duration'] < 80),:]
 .groupby('work_duration_quality')
 ['work_duration']
 .agg(['count', 'mean', 'std', 'median', lower_quartile, upper_quartile, 'min', 'max']))

# %%
installs['How many days in total did it take to install the heat pump in your home?'].dropna().agg(['count', 'mean', 'std', 'median', lower_quartile, upper_quartile, 'min', 'max'])

# %%
model_data = (installs
              .loc[lambda df: (df['work_duration'] > 0) & (df['work_duration'] < 80), ['work_duration', 'work_duration_quality']]
              .assign(work_duration = lambda x: x['work_duration'].astype(float)))

# %%
f, ax = pyplot.subplots(figsize=(8,6))

qqplot_2samples(model_data.loc[lambda df: df['work_duration_quality'] == 'exact', 'work_duration'],
                model_data.loc[lambda df: df['work_duration_quality'] == 'approx', 'work_duration'],
                xlabel= 'exact dates',
                ylabel= 'approx dates',
                line='45', ax=ax)

ax.set_title("qqplot for duration between work started and work completed.")

# %%
model = QuantReg.from_formula('work_duration ~ work_duration_quality', data=model_data).fit()
model.summary()

# %%
model = QuantReg.from_formula('work_duration ~ work_duration_quality', data=model_data).fit(0.25)
model.summary()

# %%
xs = numpy.arange(0,85, 1)
ys_full = gaussian_kde(installs.loc[lambda df: (df['work_duration'] > 0) & (df['work_duration'] < 80), 'work_duration'].astype(float)).evaluate(xs)

exact = installs.loc[lambda df: (df['work_duration'] > 0) & (df['work_duration'] < 80) & (df['work_duration_quality'] == 'exact'), 'work_duration'].astype(float)
approx = installs.loc[lambda df: (df['work_duration'] > 0) & (df['work_duration'] < 80) & (df['work_duration_quality'] == 'approx'), 'work_duration'].astype(float)

ys_exact = gaussian_kde(exact).evaluate(xs)
ys_approx = gaussian_kde(approx).evaluate(xs)

# %%
f, ax = pyplot.subplots(figsize=(8,6))

ax.plot(xs, ys_full, color='0.75', linestyle='dashed', label='combined')
ax.plot(xs, ys_exact, color='dodgerblue', label='exact')
ax.plot(xs, ys_approx, color='indianred', label='approx')

ax.plot(exact, [0.0001]*len(exact), '|', color='dodgerblue')
ax.plot(approx, [0.0001]*len(approx), '|', color='indianred')

ax.set_title("Time from work starting to completed installation", loc='left')
ax.set_xlabel('Duration (Days)')
ax.set_ylabel('Density')

ax.legend()

# %%
# modes 5 days - 1 week of working days?
xs[ys_exact.argmax()], xs[ys_approx.argmax()], xs[ys_full.argmax()]

# %% [markdown]
# ## Relationship Between Quote and Work Duration
# 
# No strong evidence of an association.

# %%
installs.loc[:, ['pre_work_duration', 'pre_work_duration_quality']] = (
    installs
    .apply(lambda df: compute_duration(df['final_quotation_date'], df['final_quote_quality'] , df['start_work_date'], df['start_work_quality']), axis=1)
    .apply(pandas.Series)
    .rename(columns={0: 'pre_work_duration', 1: 'pre_work_duration_quality'}))

# %%
model_data = (installs[['pre_work_duration', 'work_duration']]
              .dropna()
              .loc[lambda df: (df['pre_work_duration'] > 0) & (df['work_duration'] > 0) & (df['work_duration'] < 80)]
              .assign(pre_work_duration = lambda x: x['pre_work_duration'].astype(float),
                      work_duration = lambda x: x['work_duration'].astype(float))).reset_index(drop=True)

# %%
model_data[['pre_work_duration', 'work_duration']].corr(method='spearman')

# %%
pyplot.scatter(model_data['pre_work_duration'], model_data['work_duration'])

# %%
model = OLS.from_formula('work_duration ~ pre_work_duration', data=model_data).fit()

# %%
model.summary()



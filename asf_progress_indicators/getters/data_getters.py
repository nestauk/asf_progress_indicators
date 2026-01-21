import io
from typing import Optional, Tuple

import asf_levies_model.getters.load_data as data
import asf_levies_model.tariffs as tariffs
import boto3
import pandas as pd
import requests
from asf_levies_model.tariffs import Tariff

from asf_progress_indicators import config


def _read_s3_csv_to_frame(
    bucket_name: str, s3_key: str, chunksize: int = None
) -> pd.DataFrame:
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket_name, Key=s3_key)
    content = io.BytesIO(obj["Body"].read())

    if chunksize:
        chunks = pd.read_csv(content, chunksize=chunksize)
        return pd.concat(chunks, ignore_index=True)
    else:
        return pd.read_csv(content)


def get_mcs_epc_data() -> pd.DataFrame:
    """Load and return combined MCS EPC data from the ASF core data S3 bucket.

    Returns:
    -------
    pd.DataFrame
        Combined MCS EPC dataset as a pandas DataFrame, using the source file
        specified in config.
    """
    return _read_s3_csv_to_frame(
        bucket_name="asf-core-data",
        s3_key=config.get("data_sources").get("mcs_epc"),
        chunksize=100000,
    )


def _read_s3_parquet_to_frame(bucket_name: str, s3_key: str) -> pd.DataFrame:
    """Downloads a parquet file from a specified S3 bucket and returns it as pandas DataFrame.

    Parameters
    ----------
    s3_file_path : str
        The S3 key (file path) within the bucket.

    Returns
    -------
    io.BytesIO
        A file-like object containing the file content.
    """
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket_name, Key=s3_key)
    content = pd.read_parquet(io.BytesIO(obj["Body"].read()))
    return content


def get_territorial_emissions_data() -> pd.DataFrame:
    """Load and return DESNZ UK territorial greenhouse gas emission data from the ASF mission data tool S3 bucket.

    Returns:
    -------
    pd.DataFrame
        Combined MCS EPC dataset as a pandas DataFrame, using the source file
        specified in config.
    """
    return _read_s3_parquet_to_frame(
        bucket_name="asf-mission-data-tool",
        s3_key=config.get("data_sources").get("uk_territorial_emissions"),
    )


def _read_excel_to_frame(dataset_name: str) -> Optional[dict[str, pd.DataFrame]]:
    try:
        response = requests.get(config.get("data_sources").get(dataset_name))
        if response.status_code == 200:
            file_content = io.BytesIO(response.content)
            # Read all sheets into a dictionary
            all_sheets = pd.read_excel(file_content, sheet_name=None)
            return all_sheets
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error occurred while reading Excel file: {e}")
        return None


def get_heat_pump_deployment_statistics() -> dict[str, pd.DataFrame]:
    """Load and return DESNZ Heat Pump Deployment Quarterly Statistics.

    Each key-value pair in the returned dictionary corresponds to an Excel sheet,
    where the key is the sheet name and the value is the associated DataFrame.

    Returns:
    -------
    dict[str, pd.DataFrame]
        Dictionary of DataFrames for each sheet in the Excel file.
    """
    return _read_excel_to_frame(
        dataset_name="heat_pump_deployment_quarterly_statistics"
    )


def get_cb7_accompanying_data() -> dict[str, pd.DataFrame]:
    """Load and return CCC Seventh Carbon Budget Methodology accompanying data.

    Each key-value pair in the returned dictionary corresponds to an Excel sheet,
    where the key is the sheet name and the value is the associated DataFrame.

    Returns:
    -------
    dict[str, pd.DataFrame]
        Dictionary of DataFrames for each sheet in the Excel file.
    """
    return _read_excel_to_frame(dataset_name="cb7_accompanying_data")


def get_public_attitudes_tracking_survey() -> dict[str, pd.DataFrame]:
    """Load and return DESNZ Public Attitudes Tracking Survey Winter Timeseries data.

    Each key-value pair in the returned dictionary corresponds to an Excel sheet,
    where the key is the sheet name and the value is the associated DataFrame.

    Returns:
    -------
    dict[str, pd.DataFrame]
        Dictionary of DataFrames for each sheet in the Excel file.
    """
    return _read_excel_to_frame(dataset_name="public_attitudes_tracking_survey_winter")


def instantiate_tariffs(payment_method: str, price_cap: str) -> Tuple[Tariff, Tariff]:
    """Create gas and electricity Tariff objects from Ofgem price cap data.

    Parameters
    ----------
    payment_method : str
        Payment method of interest, valid arguments are: Other Payment Method, PPM, Standard Credit.

    Returns:
    -------
    Tuple[Tariff, Tariff]
        Gas tariff and electricity tariff for payment method provided.
    """
    # Get Annex 9
    fileobject = data.download_annex_9(as_fileobject=True)

    if payment_method == "Other Payment Method":
        gas_tariff = tariffs.GasOtherPayment.from_dataframe(
            data.process_tariff_gas_other_payment_nil(fileobject),
            data.process_tariff_gas_other_payment_typical(fileobject),
            price_cap=price_cap,
        )
        electricity_tariff = tariffs.ElectricityOtherPayment.from_dataframe(
            data.process_tariff_elec_other_payment_nil(fileobject),
            data.process_tariff_elec_other_payment_typical(fileobject),
            price_cap=price_cap,
        )
    elif payment_method == "PPM":
        gas_tariff = tariffs.GasPPM.from_dataframe(
            data.process_tariff_gas_ppm_nil(fileobject),
            data.process_tariff_gas_ppm_typical(fileobject),
            price_cap=price_cap,
        )
        electricity_tariff = tariffs.ElectricityPPM.from_dataframe(
            data.process_tariff_elec_ppm_nil(fileobject),
            data.process_tariff_elec_ppm_typical(fileobject),
            price_cap=price_cap,
        )
    elif payment_method == "Standard Credit":
        gas_tariff = tariffs.GasStandardCredit.from_dataframe(
            data.process_tariff_gas_standard_credit_nil(fileobject),
            data.process_tariff_gas_standard_credit_typical(fileobject),
            price_cap=price_cap,
        )
        electricity_tariff = tariffs.ElectricityStandardCredit.from_dataframe(
            data.process_tariff_elec_standard_credit_nil(fileobject),
            data.process_tariff_elec_standard_credit_typical(fileobject),
            price_cap=price_cap,
        )

    else:
        raise KeyError(
            "Please provide a valid payment method (Other Payment Method, PPM or Standard Credit.)"
        )

    fileobject.close()

    return gas_tariff, electricity_tariff

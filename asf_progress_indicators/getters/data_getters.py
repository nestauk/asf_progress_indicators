import io
from typing import Optional

import boto3
import pandas as pd
import requests

from asf_progress_indicators import config


def _read_s3_csv_to_frame(bucket_name: str, file_name: str, chunksize: int = None) -> pd.DataFrame:
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
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
        specified in the configuration.
    """
    return _read_s3_csv_to_frame(
        bucket_name="asf-core-data",
        file_name=config.get("data_sources").get("mcs_epc"),
        chunksize=100000,
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
    return _read_excel_to_frame(dataset_name="heat_pump_deployment_quarterly_statistics")

# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 15:59:37 2019

@author: MichaelEK
"""
from pdsql import mssql
import pandas as pd
import numpy as np
from pyproj import Proj, transform

##########################################
### Parameters

## Convert projections
from_crs = Proj('+proj=tmerc +ellps=GRS80 +a=6378137.0 +f=298.257222101 +towgs84=0,0,0,0,0,0,0 +pm=0  +lon_0=173 +x_0=1600000 +y_0=10000000 +k_0=0.9996 +lat_0=0 +units=m +axis=enu +no_defs', preserve_units=True)
to_crs = Proj('+proj=longlat +datum=WGS84 +ellps=WGS84 +a=6378137 +f=298.257223563 +pm=0  +no_defs', preserve_units=True)

sites_table = 'ExternalSite'
ts_summ_table = 'TSDataNumericDailySumm'
ts_table = 'TSDataNumericDaily'
dataset_table = 'vDatasetTypeNamesActive'
mtype_table = 'MeasurementType'
sites_cols = ['ExtSiteID', 'ExtSiteName', 'NZTMX', 'NZTMY']

wq_mtypes_table = 'WQMeasurement'
wq_summ_table = 'WQDataSumm'

##########################################
### Functions


def ecan_ts_summ(server, database, features, mtypes, ctypes, data_codes, data_providers):
    """

    """
    ### Get the appropriate dataset/mtype keys
    datasets1 = mssql.rd_sql(server, database, dataset_table, where_col={'Feature': features, 'MeasurementType': mtypes, 'CollectionType': ctypes, 'DataCode': data_codes, 'DataProvider': data_providers})
    mtypes1 = mssql.rd_sql(server, database, mtype_table, ['MeasurementType', 'Units'], where_col={'MeasurementType': mtypes})
    datasets2 = pd.merge(datasets1, mtypes1, on='MeasurementType')

    wq_mtypes = mssql.rd_sql(server, database, wq_mtypes_table, ['MeasurementID', 'Measurement'], where_col={'Measurement': mtypes})
    wq_mtypes.rename(columns={'Measurement': 'MeasurementType'}, inplace=True)

    ### Get the summary data
    summ1 = mssql.rd_sql(server, database, ts_summ_table, ['ExtSiteID', 'DatasetTypeID', 'Min', 'Median', 'Mean', 'Max', 'Count', 'FromDate', 'ToDate'], where_col={'DatasetTypeID': datasets1.DatasetTypeID.tolist()})
    summ2 = pd.merge(summ1, datasets2, on='DatasetTypeID').drop('DatasetTypeID', axis=1)

    wq_summ1 = mssql.rd_sql(server, database, wq_summ_table, ['ExtSiteID', 'MeasurementID', 'Units', 'FromDate', 'ToDate'], where_col={'MeasurementID': wq_mtypes.MeasurementID.tolist(), 'DataType': ['WQData']})
    wq_summ1['CollectionType'] = 'Manual Field'
    wq_summ1['DataCode'] = 'Primary'
    wq_summ1['DataProvider'] = 'ECan'
    wq_summ1['Feature'] = 'Aquifer'
    wq_summ1.loc[wq_summ1.ExtSiteID.str.contains('SQ', case=False), 'Feature'] = 'River'

    wq_summ2 = pd.merge(wq_summ1, wq_mtypes, on='MeasurementID').drop('MeasurementID', axis=1)

    ### Join
    summ3 = pd.concat([summ2, wq_summ2], sort=True)
    summ3['FromDate'] = pd.to_datetime(summ3['FromDate'])
    summ3['ToDate'] = pd.to_datetime(summ3['ToDate'])

    return summ3


def app_ts_summ(server, database, features, mtypes, ctypes, data_codes, data_providers):
    """

    """
    ## Get TS summary
    ecan_summ = ecan_ts_summ(server, database, features, mtypes, ctypes, data_codes, data_providers)

    ## Get site info
    sites = mssql.rd_sql(server, database, sites_table, sites_cols)
    sites['NZTMX'] = sites['NZTMX'].astype(int)
    sites['NZTMY'] = sites['NZTMY'].astype(int)

    # Hover text
    sites.loc[sites.ExtSiteName.isnull(), 'ExtSiteName'] = ''

    sites['hover'] = sites.ExtSiteID + '<br>' + sites.ExtSiteName.str.strip()

    # Convert projections
    xy1 = list(zip(sites['NZTMX'], sites['NZTMY']))
    x, y = list(zip(*[transform(from_crs, to_crs, x, y) for x, y in xy1]))

    sites['lon'] = x
    sites['lat'] = y

    ## Combine with everything
    ts_summ = pd.merge(sites, ecan_summ, on='ExtSiteID')

    return ts_summ


def sel_ts_summ(ts_summ, features, mtypes, ctypes, data_codes, data_providers, start_date, end_date):
    if isinstance(features, str):
        features = [features]
    if isinstance(mtypes, str):
        mtypes = [mtypes]
    if isinstance(ctypes, str):
        ctypes = [ctypes]
    if isinstance(data_codes, str):
        data_codes = [data_codes]
    if isinstance(data_providers, str):
        data_providers = [data_providers]

    date_bool = ((ts_summ.FromDate >= start_date) & (ts_summ.FromDate <= end_date)) | ((ts_summ.ToDate >= start_date) & (ts_summ.ToDate <= end_date)) | ((ts_summ.FromDate <= start_date) & (ts_summ.ToDate >= end_date))
    df = ts_summ[date_bool & ts_summ.Feature.isin(features) & ts_summ.MeasurementType.isin(mtypes) & ts_summ.CollectionType.isin(ctypes) & ts_summ.DataCode.isin(data_codes) & ts_summ.DataProvider.isin(data_providers)].copy()

    df['FromDate'] = df['FromDate'].dt.date.astype(str)
    df['ToDate'] = df['ToDate'].dt.date.astype(str)
    df['Min'] = df['Min'].round(3).astype(str)
    df['Mean'] = df['Mean'].round(3).astype(str)
    df['Max'] = df['Max'].round(3).astype(str)

    return df



















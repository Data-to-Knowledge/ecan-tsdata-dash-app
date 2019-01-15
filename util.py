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

##########################################
### Functions


def rd_ts_summ(server, db, ts_summ_table, dataset_table, mtype_table, sites_table, sites_cols):
    ## Load ts summary data
    ts_summ1 = mssql.rd_sql(server, db, ts_summ_table)
    ts_summ1['FromDate'] = pd.to_datetime(ts_summ1['FromDate'])
    ts_summ1['ToDate'] = pd.to_datetime(ts_summ1['ToDate'])

    ## Load other data
    datasets1 = mssql.rd_sql(server, db, dataset_table)
    mtypes = mssql.rd_sql(server, db, mtype_table)
    datasets = pd.merge(datasets1, mtypes, on='MeasurementType')
    datasets['Dataset Name'] = datasets.Feature + ' - ' + datasets.MeasurementType + ' - ' + datasets.CollectionType + ' - ' + datasets.DataCode + ' - ' + datasets.DataProvider + ' (' + datasets.Units + ')'

    ## Merge the two
    ts_summ2 = pd.merge(datasets, ts_summ1, on='DatasetTypeID')

    ## Get site info
    sites = mssql.rd_sql(server, db, sites_table, sites_cols)
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
    ts_summ = pd.merge(sites, ts_summ2, on='ExtSiteID')

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



















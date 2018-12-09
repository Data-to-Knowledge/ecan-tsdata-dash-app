# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from pdsql import mssql
from pyproj import Proj, transform
import urllib

app = dash.Dash(__name__)
server = app.server

#######################################
### Functions


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
    df['Min'] = df['Min'].round(3)
    df['Mean'] = df['Mean'].round(3)
    df['Max'] = df['Max'].round(3)
    return df


def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


##########################################
### Parameters

server = 'sql2012test01'
db = 'hydro'
sites_table = 'ExternalSite'
ts_summ_table = 'TSDataNumericDailySumm'
ts_table = 'TSDataNumericDaily'
dataset_table = 'vDatasetTypeNamesActive'
mtype_table = 'MeasurementType'
#datasettypes = [4, 5, 15]
#datasettype_names = {4: 'Water Level (m)', 5: 'Flow (m3/s)', 15: 'Precip (mm)'}

sites = mssql.rd_sql(server, db, sites_table)
ts_summ1 = mssql.rd_sql(server, db, ts_summ_table)

ts_summ1['FromDate'] = pd.to_datetime(ts_summ1['FromDate'])
ts_summ1['ToDate'] = pd.to_datetime(ts_summ1['ToDate'])

datasets1 = mssql.rd_sql(server, db, dataset_table)
mtypes = mssql.rd_sql(server, db, mtype_table)
datasets = pd.merge(datasets1, mtypes, on='MeasurementType')
datasets['Dataset Name'] = datasets.Feature + ' - ' + datasets.MeasurementType + ' - ' + datasets.CollectionType + ' - ' + datasets.DataCode + ' - ' + datasets.DataProvider + ' (' + datasets.Units + ')'

ts_summ = pd.merge(datasets, ts_summ1, on='DatasetTypeID')



#ts_summ.replace({'DatasetTypeID': datasettype_names}, inplace=True)
#
#ts_summ.rename(columns={'DatasetTypeID': 'Dataset Name'}, inplace=True)

sites = sites[sites.ExtSiteID.isin(ts_summ.ExtSiteID.unique())].copy()

### Convert projections
from_crs1 = Proj('+proj=tmerc +ellps=GRS80 +a=6378137.0 +f=298.257222101 +towgs84=0,0,0,0,0,0,0 +pm=0  +lon_0=173 +x_0=1600000 +y_0=10000000 +k_0=0.9996 +lat_0=0 +units=m +axis=enu +no_defs', preserve_units=True)
to_crs1 = Proj('+proj=longlat +datum=WGS84 +ellps=WGS84 +a=6378137 +f=298.257223563 +pm=0  +no_defs', preserve_units=True)
xy1 = list(zip(sites['NZTMX'], sites['NZTMY']))
x, y = list(zip(*[transform(from_crs1, to_crs1, x, y) for x, y in xy1]))

sites['lon'] = x
sites['lat'] = y

temp1 = 'River - Flow - Recorder - Primary - ECan (m**3/s)'

table_cols = ['ExtSiteID', 'DatasetTypeID', 'Feature', 'MeasurementType', 'CollectionType', 'DataCode', 'DataProvider', 'Units', 'Min', 'Mean', 'Max', 'Count', 'FromDate', 'ToDate']

### Make hover text

#dict1 = {}
#
#for group, val in ts_summ.groupby('ExtSiteID'):
#    hov1 = [group]
#    for name, t in val.iterrows():
#        hov1.append('{} from {} to {}'.format(t['Dataset Name'], str(t['FromDate'].date()), str(t['ToDate'].date())))
#    hov2 = '<br>'.join(hov1)
#    dict1.update({group: hov2})
#
#names1 = pd.DataFrame.from_dict(dict1, orient='index', columns=['hover'])
#names1.index.name = 'ExtSiteID'
#
#sites = pd.merge(sites, names1.reset_index(), on='ExtSiteID')



sites.loc[sites.ExtSiteName.isnull(), 'ExtSiteName'] = ''

sites['hover'] = sites.ExtSiteID + '<br>' + sites.ExtSiteName.str.strip()

lat = -43.45
lon = 171.9

### prepare summaries and initial states
min_year = ts_summ.FromDate.min().year
max_year = ts_summ.ToDate.max().year
max_date = ts_summ.ToDate.max()

start_date = max_date - pd.DateOffset(years=1)

init_summ = sel_ts_summ(ts_summ, 'River', 'Flow', 'Recorder', 'Primary', 'ECan', str(start_date.date()), str(max_date.date()))

#years = np.arange(min_year2 + 2, max_year + 1)
#years_label = {str(min_year2): 'All Years'}
#years_label.update({str(year): str(year) for year in years[::2]})
#features = 'River'
#mtypes = 'Abstraction'
#ctypes = 'Recorder'
#data_codes = 'RAW'
#data_providers = 'ECan'
#start_date = '2017-12-06'
#end_date = '2018-12-06'


#init_summ = sel_ts_summ(ts_summ, init_years)
#init_sites = sites[sites.ExtSiteID.isin(init_summ.ExtSiteID.unique())].copy()

#col1 = ["#2a4858", "#265465", "#1e6172", "#106e7c", "#007b84",
#	"#00898a", "#00968e", "#19a390", "#31b08f", "#4abd8c", "#64c988",
#	"#80d482", "#9cdf7c", "#bae976", "#d9f271", "#fafa6e"]

mapbox_access_token = "pk.eyJ1IjoibXVsbGVua2FtcDEiLCJhIjoiY2pudXE0bXlmMDc3cTNxbnZ0em4xN2M1ZCJ9.sIOtya_qe9RwkYXj5Du1yg"

###############################################
### App layout

map_layout = dict(mapbox = dict(layers = [], accesstoken = mapbox_access_token, style = 'outdoors', center=dict(lat=-43.45, lon=171.9), zoom=7), margin = dict(r=0, l=0, t=0, b=0), autosize=True, hovermode='closest', height=600)


app.layout = html.Div(children=[

    html.Div([
        html.P(children='Filter sites by:'),
		html.Label('Feature'),
		dcc.Dropdown(options=[{'label': d, 'value': d} for d in np.sort(ts_summ.Feature.unique())], multi=True, value='River', id='features'),
        html.Label('Measurement Type'),
		dcc.Dropdown(options=[{'label': d, 'value': d} for d in np.sort(ts_summ.MeasurementType.unique())], multi=True, value='Flow', id='mtypes'),
        html.Label('CollectionType'),
		dcc.Dropdown(options=[{'label': d, 'value': d} for d in np.sort(ts_summ.CollectionType.unique())], multi=True, value='Recorder', id='ctypes'),
        html.Label('Data Code'),
		dcc.Dropdown(options=[{'label': d, 'value': d} for d in np.sort(ts_summ.DataCode.unique())], multi=True, value='Primary', id='data_codes'),
        html.Label('Data Provider'),
		dcc.Dropdown(options=[{'label': d, 'value': d} for d in np.sort(ts_summ.DataProvider.unique())], multi=True, value='ECan', id='data_providers'),
        html.Label('Date Range'),
		dcc.DatePickerRange(
            end_date=max_date,
            display_format='DD/MM/YYYY',
            start_date=start_date,
            id='date_sel'
#               start_date_placeholder_text='DD/MM/YYYY'
            )
		], className='two columns', style={'margin': 20}),

	html.Div([
		dcc.Graph(id = 'site-map', style={'height': 700}),

        html.A(
            'Download Dataset Summary Data',
            id='download-summ',
            download="dataset_summary.csv",
            href="",
            target="_blank",
            style={'margin': 50}),

        dash_table.DataTable(
            id='summ_table',
            columns=[{"name": i, "id": i, 'deletable': True} for i in table_cols],
            data=init_summ[table_cols].astype(str).to_dict('rows'),
            sorting=True,
            sorting_type="multi",
            filtering=True
#            column_widths=[20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
            )

	], className='five columns', style={'margin': 20}),

    html.Div([

		html.P('Select Dataset:', style={'display': 'inline-block'}),
		dcc.Dropdown(options=[], value='River - Flow - Recorder - Primary - ECan (m**3/s)', id='sel_dataset'),
		dcc.Graph(
			id = 'selected-data',
			figure = dict(
				data = [dict(x=0, y=0)],
				layout = dict(
					paper_bgcolor = '#F4F4F8',
					plot_bgcolor = '#F4F4F8', height=600
				)
			),
			# animate = True
		),
        html.A(
            'Download Time Series Data',
            id='download-tsdata',
            download="tsdata.csv",
            href="",
            target="_blank",
            style={'margin': 50})
	], className='five columns', style={'margin': 20, 'height': 900}),
    html.Div(id='summ_data', style={'display': 'none'})
], style={'margin':0})

app.css.append_css({'external_url': 'https://codepen.io/plotly/pen/EQZeaW.css'})

########################################
### Callbacks

@app.callback(
    Output('summ_data', 'children'), [Input('features', 'value'), Input('mtypes', 'value'), Input('ctypes', 'value'), Input('data_codes', 'value'), Input('data_providers', 'value'), Input('date_sel', 'start_date'), Input('date_sel', 'end_date')])
def calc_summ(features, mtypes, ctypes, data_codes, data_providers, start_date, end_date):
    new_summ = sel_ts_summ(ts_summ, features, mtypes, ctypes, data_codes, data_providers, start_date, end_date).copy()
    print(features, mtypes, ctypes, data_codes, data_providers, start_date, end_date)
    return new_summ.to_json(date_format='iso', orient='split')


@app.callback(
		Output('site-map', 'figure'),
		[Input('summ_data', 'children')],
		[State('site-map', 'relayoutData')])
def display_map(summ_data, relay):
    new_summ = pd.read_json(summ_data, orient='split')
    new_sites = sites[sites.ExtSiteID.isin(new_summ.ExtSiteID.astype(str).unique())].copy()
#    print(new_sites)
#    print(new_summ.ExtSiteID.unique())

    data = [dict(
		lat = new_sites['lat'],
		lon = new_sites['lon'],
		text = new_sites['hover'],
		type = 'scattermapbox',
		hoverinfo = 'text',
		marker = dict(size=8, color='black', opacity=1)
	)]

    if relay is not None:
        if 'mapbox.center' in relay:
            print(relay)
            lat = float(relay['mapbox.center']['lat'])
            lon = float(relay['mapbox.center']['lon'])
            zoom = float(relay['mapbox.zoom'])
            map_layout['mapbox']['center']['lon'] = lon
            map_layout['mapbox']['center']['lat'] = lat
            map_layout['mapbox']['zoom'] = zoom

    fig = dict(data=data, layout=map_layout, config={"displaylogo": False})
    return fig


@app.callback(
    Output('sel_dataset', 'options'),
    [Input('summ_data', 'children')])
def dataset_options(summ_data):
    new_summ = pd.read_json(summ_data, orient='split')

    new_summ2 = new_summ[['DatasetTypeID', 'Dataset Name']].drop_duplicates().copy()
    new_summ2.columns = ['value', 'label']
    options1 = new_summ2.to_dict('records')

    return options1


@app.callback(
	Output('selected-data', 'figure'),
	[Input('site-map', 'selectedData'), Input('site-map', 'clickData'),
	Input('sel_dataset', 'value')],
	[State('date_sel', 'start_date'), State('date_sel', 'end_date')])
def display_data(selectedData, clickData, sel_dataset, start_date, end_date):

    print(sel_dataset)

    sites1 = None

    if selectedData is not None:
        sites1 = [s['text'].split('<br>')[0] for s in selectedData['points']]
        print(sites1)
    elif clickData is not None:
        sites1 = [clickData['points'][0]['text'].split('<br>')[0]]
        print(sites1)
    if sites1 is None:
        return dict(
			data = [dict(x=0, y=0)],
			layout = dict(
				title='Click-drag on the map to select sites',
				paper_bgcolor = '#F4F4F8',
				plot_bgcolor = '#F4F4F8'
			)
		)

    ts1 = mssql.rd_sql(server, db, ts_table, ['ExtSiteID', 'DatasetTypeID', 'DateTime', 'Value'], where_col={'DatasetTypeID': [sel_dataset], 'ExtSiteID': sites1}, from_date=start_date, to_date=end_date, date_col='DateTime')

#    n_tiles = int(np.ceil(len(sites1)/len(col1)))
#    col2 = np.tile(col1, n_tiles)[:len(sites1)].tolist()
#    col3 = dict(zip(sites1, col2))

    data = []
    for s in sites1:
        dataset1 = ts1[ts1.ExtSiteID == s]
        set1 = go.Scattergl(
                x=dataset1.DateTime,
                y=dataset1.Value,
                name=s,
#                line={'color': col3[s]},
                opacity=0.8)
        data.append(set1)

    layout = dict(
            title = 'Time series data',
            paper_bgcolor = '#F4F4F8',
			plot_bgcolor = '#F4F4F8',
            xaxis = dict(
                    range = [start_date, end_date]))

    fig = dict(data=data, layout=layout, config={"displaylogo": False})
    return fig


@app.callback(
    Output('summ_table', 'data'),
    [Input('summ_data', 'children')])
def plot_table(summ_data):
    new_summ = pd.read_json(summ_data, orient='split')[table_cols]
    return new_summ.astype(str).to_dict("rows")


@app.callback(
    Output('download-tsdata', 'href'),
    [Input('site-map', 'selectedData'), Input('site-map', 'clickData'),
	Input('sel_dataset', 'value')],
	[State('date_sel', 'start_date'), State('date_sel', 'end_date')])
def download_tsdata(selectedData, clickData, sel_dataset, start_date, end_date):
    sites1 = None

    if selectedData is not None:
        sites1 = [s['text'].split('<br>')[0] for s in selectedData['points']]
        print(sites1)
    elif clickData is not None:
        sites1 = [clickData['points'][0]['text'].split('<br>')[0]]
        print(sites1)

    ts1 = mssql.rd_sql(server, db, ts_table, ['ExtSiteID', 'DatasetTypeID', 'DateTime', 'Value'], where_col={'DatasetTypeID': [sel_dataset], 'ExtSiteID': sites1}, from_date=start_date, to_date=end_date, date_col='DateTime')
#    ts1.replace({'DatasetTypeID': datasettype_names}, inplace=True)
#    ts1.rename(columns={'DatasetTypeID': 'DatasetType'}, inplace=True)
    csv_string = ts1.to_csv(index=False, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string


@app.callback(
    Output('download-summ', 'href'),
    [Input('summ_data', 'children')])
def download_summ(summ_data):
    new_summ = pd.read_json(summ_data, orient='split')[table_cols]

    csv_string = new_summ.to_csv(index=False, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string


if __name__ == '__main__':
	app.run_server(debug=True, host='0.0.0.0')


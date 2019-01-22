# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import urllib
from util import app_ts_summ, sel_ts_summ, ecan_ts_data

pd.options.display.max_columns = 10


app = dash.Dash(__name__)
server = app.server

##########################################
### Parameters

server = 'sql2012test01'
db = 'hydro'
sites_table = 'ExternalSite'
ts_summ_table = 'TSDataNumericDailySumm'
ts_table = 'TSDataNumericDaily'
dataset_table = 'vDatasetTypeNamesActive'
mtype_table = 'MeasurementType'
sites_cols = ['ExtSiteID', 'ExtSiteName', 'NZTMX', 'NZTMY']
features = ['River', 'Aquifer', 'Atmosphere']
mtypes = ['Abstraction', 'Water Level', 'Flow', 'Temperature', 'Precipitation', 'Nitrate Nitrogen', 'Nitrate-N + Nitrite-N', 'Ammoniacal Nitrogen', 'Total Nitrogen', 'Dissolved Oxygen', 'Dissolved Oxygen % Saturation', 'Turbidity', 'Dissolved Reactive Phosphorus', 'Total Phosphorus', 'E. coli', 'Total Coliforms', 'Water Temperature (Field)', 'Conductivity (Field)', 'Conductivity', 'Total Suspended Solids', 'Chlorophyll a (planktonic)']
data_codes = ['RAW', 'Primary']
ctypes = ['Recorder', 'Manual Field']
data_providers = ['ECan', 'NIWA', 'Aqualinc', 'Boraman', 'ECS']

#include_datasets = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,424,1520,1521,1636,
#                1637,1638,1886,1887,1943,4502,4503,4514,4514,4520,4521,4557,4558,
#                4559,4563,4564,4565,4569,4570,4571]
#datasettype_names = {4: 'Water Level (m)', 5: 'Flow (m3/s)', 15: 'Precip (mm)'}

ts_plot_height = 600
map_height = 700

init_dataset = 'River - Flow - Recorder - Primary - ECan (m**3/s)'

table_cols = ['ExtSiteID', 'ExtSiteName', 'NZTMX', 'NZTMY', 'Feature', 'MeasurementType', 'CollectionType', 'DataCode', 'DataProvider', 'Units', 'Min', 'Median', 'Mean', 'Max', 'Count', 'FromDate', 'ToDate']

lat1 = -43.45
lon1 = 171.9
zoom1 = 7

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

mapbox_access_token = "pk.eyJ1IjoibXVsbGVua2FtcDEiLCJhIjoiY2pudXE0bXlmMDc3cTNxbnZ0em4xN2M1ZCJ9.sIOtya_qe9RwkYXj5Du1yg"

###############################################
### App layout

map_layout = dict(mapbox = dict(layers = [], accesstoken = mapbox_access_token, style = 'outdoors', center=dict(lat=lat1, lon=lon1), zoom=zoom1), margin = dict(r=0, l=0, t=0, b=0), autosize=True, hovermode='closest', height=map_height)

def serve_layout():

    ts_summ = app_ts_summ(server, db, features, mtypes, ctypes, data_codes, data_providers)

    ### prepare summaries and initial states
    max_date = pd.Timestamp.now()
    start_date = max_date - pd.DateOffset(years=1)

    init_summ = sel_ts_summ(ts_summ, 'River', 'Flow', 'Recorder', 'Primary', 'ECan', str(start_date.date()), str(max_date.date()))

    new_sites = init_summ.drop_duplicates('ExtSiteID')

    layout = html.Div(children=[
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
            end_date=str(max_date.date()),
            display_format='DD/MM/YYYY',
            start_date=str(start_date.date()),
            id='date_sel'
#               start_date_placeholder_text='DD/MM/YYYY'
            ),
        html.Label('Site IDs'),
		dcc.Dropdown(options=[{'label': d, 'value': d} for d in np.sort(init_summ.ExtSiteID.unique())], multi=True, id='sites'),
        html.Label('Water quality below detection limit method'),
        dcc.RadioItems(
            options=[
                {'label': 'Half dtl', 'value': 'half'},
                {'label': 'Trend analysis method', 'value': 'trend'}
            ],
            value='half',
            id='dtl')
		],
    className='two columns', style={'margin': 20}),

	html.Div([
        html.P('Click on a site or "box select" multiple sites:', style={'display': 'inline-block'}),
		dcc.Graph(
                id = 'site-map',
                style={'height': map_height},
                figure=dict(
                        data = [dict(lat = new_sites['lat'],
                                     lon = new_sites['lon'],
                                     text = new_sites['hover'],
                                     type = 'scattermapbox',
                                     hoverinfo = 'text',
                                     marker = dict(
                                             size=8,
                                             color='black',
                                             opacity=1
                                             )
                                     )
                                ],
                        layout=map_layout),
                config={"displaylogo": False}),

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
            style_cell={
                'minWidth': '80px', 'maxWidth': '200px',
                'whiteSpace': 'normal'
            },
#            column_widths=[20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
            )

	], className='four columns', style={'margin': 20}),

    html.Div([

		html.P('Select Dataset for time series plot:', style={'display': 'inline-block'}),
		dcc.Dropdown(options=[{'value:': 5, 'label': init_dataset}], value=5, id='sel_dataset'),
		dcc.Graph(
			id = 'selected-data',
			figure = dict(
				data = [dict(x=0, y=0)],
                layout = dict(
                        paper_bgcolor = '#F4F4F8',
                        plot_bgcolor = '#F4F4F8',
                        height = ts_plot_height
                        )
                ),
			config={"displaylogo": False}
            ),
        html.A(
            'Download Time Series Data',
            id='download-tsdata',
            download="tsdata.csv",
            href="",
            target="_blank",
            style={'margin': 50})
	], className='six columns', style={'margin': 10, 'height': 900}),
    html.Div(id='summ_data', style={'display': 'none'}),
    html.Div(id='summ_data_all', style={'display': 'none'}, children=ts_summ.to_json(date_format='iso', orient='split')),
    dcc.Graph(id='map-layout', style={'display': 'none'}, figure=dict(data=[], layout=map_layout))
], style={'margin':0})

    return layout


app.layout = serve_layout

app.css.append_css({'external_url': 'https://codepen.io/plotly/pen/EQZeaW.css'})

########################################
### Callbacks


@app.callback(
    Output('summ_data', 'children'), [Input('features', 'value'), Input('mtypes', 'value'), Input('ctypes', 'value'), Input('data_codes', 'value'), Input('data_providers', 'value'), Input('date_sel', 'start_date'), Input('date_sel', 'end_date')], [State('summ_data_all', 'children')])
def calc_summ(features, mtypes, ctypes, data_codes, data_providers, start_date, end_date, summ_data_all):
    ts_summ = pd.read_json(summ_data_all, orient='split')
    ts_summ['FromDate'] = pd.to_datetime(ts_summ['FromDate'])
    ts_summ['ToDate'] = pd.to_datetime(ts_summ['ToDate'])
    new_summ = sel_ts_summ(ts_summ, features, mtypes, ctypes, data_codes, data_providers, start_date, end_date).copy()
    print(features, mtypes, ctypes, data_codes, data_providers, start_date, end_date)
    return new_summ.to_json(date_format='iso', orient='split')


@app.callback(
		Output('map-layout', 'figure'),
		[Input('site-map', 'relayoutData')],
		[State('map-layout', 'figure')])
def update_map_layout(relay, figure):
    if relay is not None:
#        print(figure['layout'])
        if 'mapbox.center' in relay:
#            print(relay)
            lat = float(relay['mapbox.center']['lat'])
            lon = float(relay['mapbox.center']['lon'])
            zoom = float(relay['mapbox.zoom'])
            new_layout = dict(mapbox = dict(layers = [], accesstoken = mapbox_access_token, style = 'outdoors', center=dict(lat=lat, lon=lon), zoom=zoom), margin = dict(r=0, l=0, t=0, b=0), autosize=True, hovermode='closest', height=map_height)
        else:
            new_layout = figure['layout'].copy()
    else:
        new_layout = figure['layout'].copy()

    return dict(data=[], layout=new_layout)


@app.callback(
		Output('site-map', 'figure'),
		[Input('summ_data', 'children')],
		[State('map-layout', 'figure')])
def display_map(summ_data, figure):
    new_summ = pd.read_json(summ_data, orient='split')
    new_sites = new_summ.drop_duplicates('ExtSiteID')
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

    fig = dict(data=data, layout=figure['layout'])
    return fig


@app.callback(
    Output('sel_dataset', 'options'),
    [Input('summ_data', 'children')])
def update_dataset_options(summ_data):
    new_summ = pd.read_json(summ_data, orient='split')

    new_summ2 = new_summ[['DatasetTypeID', 'Dataset Name']].drop_duplicates().copy()
    new_summ2.columns = ['value', 'label']
    options1 = new_summ2.to_dict('records')
    print(options1)

    return options1


@app.callback(
        Output('sites', 'options'),
        [Input('summ_data', 'children')])
def update_sites_options(summ_data):
    new_summ = pd.read_json(summ_data, orient='split')
    sites = np.sort(new_summ.ExtSiteID.unique())
    options1 = [{'label': i, 'value': i} for i in sites]
    return options1


@app.callback(
        Output('sites', 'value'),
        [Input('site-map', 'selectedData'), Input('site-map', 'clickData')])
def update_sites_values(selectedData, clickData):
    if selectedData is not None:
        sites1 = [s['text'].split('<br>')[0] for s in selectedData['points']]
        print(sites1)
    elif clickData is not None:
        sites1 = [clickData['points'][0]['text'].split('<br>')[0]]
        print(sites1)
    else:
        sites1 = []
    return sites1[:20]


@app.callback(
	Output('selected-data', 'figure'),
	[Input('sites', 'value'), Input('sel_dataset', 'value'), Input('site-map', 'selectedData'), Input('site-map', 'clickData'), Input('date_sel', 'start_date'), Input('date_sel', 'end_date'), Input('summ_data', 'children'), Input('dtl', 'value')])
def display_data(sites, sel_dataset, selected, clicked, start_date, end_date, summ_data, dtl):

    base_dict = dict(
			data = [dict(x=0, y=0)],
			layout = dict(
				title='Click-drag on the map to select sites',
				paper_bgcolor = '#F4F4F8',
				plot_bgcolor = '#F4F4F8'
                )
            )

    if not sites:
        return base_dict

    print(sel_dataset)

    new_summ = pd.read_json(summ_data, orient='split')
    sites1 = [str(s) for s in sites]

    site_ts_summ = new_summ[new_summ.ExtSiteID.isin(sites1)].copy()
    if site_ts_summ.empty:
        return base_dict

    ts1 = ecan_ts_data(server, db, site_ts_summ, start_date, end_date, dtl)
    grp1 = ts1.groupby('ExtSiteID')

    data = []
    for s, group in grp1:
        set1 = go.Scattergl(
                x=group.DateTime,
                y=group.Value,
                name=s,
#                line={'color': col3[s]},
                opacity=0.8)
        data.append(set1)

    layout = dict(title = 'Time series data', paper_bgcolor = '#F4F4F8', plot_bgcolor = '#F4F4F8', xaxis = dict(range = [start_date, end_date]), showlegend=True, height=ts_plot_height)

    fig = dict(data=data, layout=layout)
    return fig


@app.callback(
    Output('summ_table', 'data'),
    [Input('summ_data', 'children'), Input('sites', 'value'), Input('site-map', 'selectedData'), Input('site-map', 'clickData')])
def plot_table(summ_data, sites, selectedData, clickData):
    new_summ = pd.read_json(summ_data, orient='split')[table_cols]

    if sites:
        new_summ = new_summ.loc[new_summ.ExtSiteID.isin(sites)]
    return new_summ.to_dict("rows")


@app.callback(
    Output('download-tsdata', 'href'),
    [Input('sites', 'value'), Input('site-map', 'selectedData'), Input('site-map', 'clickData'),	Input('sel_dataset', 'value')],
	[State('date_sel', 'start_date'), State('date_sel', 'end_date'), State('summ_data', 'children')])
def download_tsdata(sites, selectedData, clickData, sel_dataset, start_date, end_date, summ_data):

    if not sites:
        return ''

    new_summ = pd.read_json(summ_data, orient='split')
    sites1 = [str(s) for s in sites]

    site_ts_summ = new_summ[new_summ.ExtSiteID.isin(sites1)].copy()

    ts1 = ecan_ts_data(server, db, site_ts_summ, start_date, end_date, 'half')
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
	app.run_server(debug=True, host='0.0.0.0', port=8050)


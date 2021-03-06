'''

Storage Model - Diagnostics Dashboard
Tony Du



v1 7/30/2020


'''


import pathlib
import os
import glob

import base64
import io 
import datetime

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


lst_vars = ['Price', 'PV avail', 'PV gen', 'PV gen to grid', 'PV gen to charge', 'Grid gen to charge', 'Storage charge', 'Storage discharge', 'Storage SOC']
dict_units = {'Price':'$', 'PV avail':'Percentage (out of 1)', 'PV gen':'MWH', 'PV gen to grid':'MWH', 'PV gen to charge':'MWH', 'Grid gen to charge':'MWH', 'Storage charge':'MWH', 'Storage discharge':'MWH', 'Storage SOC':'MWH'}
inputfolder = os.getcwd() + '\\input\\' 


inputfile = inputfolder + [i for i in os.listdir(inputfolder) if os.path.isfile(os.path.join(inputfolder, i)) and '.xls' in i][0]
df_global = pd.read_excel(inputfile, header=None)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server  # for Heroku deployment


NAVBAR = dbc.Navbar(
    [
        html.Img(src=app.get_asset_url('branding.png'), height='40px'),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink('Storage Model Diagnostics', href='/dashboard', id='dashboard-link', active=True))
            ], navbar=True, style={'marginLeft': '20px'}
        )

    ],
    color='dark',
    dark=True,
)

INPUTS = dbc.Jumbotron(
    [
        dbc.Container(
            [
                html.H4(children='Global Inputs', className='display-5', style = {'fontSize': 36}),
                html.Hr(className='my-2'),
                html.Label('Import Results', className='lead'),
                html.Div(
                    id='input-div',
                    children=[
                        dcc.Dropdown(
                            id='input-drop', clearable=False
                        )
                    ]    
                ),
                html.Div(id='store-df', style={'display' : 'none'}),
                html.Div(style = {'marginBottom':25}),
                html.Label('Select Start Time', className='lead'),
                dbc.Input(
                    id ='input-start', type='datetime-local', style={'marginBottom': 25}, value='2017-12-01T00:00'
                ),
                html.Label('Select End Time', className='lead'),
                dbc.Input(
                    id ='input-end', type='datetime-local', style={'marginBottom': 25}, value='2017-12-07T23:00'
                ),
                dbc.Button(id='submit-btn', color='primary', children='Update time period and refresh graphs', size='md')
            ], fluid = True
        )
    ], style={'height':'100%'}
)

CONTENT = html.Div(
    [
        dbc.CardGroup(
            [
                dbc.Card(
                    [
                        html.H5('PV Power (MW)'),
                        html.P(id='pv-power-value')
                    ], body=True
                ),
                dbc.Card(
                    [
                        html.H5('Storage Power (MW)'),
                        html.P(id='storage-power-value')
                    ], body=True
                ),
                dbc.Card(
                    [
                        html.H5('Storage Energy (MWH)'),
                        html.P(id='storage-energy-value')
                    ], body=True
                ),
                dbc.Card(
                    [
                        html.H5('Efficiency'),
                        html.P(id='efficiency-value')
                    ], body=True
                ),
                dbc.Card(
                    [
                        html.H5('Duration (Hours)'),
                        html.P(id='duration-value')
                    ], body=True
                ),
            ], style={'text-align': 'Center'}
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H3('Timeseries Graph', style={'marginTop':25, 'marginBottom':10})
                    ]
                )

            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label('Select Primary Y-Axis Variable(s)'),
                        dcc.Dropdown(
                            id='primaryaxis-drop', multi=True,
                            value=['Price'],
                            options = [{'label':i, 'value':i} for i in lst_vars]
                        ),
                    ], width=4
                ),
                dbc.Col(
                    [
                        html.Label('Select Secondary Y-Axis Variable(s) - Optional '),
                        dcc.Dropdown(
                            id='secondaryaxis-drop', multi=True,
                            value=['PV gen to grid'],
                            options = [{'label':i, 'value':i} for i in lst_vars]
                        ),
                    ], width=4
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [ 
                        dcc.Loading(
                            [
                                dcc.Graph(id='graph-timeseries')
                            ]
                        )

                    ]
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H3('Battery and PV Flow'),
                        dcc.Loading(
                            [
                                dcc.Graph(id='graph-batteryflow')
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)


BODY = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(INPUTS, width=3),
                dbc.Col(CONTENT, width=9),
            ],
            style={'marginTop': 30},
        )
    ],
    className='mt-12', fluid = True
)


@app.callback(
    Output('input-drop', 'options'),
    [Input('input-div', 'n_clicks')]
)

def update_dropdown_options(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    options = [i for i in os.listdir(inputfolder) if os.path.isfile(os.path.join(inputfolder, i)) and '.xls' in i]
    return [{'label':i, 'value':i} for i in options]


@app.callback(
    Output('store-df', 'children'),
    [Input('input-drop', 'value')]
)

def store_jsondf(filename):
    if filename is None:
        raise PreventUpdate

    df = pd.read_excel(inputfolder + filename, header=None)
    return df.to_json(date_format='iso', orient='split')

@app.callback(
    Output('graph-timeseries', 'figure'),
    [Input('submit-btn', 'n_clicks'),
    Input('primaryaxis-drop', 'value'),
    Input('secondaryaxis-drop', 'value'),
    Input('store-df', 'children')],
    [State('input-start', 'value'),
    State('input-end', 'value')])

def update_content(n_clicks,  primaryvars, secondaryvars, json_df, starttime, endtime):
    if json_df is None:
        raise PreventUpdate

    df = pd.read_json(json_df, orient='split')
    
    #Select data and generate timeseries graph
    df.columns = df.iloc[4]
    df_data = df.iloc[5:].reset_index()

    print('convert to dt')
    df_data['Time'] = pd.to_datetime(df_data['Time'])

    print('filter on dt')
    df_graph = df_data[(df_data['Time'] >= starttime) & (df_data['Time'] <= endtime)]

    print('make graphs')
    if len(secondaryvars) != 0:
        fig = make_subplots(specs=[[{'secondary_y' : True}]])

        for var in primaryvars:
            fig.add_trace(go.Scatter(x=df_graph['Time'], y=df_graph[var], name=var), secondary_y=False)

        for var in secondaryvars:
            fig.add_trace(go.Scatter(x=df_graph['Time'], y=df_graph[var], name=var), secondary_y=True)
        
        fig.update_yaxes(title_text=dict_units.get(primaryvars[0]), secondary_y=False)
        fig.update_yaxes(title_text=dict_units.get(secondaryvars[0]), secondary_y=True)

    else:
        fig = make_subplots()

        for var in primaryvars:
            fig.add_trace(go.Scatter(x=df_graph['Time'], y=df_graph[var], name=var), secondary_y=False)

        fig.update_yaxes(title_text=dict_units.get(primaryvars[0]), secondary_y=False)    



    return fig

@app.callback(
    [Output('pv-power-value', 'children'),
    Output('storage-power-value', 'children'),
    Output('storage-energy-value', 'children'),
    Output('efficiency-value', 'children'),
    Output('duration-value', 'children')],
    [Input('store-df', 'children')])

def update_modelinfo(json_df):
    #Read Dataframe
    if json_df is None:
        raise PreventUpdate
    df = pd.read_json(json_df, orient='split')


    #Update model info headers
    pv_power = '{:.2f}'.format(df.iloc[0,1])
    storage_power = '{:.2f}'.format(df.iloc[1,1])
    storage_energy = '{:.2f}'.format(df.iloc[2,1])
    efficiency = '{0:.0%}'.format(df.iloc[1,4])
    duration = df.iloc[2,4]


    return pv_power, storage_power, storage_energy, efficiency, duration 

@app.callback(
    Output('graph-batteryflow', 'figure'),
    [Input('submit-btn','n_clicks')],
    [State('store-df', 'children'),
    State('input-start', 'value'),
    State('input-end', 'value')])

def update_batteryflow(n_clicks, json_df, starttime, endtime):
    if json_df is None:
        raise PreventUpdate

    df = pd.read_json(json_df, orient='split')

    #Select data and generate timeseries graph
    
    df.columns = df.iloc[4]
    df_data = df.iloc[5:].reset_index()


    df_data['Time'] = pd.to_datetime(df_data['Time'])
    df_data['Time'] = df_data['Time'].dt.round('H')



    df_graph = df_data[(df_data['Time'] >= starttime) & (df_data['Time'] <= endtime)]
    df_graph.loc[:,'Time'] = df_graph.loc[:,'Time'].apply(str).apply(lambda x: x[0:16])


    df_SOC = pd.DataFrame()
    df_SOC['Time'] = df_graph['Time']
    df_SOC['Category'] = 'Storage SOC'
    df_SOC['Value'] = df_graph['Storage SOC']
   


    df_Charge = pd.DataFrame()
    df_Charge['Time'] = df_graph['Time']
    df_Charge['Category'] = 'Storage Charge'
    df_Charge['Value'] = df_graph['Storage charge']
  

    df_Discharge = pd.DataFrame()
    df_Discharge['Time'] = df_graph['Time']
    df_Discharge['Category'] = 'Storage Discharge'
    df_Discharge['Value'] = -df_graph['Storage discharge']
   


    df_PV = pd.DataFrame()
    df_PV['Time'] = df_graph['Time']
    df_PV['Category'] = 'PV Generation'
    df_PV['Value'] = df_graph['PV gen']



    df_PVtoBattery = pd.DataFrame()
    df_PVtoBattery['Time'] = df_graph['Time']
    df_PVtoBattery['Category'] = 'PV to battery'
    df_PVtoBattery['Value'] = df_graph['PV gen to charge']
   


    df_PVtoGrid = pd.DataFrame()
    df_PVtoGrid['Time'] = df_graph['Time']
    df_PVtoGrid['Category'] = 'PV to grid'
    df_PVtoGrid['Value'] = df_graph['PV gen to grid']


    df_out = pd.concat([df_SOC, df_Charge, df_Discharge, df_PV, df_PVtoBattery, df_PVtoGrid], ignore_index=True)


    fig = px.bar(df_out, x='Category', y='Value', animation_frame='Time', range_y=[-150,550],
        color='Category', color_discrete_sequence=['#636EFA', '#00CC96', '#EF553B', '#FECB52', '#00CC96', '#EF553B'])

    fig.update_layout(showlegend=False)

    return fig

app.title = 'Storage Diagnostics'

app.layout = html.Div(id='page-content', children=[NAVBAR, BODY]) 
app.enable_dev_tools(debug=True, dev_tools_props_check=False)

if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port='8050', debug=True, dev_tools_ui=True)
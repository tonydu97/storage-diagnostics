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




app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server  # for Heroku deployment


NAVBAR = dbc.Navbar(
    [
        html.Img(src=app.get_asset_url('branding.png'), height='40px'),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink('DPT Dashboard', href='/dashboard', id='dashboard-link', active=True)),
                dbc.NavItem(dbc.NavLink('Diagnostics Library - Generate XLSX', id='download-link', href='/download'))
            ], navbar=True, style={'marginLeft': '20px'}
        )

    ],
    color='dark',
    dark=True,
)

INPUTS = dbc.Jumbotron(
    [
        dcc.Loading(
            id = 'loading-inputs',
            children = [
                html.Div(id='store-df', style={'display' : 'none'}),
                dbc.Container(
                    [
                        html.H4(children='Inputs', className='display-5', style = {'fontSize': 36}),
                        html.Hr(className='my-2'),
                        html.Label('Import Results', className='lead'),
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select Files')
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            },
                        ),
                        html.Div(id='output-data-upload'),
                        html.Div(style = {'marginBottom':25}),
                        html.Label('Select Start Time', className='lead'),
                        dbc.Input(
                            id ='input-hours', type='datetime-local', style={'marginBottom': 25}
                        ),
                        html.Label('Select End Time', className='lead'),
                        dbc.Input(
                            id ='input-hours', type='datetime-local', style={'marginBottom': 25}
                        ),
                    ], fluid = True
                )
            ]

        )
    ], style={'height':'100%'}
)

CONTENT = html.Div(
    [
        dbc.Card(id='page-content', style={'height':'720px'})
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

DOWNLOAD = dbc.Container(
    [
        dbc.Jumbotron(
            [
                html.H2('Select Input Folder and Diagnostic'),
                html.Div(style = {'marginBottom':'10px'}),
                html.Label('Raw Results Folder'),
                dcc.Dropdown(id='dl-case-dropdown', clearable=False, style = {'marginBottom': '20px'}),
                html.Label('Diagnostic to Generate'),
                dcc.Dropdown(id='dl-diagnostic-dropdown', clearable=False, style = {'marginBottom': '20px'}),
                html.Label('Output Directory'),
                html.Div(style = {'marginBottom':'10px'}),
                dcc.Input(id='dl-output-textbox', size = '125'),
                html.Hr(),
                html.H2('Diagnostic-specific Inputs'),
                dcc.Loading(html.Div(id='dl-diagnostic-inputs'))
            ], style={'marginTop': 30}
        )
    ]
)

def parse_dataframe(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div(['There was an error processing this file.'])

    return df.to_json(date_format='iso', orient='split')

@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(contents, filename):
    if contents is not None:
        return parse_dataframe(contents, filename)




@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname in ['/', '/dashboard']:
        return [NAVBAR, BODY]
    elif pathname == '/download':
        return [NAVBAR, DOWNLOAD]
    return dbc.Jumbotron(
        [
            html.H1('404: Not found', className='text-danger'),
            html.Hr(),
            html.P(f'The pathname {pathname} is invalid'),
        ]
    )

@app.callback(
    [Output('dashboard-link', 'active'),
    Output('download-link', 'active')],
    [Input('url', 'pathname')]
)
def update_active_link(pathname):
    if pathname in ['/', '/dashboard']:
        return True, False
    elif pathname == '/download':
        return False, True
    return False, False


app.title = 'Storage Diagnostics'
def serve_layout():
    return html.Div(
        [
            dcc.Location(id='url'),
            html.Div(id='page-content') 
        ]
    )

app.layout = serve_layout
app.enable_dev_tools(debug=True, dev_tools_props_check=False)

if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port='8050', debug=True, dev_tools_ui=True)
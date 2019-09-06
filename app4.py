#TEST for layout of loading screen

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_table
from dash.exceptions import PreventUpdate
from os import listdir                      #for getting directories
from os.path import isfile, isdir,join      #for getting directories
import subprocess
import base64                               #for decoding upload content
import io                                   #for decoding upload content
import pandas as pd                         #for dash table
import json                                 #for getting and saving report images list
from os import getcwd
import time                                 #measure time for loading df table
from flask_caching import Cache             #for cache of .targets or .scores

PAGE_SIZE = 10                     #number of entries in each page of the table in view report

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True       #necessary if update element in a callback generated in another callback
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

CACHE_CONFIG = {
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': ('Cache')#os.environ.get('REDIS_URL', 'localhost:6379')
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)

app.layout = html.Div([
    html.H1('CRISPRitz Web Application'),
    html.Div(children='''
        CRISPRitz is a software package containing 5 different tools dedicated to perform predictive analysis and result assessement on CRISPR/Cas experiments. 
    '''),
    html.P(),
    dcc.Tabs(id="main-menu", value='Main menu', children=[
        dcc.Tab(label='Add variants', value='add-variants'),
        dcc.Tab(label='Index genome', value='index-genome'),
        dcc.Tab(label='Search', value='search'),
        dcc.Tab(label='Annotate results', value='annotate-results'),
        dcc.Tab(label='Generate report', value='generate-report'),
        dcc.Tab(label='View report', value='view-report')
    ]),
    html.Div(id='tab-content')
])

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains ']]     #for filtering

@app.callback(Output('tab-content', 'children'),
              [Input('main-menu', 'value')])
def render_content(tab):
    if tab == 'add-variants':
        #TODO https://community.plot.ly/t/dash-loading-states/5687/27
        #TODO https://www.w3schools.com/howto/howto_css_loader.asp
        #TODO https://community.plot.ly/t/in-a-plotly-dash-app-how-to-show-a-default-text-value-in-a-div-upon-each-click-on-a-dropdown-or-button-etc-until-the-div-is-populated/14588/4
        #CHECK http://yaaics.blogspot.com/2019/03/circular-references-in-plotlydash.html
        final_list = []

        final_list.append(html.Button('Long process', id = 'long-process-button'))
        final_list.append(html.Div(id='loop_breaker_container', children=[]))
        final_list.append(html.Div('Loading processo x',className = 'loader-name', id = 'id-loader-name',  style = {'visibility':'hidden'}))
        final_list.append(html.Div('',className = 'loader', id='sbinnato', style = {'visibility':'hidden'}))
        return final_list
    return []

######################TEST###################
@app.callback(
    [Output('sbinnato', 'style'),
    Output('id-loader-name', 'style'),],
    [Input('long-process-button', 'n_clicks')]
)
def modifyVisibilitySbin(n):
    if n is None:
        raise PreventUpdate
    if n > 0:
        return {'visibility':'visible'}, {'visibility':'visible'}
    else:
        return {'visibility':'hidden'}, {'visibility':'hidden'}


@app.callback(
    Output('loop_breaker_container', 'children'),
    [Input('sbinnato', 'style')],
    [State('long-process-button', 'n_clicks')]
)
def longProcess(style, n):
  
    if n is None:
        raise PreventUpdate
    if n > 0:
        subprocess.call(["sleep", "5s"])
        return [html.Div(id='loop_breaker', children=True)]
    return [html.Div(id='loop_breaker', children=False)]

@app.callback(
    Output('long-process-button', 'n_clicks'),
    [Input ('loop_breaker', 'children')]
)
def resetButton(val):
    if val is None or val is '':
        raise PreventUpdate

    if val:
        return 0
    return None

if __name__ == '__main__':
    app.run_server(debug=True)
    cache.clear()       #delete cache when server is closed
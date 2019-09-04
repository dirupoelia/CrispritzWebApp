#test per cache su disco
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
#import time                                 #measure time for loading df table
# for caching
import os
import copy
import time
import datetime
import numpy as np
from flask_caching import Cache

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
        final_list = []

        #Images from the report #TODO modify the 3 call for .savefig to also create png images in radar_chart.py and radar_chart_docker.py
        onlydir = [f for f in listdir('Results') if isdir(join('Results', f))]
        result_file = []
        for result_name in onlydir:
            result_file.append({'label': result_name, 'value' : result_name})
        final_list.append(html.P(["Select an available result file ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your directory containing the result file into the Results directory"))]))
        final_list.append(html.Div(
            dcc.Dropdown(options = result_file, clearable = False, id = "available-results-view", style={'position':'relative', 'zIndex':'999', 'widht':'50%'}), #position and zindex is for avoid being under column fixed
            id = 'div-available-results-view')
        )
        final_list.append(html.Br())

        #Table for targets and score#TODO check if user has created only targets or also scores
        
        # final_list.append(dash_table.DataTable(
        #     id='result-table', 
        #     columns=[{"name": i, "id": i} for i in df.columns], 
        #     data=df.to_dict('records'), 
        #     virtualization = True,
        #     fixed_rows={ 'headers': True, 'data': 0 },
        #     style_cell={'width': '150px'},
        #     page_current=0,
        #     page_size=PAGE_SIZE,
        #     page_action='custom'
        #     )
        # )
        col_list = ['#Bulge type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Direction', 'Mismatches', 'Bulge Size', 'CFD', 'Doench 2016']
        final_list.append(dash_table.DataTable(
            id='result-table', 
            columns=[{"name": i, "id": i} for i in col_list], 
            #data=[{'type':'1', 'rna':'1', 'dna':'1', 'chr':'1', 'pos':'1', 'strand':'1', 'mm':'1', 'bulge':'1', 'cfd':'1', 'doe':'1'}],
            virtualization = True,
            fixed_rows={ 'headers': True, 'data': 0 },
            style_cell={'width': '150px'},
            page_current=0,
            page_size=PAGE_SIZE,
            page_action='custom',
            sort_action='custom',
            sort_mode='multi',
            sort_by=[],
            filter_action='custom',
            filter_query=''
            )
        )

        # hidden signal value
        final_list.append(html.Div(id='signal', style={'display': 'none'}))
        return final_list
    if tab == 'index-genome':
        cache.clear()


# perform expensive computations in this "global store"
# these computations are cached in a globally available
# redis memory store which is available across processes
# and for all time.
@cache.memoize()
def global_store(value):
    # simulate expensive query
    target = [f for f in listdir('Results/' + value) if isfile(join('Results/'+value, f)) and f.endswith('scores.txt') ]    #TODO check if targets or scores exists and load the appropriate
    
    df = pd.read_csv('Results/' +value + '/' + target[0], sep = '\t')
    return df

@app.callback([Output('signal', 'children'), Output('result-table', 'page_current'), Output('result-table', "sort_by"), Output('result-table','filter_query')], [Input('available-results-view', 'value')])
def compute_value(value):
    # compute value and send a signal when done
    if value is None:
        raise PreventUpdate
    global_store(value)
    return value, 0, [], ''

#Send the data when next or prev button is clicked on the result table
@app.callback(
    Output('result-table', 'data'),
    [Input('signal', 'children'),
     Input('result-table', "page_current"),
     Input('result-table', "page_size"),
     Input('result-table', "sort_by"),
     Input('result-table', 'filter_query')])
def update_table(value, page_current,page_size, sort_by, filter):
    if value is None:
        raise PreventUpdate
    print(filter)

    filtering_expressions = filter.split(' && ')    
    df = global_store(value)
    dff = df
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )
    
    return dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')


#For filtering
def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3



if __name__ == '__main__':
    app.run_server(debug=True)
    cache.clear()       #delete cache when server is closed
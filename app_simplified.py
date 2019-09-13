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
import os
import string                               #for job id
import random                               #for job id
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
app_location = os.path.dirname(os.path.abspath(__file__)) + '/'
operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains ']]     #for filtering

#Dropdown available genomes
onlydir = [f for f in listdir('Genomes') if isdir(join('Genomes', f))]
gen_dir = []
for dir in onlydir:
    gen_dir.append({'label': dir, 'value' : dir})

#Dropdown available PAM
onlyfile = [f for f in listdir('pam') if isfile(join('pam', f))]
pam_file = []
for pam_name in onlyfile:
    pam_file.append({'label': pam_name, 'value' : pam_name})

#Dropdown available Variants
onlydir = [f for f in listdir('Variants') if isdir(join('Variants', f))]
var_dir = []
for dir in onlydir:
    var_dir.append({'label': dir, 'value' : dir})

#For multipage
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

final_list = []
final_list.extend([html.H1('CRISPRitz Web Application'),
    html.Div(children='''
        CRISPRitz is a software package containing 5 different tools dedicated to perform predictive analysis and result assessement on CRISPR/Cas experiments. 
    '''),
    html.P()])

final_list.append(
    html.Div(
        [
            html.P(['Download the offline version here: ', html.A('www.google.com', href = 'https://github.com/InfOmics/CRISPRitz', target="_blank")])
        ]
    )
)

# final_list.append(
#     html.Div(
#         [
#             html.P('Insert Job title: ', style = {'padding-top':'5px'}),
#             dcc.Input(id = 'job-name', size = '30')
#         ],
#         className = 'flex-job-title',
#         style = {'margin':'1%', 'width':'23%'}
#     )
# )
final_list.append(
    html.Div(
        [
            html.P('Insert Email: ', style = {'padding-top':'5px'}),
            dcc.Input(id = 'email', size = '30')
        ],
        className = 'flex-job-title',
        style = {'margin':'1%', 'width':'23%'}
    )
)

final_list.append(
    html.Div(
        [
            html.Div(
                html.Div(
                    [
                        html.H5('Step 1'),
                        html.P('Insert Job title: ', style = {'padding-top':'5px'}),
                        dcc.Input(id = 'job-name', size = '30'),
                        html.P('Select a Genome'),
                            
                            html.Div(
                                dcc.Dropdown(options = gen_dir, clearable = False, id = "available-genome"),
                                style = {'width':'50%'}
                            ),
                            html.P('Select a vcf file'),
                            html.Div(
                                dcc.Dropdown(options = var_dir, clearable = False, id = 'available-variant'),
                                style = {'width':'50%'}
                            )
                            
                    ],
                    id = 'div-step1',
                    style = {'margin':'1%'}
                ),
                style = {'background-color':'#eee', 'border-radius': '10px', 'width':'45%'},
                id = 'div-background-step1'
            ),
            html.Div(
                html.Div(
                    [
                        html.H5('Step 2'),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P('Insert guide'),
                                        dcc.Textarea(id = 'guides', rows = 20, style = {'width':'300px', 'height':'200px'})
                                    ]
                                ),
                                html.Div(
                                    html.Div(
                                        [
                                            html.P('Select a Pam', style = {'margin':'5px'}),
                                            html.Div(
                                                dcc.Dropdown(options = pam_file, clearable = False, id = "available-pams"),
                                                #style = {'width':'75%'}
                                            ),
                                            html.P('Select # of mismatches', style = {'margin':'5px'}),
                                            html.Div(
                                                dcc.Dropdown(options = pam_file, clearable = False, id = "mismatches"),
                                                #style = {'width':'75%'}
                                            ),
                                            html.P('Select # of DNA bulges', style = {'margin':'5px'}),
                                            html.Div(
                                                dcc.Dropdown(options = pam_file, clearable = False, id = "dna"),
                                                #style = {'width':'75%'}
                                            ),
                                            html.P('Select # of RNA bulges', style = {'margin':'5px'}),
                                            html.Div(
                                                dcc.Dropdown(options = pam_file, clearable = False, id = "rna"),
                                                #style = {'width':'75%'}
                                            )
                                        
                                        ],
                                        className = 'flex-pam-mm-bul',
                                        #style={'flex-basis': '200px'} 
                                    )
                                )
                                
                            ],
                            className = 'flex-guide-pam-mm-bul'
                        ),


                        
                        html.Button('Submit job', id = 'submit-job')
                    ],
                
                    id = 'div-step2',
                    style = {'margin':'1%', 'width':'75%'}
                
                ),
                style = {'background-color':'#eee', 'border-radius': '10px', 'width':'45%'},
                id = 'div-background-step2'
            )
        ],
        className = 'flex-steps'
    )
)

index_page = html.Div(final_list, style = {'margin':'1%'})

#Load Page
final_list = []
final_list.append(html.P('Passo1', id = 'passo1'))
final_list.append(html.P('Passo2', id = 'passo2'))
final_list.append(html.P('', id = 'done'))

final_list.append(dcc.Interval(id = 'load-page-check', interval=3*1000))
load_page = html.Div(final_list, style = {'margin':'1%'})
##################################################CALLBACKS##################################################

#Submit Job, chenge url
@app.callback(
    [Output('url', 'pathname'),
    Output('url','search')],

    [Input('submit-job', 'n_clicks')]
)
def changeUrl(n):
    if n is None:
        raise PreventUpdate
    
    job_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    subprocess.Popen(['sleep 5s; mkdir Results/' + job_id], shell = True)
    return '/load','?job=' + job_id

#When url changed, load new page
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def changePage(path):
    if path == '/load':
        return load_page

    return index_page

#Check end job
@app.callback(
    Output('done', 'children'),
    [Input('load-page-check', 'n_intervals')],
    [State('url', 'search')]
)
def refreshSearch(n, dir_name):
    if n is None:
        raise PreventUpdate
    onlydir = [f for f in listdir('Results') if isdir(join('Results', f))]
    print(onlydir)
    print(dir_name.split('=')[-1])
    if dir_name.split('=')[-1] in onlydir:
        return 'Done'
    raise PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True)
    cache.clear()       #delete cache when server is closed
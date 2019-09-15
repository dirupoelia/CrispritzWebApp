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
# final_list.append(
#     html.Div(
#         [
#             html.P('Insert Email: ', style = {'padding-top':'5px'}),
#             dcc.Input(id = 'email', size = '30')
#         ],
#         className = 'flex-job-title',
#         style = {'margin':'1%', 'width':'23%'}
#     )
# )



#new final_list
final_list = []
final_list.extend([html.H1('CRISPRitz Web Application'),
    html.Div(children='''
        CRISPRitz is a software package containing 5 different tools dedicated to perform predictive analysis and result assessement on CRISPR/Cas experiments. 
    '''),
    html.P()])

final_list.append(
    html.Div(
        [
            html.P(['Download the offline version here: ', html.A('InfOmics/CRISPRitz', href = 'https://github.com/InfOmics/CRISPRitz', target="_blank"), ' or ', html.A('Pinellolab/CRISPRitz', href = 'https://github.com/pinellolab/CRISPRitz', target="_blank") ])
        ]
    )
)

final_list.append(
    html.Div(
        html.Div(
            [
                html.Div(
                    [
                        html.H3('STEP 1', style = {'margin-top':'0'}), 
                        html.P('Select a genome'),
                        html.Div(
                            dcc.Dropdown(options = gen_dir, clearable = False, id = "available-genome", style = {'width':'75%'}),
                            #style = {'width':'50%'}
                        ),
                        html.P('Add a genome variant'),
                        html.Div(
                            dcc.Dropdown(options = var_dir, clearable = False, id = 'available-variant', style = {'width':'75%'})
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P('Select PAM'),
                                        html.Div(
                                            dcc.Dropdown(options = pam_file, clearable = False, id = 'available-pam', style = {'width':'75%'})
                                        )
                                    ],
                                    style = {'flex':'0 0 50%'}
                                ),
                                #html.P('or'),
                                html.Div(
                                    [
                                        html.P('Insert custom PAM'),
                                        dcc.Input(type = 'text')
                                    ]
                                )
                            ],
                            id = 'div-pam',
                            className = 'flex-div-pam'
                        )
                    ],
                    id = 'step1',
                    style = {'flex':'0 0 40%'}
                ),
                html.Div(style = {'border-right':'solid 1px white'}),
                html.Div(
                    [
                        html.H3('STEP 2', style = {'margin-top':'0'}),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        
                                        html.Div(
                                            [
                                                html.P(['Insert crRNA sequence(s)', html.Abbr('\uD83D\uDEC8', style = {'text-decoration':'none'} ,title = 'One sequence per line. All sequences must have the same lenght and PAM characters are not required')], style = {'word-wrap': 'break-word'}), 
                            
                                                dcc.Textarea(id = 'text-guides', placeholder = 'GAGTCCGAGCAGAAGAAGAANNN\nCCATCGGTGGCCGTTTGCCCNNN', style = {'width':'275px', 'height':'160px'}),
                                                html.P('or', style = {'position': 'relative', 'left':'50%'}),
                                                html.Div(
                                                    [
                                                        dcc.Upload('Upload file with crRNA sequences',id = 'upload-guides')
                                                    ],
                                                    style={
                                                        'width': '100%',
                                                        'height': '60px',
                                                        'lineHeight': '60px',
                                                        'borderWidth': '1px',
                                                        'borderStyle': 'dashed',
                                                        'borderRadius': '5px',
                                                        'textAlign': 'center',
                                                        #'margin': '10px'
                                                    }
                                                )
                                            ],
                                            style = {'width':'275px'} #same as text-area
                                        )
                                    ],
                                    id = 'div-guides'
                                ),
                                html.Div(
                                    [
                                        html.P('Allowed mismatches'),
                                        dcc.Input(value = '0', id = 'mms', type = 'number', min = '0', style = {'width':'60px'}),
                                        html.P('Bulge DNA size'),
                                        dcc.Input(value = '0', id = 'dna', type = 'number', min = '0', style = {'width':'60px'}),
                                        html.P('Bulge RNA size'),
                                        dcc.Input(value = '0', id = 'rna', type = 'number', min = '0', style = {'width':'60px'})
                                    ]
                                )
                            ],
                            className = 'flex-step2'
                        )

                    ],
                    id = 'step2',
                    style = {'flex':'0 0 40%'}
                    
                ),
                html.Div(style = {'border-right':'solid 1px white'}),
                html.Div(
                    [
                        html.H3('Submit', style = {'margin-top':'0'}),
                        html.Div(
                            [
                                html.Button('Submit', id = 'submit-job')
                            ],
                            style = {'display':'inline-block', 'margin':'0 auto'}
                        )
                    ],
                    id = 'step3',
                    style = {'tex-align':'center'}
                )
            ],
            id = 'div-steps',
            style = {'margin':'1%'},
            className = 'flex-div-steps'
        ),
        style = {'background-color':'rgba(154, 208, 150, 0.39)', 'border-radius': '10px', 'border':'1px solid black'},
        id = 'steps-background'
    )
)
index_page = html.Div(final_list, style = {'margin':'1%'})

#Load Page
final_list = []
final_list.append(html.H1('CRISPRitz Web Application'))
final_list.append(
    html.Div(
        html.Div(
            html.Div(
                [
                    html.P('Job submitted. Copy this link to view the status and the result page '),
                    html.Div(
                        html.P('link', id = 'job-link'),
                        style = {'border':'2px solid', 'border-color':'blue' ,'width':'70%','display':'inline-block', 'margin':'5px'}
                    )
                ],
                style = {'display':'inline-block'}
            ),
            style = {'display':'inline-block','background-color':'rgba(154, 208, 150, 0.39)', 'border-radius': '10px', 'border':'1px solid black', 'width':'70%'}
        ),
        style = {'text-align':'center'}
    )
)

final_list.append(
    html.Div(
        [
            html.H4('Status report'),
            html.Div(
                [
                    html.Div(
                        html.Ul(
                            [
                                html.Li('Adding variants'),
                                html.Li('Searching crRNA'),
                                html.Li('Generating report')
                            ]
                        ),
                        style = {'flex':'0 0 20%'}
                    ),
                    html.Div(
                        html.Ul(
                            [
                                html.Li('To do', style = {'color':'red'}, id = 'add-variants-status'),
                                html.Li('To do', style = {'color':'red'}, id = 'search-status'),
                                html.Li('To do', style = {'color':'red'}, id = 'generate-report-status')
                            ],
                            style = {'list-style-type':'none'}
                        )
                    )
                ],
                className = 'flex-status'
            )
        ]
    )
)

final_list.append(html.P('', id = 'done'))

final_list.append(dcc.Interval(id = 'load-page-check', interval=3*1000))
load_page = html.Div(final_list, style = {'margin':'1%'})
##################################################CALLBACKS##################################################

#Submit Job, chenge url
@app.callback(
    [Output('url', 'pathname'),
    Output('url','search')
    ],
    [Input('submit-job', 'n_clicks')],
    [State('url', 'href')]
)
def changeUrl(n, href):
    if n is None:
        raise PreventUpdate
    
    job_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    subprocess.Popen(['sleep 5s; mkdir Results/' + job_id], shell = True)
    print( 'change url: ',href + '?job=' + job_id)
    return '/load','?job=' + job_id

#When url changed, load new page
@app.callback(
    [Output('page-content', 'children'),
    Output('job-link', 'children')],
    [Input('url', 'pathname')],
    [State('url','href'), 
    State('url','search')
    ]
)
def changePage(path, href, search):
    print ('changepage: ', href)
    print('search', search)
    if path == '/load':
        return load_page, href+search   #TODO se ricarico la pagina si sdoppia il search

    return index_page, ''

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
    
    if dir_name.split('=')[-1] in onlydir:
        return 'Done'
    raise PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True)
    cache.clear()       #delete cache when server is closed
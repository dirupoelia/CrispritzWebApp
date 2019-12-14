#NEW: 
#Result page with tabs
#Image result for Samples

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
import sys                                  #for sys.exit()
import filecmp                              #check if Params files are equals
import dash_bootstrap_components as dbc
import collections                          #For check if guides are the same in two results
from datetime import datetime               #For time when job submitted
from seq_script import extract_seq, convert_pam
import re                                   #For sort chr filter values
#Warning symbol \u26A0

PAGE_SIZE = 50                    #number of entries in each page of the table in view report
URL = 'http://crispritz.di.univr.it'
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'CRISPRitz'
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

#Populations 1000 gen proj
population_1000gp = {
    'EAS':['CHB', 'JPT', 'CHS', 'CDX', 'KHV'],
    'EUR':['CEU', 'TSI', 'FIN', 'GBR', 'IBS'],
    'AFR':['YRI', 'LWK', 'GWD', 'MSL', 'ESN', 'ASW', 'ACB'],
    'AMR':['MXL', 'PUR', 'CLM', 'PEL'],
    'SAS':['GIH', 'PJL', 'BEB', 'STU', 'ITU']
}
dict_pop_to_superpop = {'CHB':'EAS', 'JPT':'EAS', 'CHS':'EAS', 'CDX':'EAS', 'KHV':'EAS',
                    'CEU':'EUR', 'TSI':'EUR', 'FIN':'EUR', 'GBR':'EUR', 'IBS':'EUR',
                    'YRI':'AFR', 'LWK':'AFR', 'GWD':'AFR', 'MSL':'AFR', 'ESN':'AFR', 'ASW':'AFR', 'ACB':'AFR',
                    'MXL':'AMR', 'PUR':'AMR', 'CLM':'AMR', 'PEL':'AMR',
                    'GIH':'SAS', 'PJL':'SAS', 'BEB':'SAS', 'STU':'SAS', 'ITU':'SAS'
}
#List of all samples
pop_file = pd.read_excel(os.path.dirname(os.path.realpath(__file__)) + '/PostProcess/20130606_sample_info.xlsx')
all_samples = pop_file.Sample.to_list()
all_pop = pop_file.Population.to_list()
dict_pop = dict()
dict_sample_to_pop = dict()
for  pos, i in enumerate(all_pop):
    try:
        dict_pop[i].append(all_samples[pos])
    except:
        dict_pop[i] = [all_samples[pos]]
    
    dict_sample_to_pop[all_samples[pos]] = i
dropdown_all_samples = [{'label': sam, 'value' : sam} for sam in all_samples]
#Dropdown available genomes
onlydir = [f for f in listdir('Genomes') if isdir(join('Genomes', f))]
onlydir = [x.replace('_', ' ') for x in onlydir]
gen_dir = []
for dir in onlydir:
    gen_dir.append({'label': dir, 'value' : dir})

#Dropdown available PAM
onlyfile = [f for f in listdir('pam') if isfile(join('pam', f))]
onlyfile = [x.replace('.txt', '') for x in onlyfile]            #removed .txt for better visualization
pam_file = []
for pam_name in onlyfile:
    if 'NGG' in pam_name:               #TODO modificare per selezionare solo le PAM disponibili
        pam_file.append({'label':pam_name, 'value':pam_name})
    else:
        pam_file.append({'label': pam_name, 'value' : pam_name, 'disabled':True})


#Available mismatches and bulges
av_mismatches = [{'label': i, 'value': i} for i in range(0, 8)]
av_bulges = [{'label': i, 'value': i} for i in range(0, 6)]
av_guide_sequence = [{'label': i, 'value': i} for i in range(15, 26)]
search_bar = dbc.Row(
    [
        #dbc.Col(dbc.Input(type="search", placeholder="Search")),
        dbc.Col(dbc.NavLink('HOME', active = True, href = URL, className= 'testHover', style = {'text-decoration':'none', 'color':'white', 'font-size':'1.5rem'})),
        dbc.Col(dbc.NavLink('ABOUT', active = True, href = URL, className= 'testHover', style = {'text-decoration':'none', 'color':'white', 'font-size':'1.5rem'})),
        dbc.Col(
            dbc.DropdownMenu(
                children=[
                    dbc.DropdownMenuItem("Github", header=True),
                    dbc.DropdownMenuItem("InfOmics/CRISPRitz", href='https://github.com/InfOmics/CRISPRitz'),
                    dbc.DropdownMenuItem("Pinellolab/CRISPRitz", href='https://github.com/pinellolab/CRISPRitz'),
                ],
                #nav=True,
                in_navbar=True,
                label="Downloads",
                style = {'width': '300px !important' } #'height': '400px !important' 
            ),
        ),
        dbc.Col(dbc.NavLink('CONTACTS', active = True, href = URL, className= 'testHover', style = {'text-decoration':'none', 'color':'white', 'font-size':'1.5rem'}))
    ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)
PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"    #TODO modificare logo


navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                    dbc.Col(dbc.NavbarBrand("CRISPRitz Web App", className="ml-2", style = {'font-size': '30px'}))
                ],
                align="center",
                no_gutters=True,
            ),
            href=URL,
        ),
        dbc.NavbarToggler(id="navbar-toggler"),
        dbc.Collapse(search_bar, id="navbar-collapse", navbar=True),
    ],
    color="dark",
    dark=True,
)

#For multipage
app.layout = html.Div([
    navbar,
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    html.P(id = 'signal', style = {'visibility':'hidden'})
])



#Main Page
final_list = []
final_list.extend([#html.H1('CRISPRitz Web Application'),
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
checklist_div = html.Div(
    [
        dbc.FormGroup(
            [
                dbc.Checkbox(
                    id="checkbox-gecko", className="form-check-input"
                ),
                dbc.Label(
                    #html.P(['Activate Gecko ', html.Abbr('comparison', title ='The results of your test guides will be compared with results obtained from a previous computed analysis on gecko library')]) ,
                    html.P('Compare your results with the GeCKO v2 library'),
                    html_for="checkbox-gecko",
                    className="form-check-label",
                ),
                dbc.Checkbox(
                    id="checkbox-ref-comp", className="form-check-input"
                ),
                dbc.Label(
                    #html.P(['Activate Reference genome ', html.Abbr('comparison', title ='The results of your test guides will be compared with the results obtained from a computed analysis on the corresponding reference genome. Note: this may increase computational time')]) ,
                    html.P('Compare your results with the corresponding reference genome'),
                    html_for="checkbox-ref-comp",
                    className="form-check-label",
                )
                
            ],
            check = True
        )
    ],
    id = 'checklist-test-div'
)

modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader("WARNING! Missing inputs"),
                dbc.ModalBody('The following inputs are missing, please select values before submitting the job', id = 'warning-list'),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close" , className="modal-button")
                ),
            ],
            id="modal",
            centered=True
        ),
    ]
)

tab_guides_content = html.Div(
    [
        html.P([
            'Insert crRNA sequence(s), one per line.', 
            html.P('Sequences must have the same length and be provided without the PAM sequence', id = 'testP') ,
        ],
        style = {'word-wrap': 'break-word'}), 

        dcc.Textarea(id = 'text-guides', placeholder = 'GAGTCCGAGCAGAAGAAGAA\nCCATCGGTGGCCGTTTGCCC', style = {'width':'450px', 'height':'160px', 'font-family':'monospace', 'font-size':'large'}),
        dbc.FormText('Note: a maximum number of 1000 sequences can be provided', color = 'secondary')
    ],
    style = {'width':'450px'} #same as text-area
)
tab_sequence_content = html.Div(
    [
        html.P(['Search crRNAs by inserting one or more genomic sequences.', html.P('Chromosome ranges can also be supplied')],
        style = {'word-wrap': 'break-word'}), 

        dcc.Textarea(id = 'text-sequence', placeholder = '>sequence 1\nAAGTCCCAGGACTTCAGAAGagctgtgagaccttggc\n>sequence2\nchr1:11,130,540-11,130,751', style = {'width':'450px', 'height':'160px', 'font-family':'monospace', 'font-size':'large'}),
        #html.P('Note: a maximum number of 1000 sequences can be provided'),
        dbc.FormText('Note: a maximum number of 1000 characters can be provided', color = 'secondary')
    ],
    style = {'width':'450px'} #same as text-area
)
final_list.append(
    html.Div(
        html.Div(
            [
                modal,
                html.Div(
                    [
                        
                        
                        html.Div([
                            html.H3('STEP 1', style = {'margin-top':'0'}),
                            html.Div([
                                html.P([html.Button(html.P("Load example", style={'color':'rgb(46,140,187)','text-decoration-line': 'underline'}), id='example-parameters',
                                            style={ 'border': 'None', 'text-transform': 'capitalize','height':'12','font-weight': '500', 'padding': '0 0px','textcolor':'blu'}), ' - ',
                                #html.Br(),
                                html.Button(html.P(children="Reset", style={'color':'rgb(46,140,187)','text-decoration-line': 'underline'}), id='remove-parameters',
                                            style={'border': 'None', 'text-transform': 'capitalize','height':'12','font-weight': '500', 'padding': '0 0px'})])
                            ])
                        ], className = 'flex-div-insert-delete-example'), 
                        
                        html.P('Select a genome'),
                        html.Div(
                            dcc.Dropdown(options = gen_dir, clearable = False, id = "available-genome",) #style = {'width':'75%'})
                        ),
                        dbc.FormText('Note: Genomes enriched with variants are indicated with a \'+\' symbol', color='secondary'),
                        
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P('Select PAM'),
                                        html.Div(
                                            dcc.Dropdown(options = pam_file, clearable = False, id = 'available-pam')
                                        )
                                    ],
                                    style = {'flex':'0 0 50%', 'margin-top': '10%'}
                                )
                            ],
                            id = 'div-pam',
                            className = 'flex-div-pam'
                        ),
                        html.Div(
                            [
                                html.Ul(
                                    [html.Li(
                                        [html.A('Contact us', href = URL, target="_blank"),' to request new genomes availability in the dropdown list'],
                                        style = {'margin-top':'5%'}
                                    ),
                                    html.Li(
                                        [html.A('Download', href = 'https://github.com/InfOmics/CRISPRitz'), ' the offline version for more custom parameters']
                                    )
                                    ],
                                    style = {'list-style':'inside'}
                                ),
                                # html.Div(
                                #     html.Button('Insert example parameters', id = 'example-parameters', style={'display':'inline-block'}),
                                #     style = {'text-align':'center'}
                                # )
                            ],
                            style = {'height':'50%'}
                        ),
                        
                    ],
                    id = 'step1',
                    style = {'flex':'0 0 30%', 'tex-align':'center'}
                ),
                html.Div(style = {'border-right':'solid 1px white'}),
                html.Div(
                    [
                        html.H3('STEP 2', style = {'margin-top':'0'}),
                        html.Div(
                            [
                                html.Div(
                                    [   html.P('Select the input type'),
                                        dbc.Tabs(
                                            [
                                                dbc.Tab(tab_guides_content, label='Guides', tab_id= 'guide-tab'),
                                                dbc.Tab(tab_sequence_content, label='Sequence', tab_id = 'sequence-tab')
                                            ],
                                            active_tab='guide-tab',
                                            id = 'tabs'
                                        )
                                    ],
                                    id = 'div-guides'
                                ),
                                html.Div(
                                    [
                                        html.P('Allowed mismatches'),
                                        dcc.Dropdown(options = av_mismatches, clearable = False, id = 'mms', style = {'width':'60px'}),
                                        html.P('Bulge DNA size'),
                                        dcc.Dropdown(options = av_bulges, clearable = False, id = 'dna', style = {'width':'60px'}),
                                        html.P('Bulge RNA size'),
                                        dcc.Dropdown(options = av_bulges, clearable = False, id = 'rna', style = {'width':'60px'}),
                                        dbc.Fade(
                                            [
                                                html.P('crRNA length (without PAM)'),
                                                dcc.Dropdown(options = av_guide_sequence, clearable = False, id = 'len-guide-sequence-ver', style = {'width':'60px'})
                                            ],
                                            id = 'fade-len-guide', is_in= False, appear= False
                                        )
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
                        html.H3('Advanced Options', style = {'margin-top':'0px'}),
                        checklist_div,
                        dcc.Checklist(
                            options = [
                                {'label':'Notify me by email','value':'email', 'disabled':False}
                            ], 
                            id = 'checklist-advanced',
                        ),
                        dbc.Fade(
                            [
                                dbc.FormGroup(
                                    [
                                        dbc.Label("Email", html_for="example-email"),
                                        dbc.Input(type="email", id="example-email", placeholder="Enter email", className='exampleEmail'),
                                        # dbc.FormText(
                                        #     "Are you on email? You simply have to be these days",
                                        #     color="secondary",
                                        # ),
                                    ]
                                )
                            ],
                            id = 'fade', is_in= False, appear= False
                        ),
                        #html.H3('Submit', style = {'margin-top':'0'}),
                        html.Div(
                            [
                                html.Button('Submit', id = 'check-job', style = {'background-color':'skyblue'}),
                                html.Button('', id = 'submit-job', style = {'display':'none'})
                            ],
                            style = {'display':'inline-block', 'margin':'0 auto'}   #style="height:55px; width:150px"
                        )
                    ],
                    id = 'step3',
                    style = {'tex-align':'center'},
                    className = 'flex-step3'
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
                                html.Li('Searching crRNA'),
                                html.Li('Annotating result'),
                                html.Li('Generating report'),
                                html.Li('Post Process data')
                            ]
                        ),
                        style = {'flex':'0 0 20%'}
                    ),
                    html.Div(
                        html.Ul(
                            [
                                html.Li('To do', style = {'color':'red'}, id = 'search-status'),
                                html.Li('To do', style = {'color':'red'}, id = 'annotate-result-status'),
                                html.Li('To do', style = {'color':'red'}, id = 'generate-report-status'),
                                html.Li('To do', style = {'color':'red'}, id = 'post-process-status')
                            ],
                            style = {'list-style-type':'none'}
                        )
                    )
                ],
                className = 'flex-status'
            ),
            html.Div(
                [
                    dcc.Link('View Results', style = {'visibility':'hidden'}, id = 'view-results'),
                    html.Div(id = 'no-directory-error')
                ]
            )
        ],
        id = 'div-status-report'
    )
)

final_list.append(html.P('', id = 'done'))

final_list.append(dcc.Interval(id = 'load-page-check', interval=3*1000))
load_page = html.Div(final_list, style = {'margin':'1%'})


#Test bootstrap page, go to /test-page to see 
final_list = []
# radar_img = 'Results/W0Q0702F1E/test.summary_single_guide_GAGTCCGAGCAGAAGAAGAANNN_4mm.png'
# radar_src = 'data:image/png;base64,{}'.format(base64.b64encode(open(radar_img, 'rb').read()).decode())
# final_list.append(html.Img(src = radar_src, width="100%", height="auto"))
# final_list.append(html.P('List of Targets found for the selected guide'))

# df = pd.read_csv('esempio_tabella_cluster.txt', sep = '\t')
# exp_col = []
# close_col = []
# status_col = []     #'Top1' or 'Subcluster'
# df.drop( df[df['top'] == 's'].index, inplace = True)

# for i in range (df.shape[0]):
#     exp_col.append('+')
#     close_col.append('-')
#     status_col.append('Top1')
# df['Open'] = exp_col
# df['Close'] = close_col
# df['Status'] = status_col
# print('columns:', df.columns)
# final_list.append(dash_table.DataTable(
#     id='table-expand',
#     columns=[{"name": i, "id": i} for i in df.columns[:]],
#     data=df.to_dict('records'),
#     row_selectable = 'multi',
#     style_data_conditional = [{
#                         'if': {
#                                 'filter_query': '{Variant unique} eq y', 
#                                 #'column_id' :'{#Bulge type}',
#                                 #'column_id' :'{Total}'
#                             },
#                             #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
#                             'background-color':'rgba(230, 0, 0,0.65)'#'rgb(255, 102, 102)'
                            
#                         }]
# ))
final_list.append(html.Div(id='test-div-for-button'))
test_page = html.Div(final_list, style = {'margin':'1%'})

#TEST PAGE 2
final_list = []
# final_list.append(html.P('List of Targets found for the selected guide'))
# final_list.append(html.P('Select a row to view the corresponding cluster'))
# df_example = pd.read_csv('esempio_tabella_cluster.txt', sep = '\t')
# print('TABELLA CLUSTER', df_example)
# #df_example.drop( df_example[df_example['top'] == 's'].index, inplace = True)
# final_list.append(dash_table.DataTable(
#     id='double-table-one',
#     columns=[{"name": i, "id": i} for i in df_example.columns[:-2]],
#     data= df_example.loc[df_example['top'] == 't'].to_dict('records'), #df_example.to_dict('records'),
#     css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],

#     style_data_conditional = [{
#                         'if': {
#                                 'filter_query': '{Variant unique} eq y', 
#                                 #'column_id' :'{#Bulge type}',
#                                 #'column_id' :'{Total}'
#                             },
#                             #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
#                             'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
#                         }]
# ))
# final_list.append(html.P())
# final_list.append(html.P())
# final_list.append(html.Div(
#     dash_table.DataTable(
#         id = 'double-table-two',
#         #columns=[{"name": i, "id": i} for i in df_example.columns[:]],
#         #fixed_rows = {'headers' : True, 'data': 0},
#         page_current=0,
#         page_size=PAGE_SIZE,
#         page_action='custom',
#         virtualization = True,
#         css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],

#         style_data_conditional = [{
#                         'if': {
#                                 'filter_query': '{Variant unique} eq y', 
#                                 #'column_id' :'{#Bulge type}',
#                                 #'column_id' :'{Total}'
#                             },
#                             #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
#                             'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
#                         },
#                         {
#                             'if': {
#                                     'filter_query': '{top} eq t',         
#                                     # 'column_id' :'BulgeType'
#                                 },
#                                 # 'border-left': '5px solid rgba(26, 26, 255, 0.9)',
#                                 'font-weight':'bold'
                                

#                         }    
                        
#                     ]
#         ),
#     id = 'div-test-page2-second-table'
#     )
# )
test_page2 = html.Div(final_list, style = {'margin':'1%'})

#TEST page3 for new result page
final_list = []

test_page3 = html.Div(final_list, style = {'margin':'1%'})

##################################################CALLBACKS##################################################
#Test callbacks

# #Callback for test-page2
# @app.callback(
#     [Output('double-table-two', 'data'),
#     Output('double-table-two', 'columns')],
#     [Input('double-table-one', 'active_cell')],
#     [State('double-table-one', 'data')]
# )
# def loadSecondTable(active_cell, data):
#     if active_cell is None:
#         raise PreventUpdate
    
#     id_selected = data[active_cell['row']]['id']
    
#     return df_example.loc[df_example['id'] == id_selected].to_dict('records'), [{"name": i, "id": i} for i in list(data[0].keys())[:-2]]




# #IDEA aggiungo colonna che mi indica se è top1 o solo parte del cluster, se l'utente clicca su +, faccio vedere anche quelle corrispondenti a quel cluster
# @app.callback(
#     Output('table-expand', 'data'),
#     #[Input('table-expand', 'active_cell')],
#     [Input('table-expand','selected_rows')],
#     [State('table-expand', 'data'),
#     State('table-expand', 'selected_row_ids')]
# )
# def expand(active_cell,  data, sri):    #Callback for test-page
#     if active_cell is None:
#         raise PreventUpdate
    
#     #df = pd.DataFrame(data)
#     df = pd.read_csv('esempio_tabella_cluster.txt', sep = '\t')
#     print('Sel row', active_cell)
    
#     print('Sel row id', sri)
#     print('Data', data)
#     df.drop( df[(df['top'] == 's') & (~( df['id'].isin(sri)))].index, inplace = True)
#     # for i in range (df.shape[0]):
#     #     exp_col.append('+')
#     #     close_col.append('-')
#     #     status_col.append('Top1')
#     # df['Open'] = exp_col
#     # df['Close'] = close_col
#     # df['Status'] = status_col
#     print('df',df)
#     return df.to_dict('records')
#     # if active_cell['column_id'] == 'Open': 
#     #     if df.iat[active_cell['row'], -1] == 'Top1':
#     #         df.iat[active_cell['row'], -1] = 'Subcluster'    
#     #         df.loc[-1] = 'n'
#     #         return df.to_dict('records')
#     #     else:
#     #         raise PreventUpdate
#     # elif active_cell['column_id'] == 'Close':
#     #     if df.iat[active_cell['row'], -1] == 'Subcluster':
#     #         df.iat[active_cell['row'], -1] = 'Top1'
#     #         df.drop(df.tail(1).index,inplace=True)
#     #         return df.to_dict('records')
#     # raise PreventUpdate

    
#################################################
#Fade in/out email
@app.callback(
    Output("fade", "is_in"),
    [Input("checklist-advanced", "value")],
    [State("fade", "is_in")],
)
def toggle_fade(selected_options, is_in):
    '''
    Selezionando l'opzione Notify me by email, compare una box in cui poter inserire l'email
    '''
    if  selected_options is None:
        return False
    if 'email' in selected_options:
        return True
    return False

# Insert/Delete example input
@app.callback(
    [Output('available-genome', 'value'),
     Output('available-pam', 'value'),
     Output('text-guides', 'value'),
     Output('mms', 'value'),
     Output('dna', 'value'),
     Output('rna', 'value'),
     Output('len-guide-sequence-ver', 'value'),
     Output('text-sequence', 'value')],
     [Input('example-parameters', 'n_clicks_timestamp'),
     Input('remove-parameters', 'n_clicks_timestamp')]
)
def inExample(nI, nR):
    '''
    Bottone per inserire degli input di esempio.
    Bottone reset esegue il punto a), ma non cancella le spunte delle Advanced Options
    a) cancellare tutto
    b) cancellare solo i campi i cui valori sono uguali a quelli di esempio
    c) se almeno un campo è diverso dal valore di esempio, non cancello nulla)
    '''

    if (nI is None) and (nR is None):
        raise PreventUpdate

    if nI is None:
        nI = 0

    if nR is None:
        nR = 0
    
    if nI > 0:
        if nI > nR:
            return 'hg38 ref+hg38 1000genomeproject', '5\'-NGG-3\'', 'GAGTCCGAGCAGAAGAAGAA\nCCATCGGTGGCCGTTTGCCC', '4', '0', '0', '20', '>sequence\nTACCCCAAACGCGGAGGCGCCTCGGGAAGGCGAGGTGGGCAAGTTCAATGCCAAGCGTGACGGGGGA'


    if nR > 0:
        if nR > nI:
            return '', '', '', '', '', '', '', ''



    # TODO salvare una cartella speciale in results che abbia i risultati di questa ricerca in modo da non occupare il server con
    # questa ricerca di esempio, ma all'utente passo già la cartella fatta (questa parte già implementata)
    # return '', '', '', '', '', '', ''
#If selected genome has a '+', update advanced options comparison with reference
@app.callback(
    Output('checkbox-ref-comp', 'checked'),
    [Input('available-genome', 'value')]
)
def suggestComparison(value):
    if value is None:
        raise PreventUpdate
    if '+' in value:
        return True
    raise PreventUpdate 

#Email validity
@app.callback(
    Output('example-email', 'style'),
    [Input('example-email', 'value')]
)
def checkEmailValidity(val):
    '''
    Controlla se l'email inserita è valida, cambiando il bordo in rosso o verde
    '''
    if val is None:
        raise PreventUpdate

    if '@' in val:
        return {'border':'1px solid #94f033', 'outline':'0'}
    return {'border':'1px solid red'}

#Fade in guide len dropdown for sequence tabs version
@app.callback(
    Output('fade-len-guide', 'is_in'),
    [Input('tabs', 'active_tab')],
    [State('fade-len-guide', 'is_in')]
)
def resetTab(current_tab, is_in):
    '''
    Fa comparire/scomparire  il dropdown per la lunghezza delle guide se l'utente seleziona l'opzione Sequence
    '''
    if current_tab is None:
        raise PreventUpdate

    if current_tab == 'guide-tab':
        return False
    return True


#Check input presence
@app.callback(
    [Output('submit-job', 'n_clicks'),
    Output('modal', 'is_open'),
    Output('available-genome', 'className'),
    Output('available-pam', 'className'),
    Output('text-guides', 'style'),
    Output('mms', 'className'),
    Output('dna', 'className'),
    Output('rna', 'className'),
    Output('len-guide-sequence-ver', 'className'),
    Output('warning-list', 'children')],
    [Input('check-job','n_clicks'),
    Input('close','n_clicks')],
    [State('available-genome', 'value'),
    State('available-pam','value'),
    State('text-guides', 'value'),
    State('mms','value'),
    State('dna','value'),
    State('rna','value'),
    State('len-guide-sequence-ver','value'),
    State('tabs','active_tab'),
    State("modal", "is_open")]
)
def checkInput(n, n_close, genome_selected, pam, text_guides, mms, dna, rna, len_guide_seq, active_tab ,is_open):
    '''
    La funzione prende i valori dei vari campi di input e controlla che siano tutti presenti, tranne la textbox delle guide e della sequenza.
    Se qualcuno manca, colora il suo bordo di rosso e fa uscire un avviso con l'elenco degli input mancanti. 
    La callback si aziona anche quando l'utente clicca Close nel modal e in quel caso chiude l'avviso
    '''
    if n is None:
        raise PreventUpdate
    if is_open is None:
        is_open = False
    
    classname_red = 'missing-input'
    genome_update = None
    pam_update = None
    text_update = {'width':'450px', 'height':'160px'}
    mms_update = None
    dna_update = None
    rna_update = None
    len_guide_update = None
    update_style = False
    miss_input_list = []
    
    if genome_selected is None or genome_selected is '':
        genome_update = classname_red
        update_style = True
        miss_input_list.append('Genome')
    if pam is None or pam is '':
        pam_update = classname_red
        update_style = True
        miss_input_list.append('PAM')
    # if text_guides is None or text_guides is '':
        # text_update = {'width':'450px', 'height':'160px','border': '1px solid red'}
        # update_style = True
        # miss_input_list.append('crRNA sequence(s)')
    if mms is None or str(mms) is '':
        mms_update = classname_red
        update_style = True
        miss_input_list.append('Allowed Mismatches')
    if dna is None or str(dna) is '':
        dna_update = classname_red
        update_style = True
        miss_input_list.append('Bulge DNA size')
    if rna is None or str(rna) is '':
        rna_update = classname_red
        update_style = True
        miss_input_list.append('Bulge RNA size')
    if (len_guide_seq is None or str(len_guide_seq) is '') and ('sequence-tab' in active_tab):
        len_guide_update = classname_red
        update_style = True
        miss_input_list.append('crRNA length')
    miss_input = html.Div(
        [
            html.P('The following inputs are missing:'),
            html.Ul([html.Li(x) for x in miss_input_list]),
            html.P('Please fill in the values before submitting the job')
        ]
    )
    
    if not update_style:
        return 1, False, genome_update, pam_update, text_update, mms_update, dna_update, rna_update, len_guide_update, miss_input
    return None, not is_open, genome_update, pam_update, text_update, mms_update, dna_update, rna_update, len_guide_update, miss_input

#Submit Job, change url
@app.callback(
    [Output('url', 'pathname'),
    Output('url','search')],
    [Input('submit-job','n_clicks')],
    [State('url', 'href'),
    State('available-genome', 'value'),
    State('available-pam','value'),
    State('text-guides', 'value'),
    State('mms','value'),
    State('dna','value'),
    State('rna','value'),
    State('checkbox-gecko','checked'),
    State('checkbox-ref-comp', 'checked'),
    State('checklist-advanced', 'value'),
    State('example-email','value'),
    State('tabs','active_tab'),
    State('text-sequence','value'),
    State('len-guide-sequence-ver', 'value')]
)
def changeUrl(n, href, genome_selected, pam, text_guides, mms, dna, rna, gecko_opt, genome_ref_opt, adv_opts,dest_email, active_tab, text_sequence, len_guide_sequence):      #NOTE startJob
    '''
    genome_selected can be Human genome (hg19), or Human Genome (hg19) + 1000 Genome Project, the '+' character defines the ref or enr version.
    Note that pam parameter can be 5'-NGG-3', but the corresponding filename is 5'-NGG-3'.txt
    Pam file (5'-NGG-3'.txt) is structured as NGG 3, or TTTN -4. The created pam.txt inside the result directory add the corresponding N's
    Annotations path file is named genome_name_annotationpath.txt, where genome_name is the reference genome name

    La funzione crea una cartella dal nome random per identificare il job, controlla che opzioni sono state aggiunte e salva il contatto della mail.
    Estrae i parametri dati in input per poterli utilizzare con crispritz. Salva un file Params.txt con i parametri della ricerca. Controlla poi se 
    un'altra ricerca è stata fatta con gli stessi parametri e nel caso copia i risultati nella cartella di questo job.
    Fa partire lo script submit_job per eseguire crispritz.
    '''
    if n is None:
        raise PreventUpdate
    
    #Check input, else give simple input
    if genome_selected is None or genome_selected is '':
        genome_selected = 'hg19_ref'
    if pam is None or pam is '':
        pam = '5\'-NGG-3\''
    if text_guides is None or text_guides is '':
        text_guides = 'GAGTCCGAGCAGAAGAAGAA\nCCATCGGTGGCCGTTTGCCC'
    else:
        text_guides = text_guides.strip()
        if len(text_guides.split('\n')) > 1000:
            text_guides = '\n'.join(text_guides.split('\n')[:1000]).strip()
        if ( not all(len(elem) == len(text_guides.split('\n')[0]) for elem in text_guides.split('\n'))):
            text_guides = selectSameLenGuides(text_guides)
    if (len_guide_sequence is None or str(len_guide_sequence) is '') and ('sequence-tab' in active_tab):
        len_guide_sequence = 20
    if (text_sequence is None or text_sequence is '') and ('sequence-tab' in active_tab):
        text_sequence = '>sequence\nTACCCCAAACGCGGAGGCGCCTCGGGAAGGCGAGGTGGGCAAGTTCAATGCCAAGCGTGACGGGGGA'
    n_it = 10
    len_id = 10
    for i in range(n_it):
        assigned_ids = [o for o in os.listdir('Results/') if os.path.isdir(os.path.join('Results/',o))]
        job_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = len_id))
        if job_id not in assigned_ids:
            break
        if i > 7:
            i = 0
            len_id += 1 
            if len_id > 20:
                break
    result_dir = 'Results/' + job_id
    subprocess.run(['mkdir ' + result_dir], shell = True)
    
    search_index = True
    search = True
    annotation = True
    report =  True
    gecko_comp = False
    ref_comparison = False
    send_email = False
    if adv_opts is None:
        adv_opts = []
    if gecko_opt:
        gecko_comp = True
    if genome_ref_opt:
        ref_comparison = True
    if 'email' in adv_opts and dest_email is not None and len(dest_email.split('@')) > 1 and dest_email.split('@')[-1] is not '':
        send_email = True
        with open(result_dir + '/email.txt', 'w') as e:
            e.write(dest_email + '\n')
            e.write(URL + '/load?job=' + job_id + '\n')
            e.write(datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S") + '\n')
            e.write('Job done. Parameters: etc etc')
            e.close()
    
    
    #Set parameters
    genome_selected = genome_selected.replace(' ', '_')
    genome_ref = genome_selected.split('+')[0]              #+ char to separate ref and vcf, eg Human_genome+1000_genome_project
    if genome_ref == genome_selected:
        ref_comparison = False
    #NOTE Indexed genomes names are PAM + _ + bMax + _ + genome_selected
    
    pam_len = 0
    custom_pam = None

    with open('pam/' + pam + '.txt') as pam_file:
        pam_char = pam_file.readline()
        index_pam_value = pam_char.split(' ')[-1]
        if int(pam_char.split(' ')[-1]) < 0:
            end_idx = int(pam_char.split(' ')[-1]) * (-1)
            pam_char = pam_char.split(' ')[0][0 : end_idx]
            pam_len = end_idx
            pam_begin = True
        else:
            end_idx = int(pam_char.split(' ')[-1])
            pam_char = pam_char.split(' ')[0][end_idx * (-1):]
            pam_len = end_idx
            pam_begin = False
    
    if 'sequence-tab' in active_tab:
        #Extract sequence and create the guides
        guides = []
        for name_and_seq in text_sequence.split('>'):
            if '' == name_and_seq:
                continue
            name, seq = name_and_seq.strip().split('\n')    #TODO rimuovere spazi o \n interni alla sequenza, rimuovere caratteri strani
            if 'chr' in seq:
                extracted_seq = extract_seq.extractSequence(name, seq, genome_selected.replace(' ', '_'))
            else:
                extracted_seq = seq.strip()
            guides.extend(convert_pam.getGuides(extracted_seq, pam_char, len_guide_sequence))
            text_guides = '\n'.join(guides).strip()
    

    len_guides = len(text_guides.split('\n')[0])
    if (pam_begin):
        pam_to_file = pam_char + ('N' * len_guides) + ' ' + index_pam_value
    else:
        pam_to_file = ('N' * len_guides) + pam_char + ' ' + index_pam_value

    save_pam_file = open(result_dir + '/pam.txt', 'w')
    save_pam_file.write(pam_to_file)
    save_pam_file.close()
    pam = result_dir + '/pam.txt'
        
    guides_file = result_dir + '/guides.txt'
    if text_guides is not None and text_guides is not '':
        save_guides_file = open(result_dir + '/guides.txt', 'w')
        if (pam_begin):
            text_guides = 'N' * pam_len + text_guides.replace('\n', '\n' + 'N' * pam_len)
        else:
            text_guides = text_guides.replace('\n', 'N' * pam_len + '\n') + 'N' * pam_len
        save_guides_file.write(text_guides)
        save_guides_file.close()     

    if (int(dna) == 0 and int(rna) == 0):
        search_index = False
    max_bulges = rna
    if (int(dna) > int(rna)):
        max_bulges = dna

    if (search_index):
        search = False

    
    
    genome_idx = pam_char + '_' + '5' + '_' + genome_selected   #TODO CUSTOM: modificare per la versione UI offline
    genome_idx_ref = genome_idx.split('+')[0]

    #Create Params.txt file
    with open(result_dir + '/Params.txt', 'w') as p:            #NOTE if modified, chenge also mms value in update_table function
        p.write('Genome_selected\t' + genome_selected + '\n')         
        p.write('Genome_ref\t' + genome_ref + '\n')
        if search_index:
            p.write('Genome_idx\t' + genome_idx + '\n')
        else:
            p.write('Genome_idx\t' + 'None\n')
        p.write('Pam\t' + pam_char + '\n')
        p.write('Max_bulges\t' + str(max_bulges) + '\n')
        p.write('Mismatches\t' + str(mms) + '\n')
        p.write('DNA\t' + str(dna) + '\n')
        p.write('RNA\t' + str(rna) + '\n')
        p.write('Gecko\t' + str(gecko_comp) + '\n')
        p.write('Ref_comp\t' + str(ref_comparison) + '\n')
        p.close()

    #Check if input parameters (mms, bulges, pam, guides, genome) are the same as a previous search     #TODO per migliorare, semplicemente modificare il job id in quello della cartella con i ris già fatti
    all_result_dirs = [f for f in listdir('Results') if isdir(join('Results', f))]
    all_result_dirs.remove(job_id)
    #all_result_dirs.remove('test')
    for check_param_dir in all_result_dirs:
        if os.path.exists('Results/' + check_param_dir + '/Params.txt'):
            if os.path.exists('Results/' + check_param_dir + '/log.txt'):
                with open('Results/' + check_param_dir + '/log.txt') as log:
                    if ('Job\tDone' in log.read()):
                        if (filecmp.cmp('Results/' + check_param_dir + '/Params.txt', result_dir + '/Params.txt' )):
                                guides1 = open('Results/' + check_param_dir + '/guides.txt').read().split('\n')
                                guides2 = open('Results/' + job_id + '/guides.txt').read().split('\n')
                                if (collections.Counter(guides1) == collections.Counter(guides2)):
                                    search = False
                                    search_index = False
                                    subprocess.run(['cp $PWD/Results/' + check_param_dir + '/' + check_param_dir + '* ' + result_dir + '/'], shell = True)
                                    subprocess.run(['cp $PWD/Results/' + check_param_dir + '/*.png ' + result_dir + '/'], shell = True)
                                    subprocess.run(['rename \'s/' + check_param_dir + '/' + job_id + '/g\' ' + result_dir + '/*'], shell = True)
                                    break           
    
    #Annotation
    if (not search and not search_index):
        annotation = False      

    #Generate report
    if (not search and not search_index):
        report = False         
    
    #TODO aggiungere annotazioni per ogni genoma
    annotation_file = [f for f in listdir('annotations/') if isfile(join('annotations/', f)) and f.startswith(genome_ref)]

    genome_type = 'ref'     #Indicates if search is 'ref', 'var' or 'both'
    if '+' in genome_selected:
        genome_type = 'var'
    if ref_comparison:
        genome_type = 'both'
    subprocess.Popen(['assets/./submit_job.sh ' + 'Results/' + job_id + ' ' + 'Genomes/' + genome_selected + ' ' + 'Genomes/' + genome_ref + ' ' + 'genome_library/' + genome_idx + (
        ' ' + pam + ' ' + guides_file + ' ' + str(mms) + ' ' + str(dna) + ' ' + str(rna) + ' ' + str(search_index) + ' ' + str(search) + ' ' + str(annotation) + (
            ' ' + str(report) + ' ' + str(gecko_comp) + ' ' + str(ref_comparison) + ' ' + 'genome_library/' + genome_idx_ref + ' ' + str(send_email) + ' ' + 'annotations/' + annotation_file[0] + 
            ' ' + genome_type
        )
    )], shell = True)
    return '/load','?job=' + job_id

#When url changed, load new page
@app.callback(
    [Output('page-content', 'children'),
    Output('job-link', 'children')],
    [Input('url', 'href'), Input('url','pathname'), Input('url','search')],[State('url','hash')]
    # [State('url','pathname'), 
    # State('url','search')]
)
def changePage( href, path, search, hash_guide):
    '''
    Controllo della pagina da mostrare in base all'url
    '''
    # print('href', href)
    # print('hash', hash_guide)
    # print('pathname', path)
    # print('search', search)
    #print('hash', hash_guide)
    if path == '/load':
        return load_page, URL + '/load' + search 
    if path == '/result':
        job_id = search.split('=')[-1]
        if hash_guide is None or hash_guide is '':
            return resultPage(job_id), URL + '/load' + search
        if 'new' in hash_guide:         #TODO cambiare nome alla pagina delle guide
            return guidePagev3(job_id, hash_guide.split('#')[1]), URL + '/load' + search
        if '-Sample-' in hash_guide:   
            return samplePage(job_id, hash_guide.split('#')[1]), URL + '/load' + search
        if '-Pos-' in hash_guide:
            return clusterPage(job_id, hash_guide.split('#')[1]), URL + '/load' + search
        return resultPage(job_id), URL + '/load' + search
    if path == '/test-page':
        return test_page, URL + '/load' + search
    if path == '/test-page2':
        return test_page2, URL + '/load' + search
    if path == '/test-page3':
        return test_page3, URL + '/load' + search
   
    return index_page, ''

#Check end job
@app.callback(
    [Output('view-results', 'style'),
    Output('annotate-result-status', 'children'),
    Output('search-status', 'children'),
    Output('generate-report-status', 'children'),
    Output('post-process-status', 'children'),
    Output('view-results','href'),
    Output('no-directory-error', 'children')],
    [Input('load-page-check', 'n_intervals')],
    [State('url', 'search')]
)
def refreshSearch(n, dir_name):
    '''
    Il componente Interval chiama questa funzione ogni 3 secondi. Essa controlla lo stato del lavoro e aggiorna la pagina se una parte del lavoro
    è stata fatta.
    Quando la ricerca è finita, visualizza un link per passare alla pagina dei risultati
    Se il job non esiste, ritorna un avviso di errore
    TODO sarebbe più comodo che automaticamente la pagina si reindirizzi ai risultati quando il job è fatto

    '''
    if n is None:
        raise PreventUpdate    
    
    onlydir = [f for f in listdir('Results') if isdir(join('Results', f))]
    current_job_dir = 'Results/' +  dir_name.split('=')[-1] + '/'
    if dir_name.split('=')[-1] in onlydir:
        onlyfile = [f for f in listdir(current_job_dir) if isfile(join(current_job_dir, f))]
        with open(current_job_dir + 'guides.txt') as guides:
            n_guides = len(guides.read().strip().split('\n'))
        if 'log.txt' in onlyfile:
            with open(current_job_dir + 'log.txt') as log:
                all_done = 0
                annotate_res_status = html.P('To do', style = {'color':'red'})
                search_status = html.P('To do', style = {'color':'red'})
                report_status = html.P('To do', style = {'color':'red'})
                post_process_status = html.P('To do', style = {'color':'red'})
                current_log = log.read()
                if ('Annotation\tDone' in current_log):
                    annotate_res_status = html.P('Done', style = {'color':'green'})
                    all_done = all_done + 1
                elif os.path.exists(current_job_dir + 'output.txt'):                #Extract % of search done
                    with open(current_job_dir + 'output.txt', 'r') as output_status:
                        line = output_status.read().strip()
                        if 'Annotate_output' in line:
                            if 'both' in line:
                                last_percent = line.rfind('%')
                                if last_percent > 0:
                                    last_percent = line[line[:last_percent].rfind(' '): last_percent]
                                    status_message = last_percent + '%'
                                else:
                                    status_message = 'Annotating...'

                                steps = 'Step [1/2]'
                                if 'Annotate_output_ref' in line:
                                    steps = 'Step [2/2]'
                            else:
                                last_percent = line.rfind('%')
                                if last_percent > 0:
                                    last_percent = line[line[:last_percent].rfind(' '): last_percent]
                                    status_message = last_percent + '%'
                                else:
                                    status_message = 'Annotating...'
                                steps = ''
                            annotate_res_status = html.P(status_message + ' ' + steps, style = {'color':'orange'})

                if ('Search-index\tDone' in current_log and 'Search\tDone' in current_log):
                    search_status = html.P('Done', style = {'color':'green'})
                    all_done = all_done + 1
                elif os.path.exists(current_job_dir + 'output.txt'):                #Extract % of search done 
                    with open(current_job_dir + 'output.txt', 'r') as output_status:
                        line = output_status.read().strip()
                        if 'Search_output' in line:
                            if 'both' in line:
                                last_percent = line.rfind('%')
                                if last_percent > 0:
                                    last_percent = line[line[:last_percent].rfind(' '): last_percent]
                                    search_status_message = last_percent + '%'
                                else:
                                    search_status_message = 'Searching...'

                                steps = 'Step [1/2]'
                                if 'Search_output_ref' in line:
                                    steps = 'Step [2/2]'
                                
                                
                            else:
                                last_percent = line.rfind('%')
                                if last_percent > 0:
                                    last_percent = line[line[:last_percent].rfind(' '): last_percent]
                                    search_status_message = last_percent + '%'
                                else:
                                    search_status_message = 'Searching...'
                                steps = ''
                            search_status = html.P(search_status_message + ' ' + steps, style = {'color':'orange'})

                if ('Report\tDone' in current_log):
                    report_status = html.P('Done', style = {'color':'green'})
                    all_done = all_done + 1
                elif os.path.exists(current_job_dir + 'output.txt'):                #Extract % of search done
                    with open(current_job_dir + 'output.txt', 'r') as output_status:
                        line = output_status.read().strip()
                        if 'Generate_report' in line:
                            status_message = round((len(line.split('\n')) - 1) / n_guides, 2)
                            report_status = html.P(str(status_message * 100) + '%', style = {'color':'orange'})
                #TODO continuare con post process
                if ('PostProcess\tDone' in current_log):
                    post_process_status = html.P('Done', style = {'color':'green'})
                    all_done = all_done + 1
                if all_done == 4 or 'Job\tDone' in current_log:
                    return {'visibility':'visible'}, annotate_res_status, search_status, report_status, post_process_status ,'/result?job=' + dir_name.split('=')[-1], ''
                else:
                    return {'visibility':'hidden'}, annotate_res_status, search_status, report_status, post_process_status,'', ''
    return {'visibility':'hidden'}, html.P('Not available', style = {'color':'red'}), html.P('Not available', style = {'color':'red'}), html.P('Not available', style = {'color':'red'}), html.P('Not available', style = {'color':'red'}) ,'', dbc.Alert("The selected result does not exist", color = "danger")

#Perform expensive loading of a dataframe and save result into 'global store'
#Cache are in the Cache directory
@cache.memoize()
def global_store(value):
    '''
    Caching dei file targets per una miglior performance di visualizzazione
    '''
    if value is None:
        return ''
    target = [f for f in listdir('Results/' + value) if isfile(join('Results/'+value, f)) and f.endswith('scores.txt') ]
    if not target:
        target = [f for f in listdir('Results/' + value) if isfile(join('Results/'+value, f)) and f.endswith('targets.txt') ]
    
    df = pd.read_csv('Results/' +value + '/' + target[0], sep = '\t')
    df.rename(columns = {"#Bulge type":'BulgeType', '#Bulge_type':'BulgeType','Bulge Size': 'BulgeSize', 'Bulge_Size': 'BulgeSize', 'Doench 2016':'Doench2016','Doench_2016':'Doench2016'}, inplace = True)
    return df

# #Callback to populate the tab, note that it's called when the result_page is loaded (dash implementation), so we do not use raise update to block this first callback
# @app.callback(
#     [Output('signal','children'),
#     Output('result-table','page_current'),
#     Output('result-table', "sort_by"), 
#     Output('result-table','filter_query')],
#     [Input('url', 'pathname')],
#     [State('url', 'search')]
# )
# def populateTable(pathname, search):
#     print('pathname', pathname)
#     if pathname != '/result':
#         raise PreventUpdate

#     job_id = search.split('=')[-1]
#     job_directory = 'Results/' + job_id + '/'
#     print('job dir', job_directory)
#     if(not isdir(job_directory)):
#         return 'not_exists', 0, [], ''
#     #global_store(job_id)
#     print('ok')
#     return job_id, 0, [], ''

#Send the data when next or prev button is clicked on the result table
@app.callback(
    Output('result-table', 'data'),
    [Input('result-table', "page_current"),
     Input('result-table', "page_size"),
     Input('result-table', "sort_by"),
     Input('result-table', 'filter_query')],
     [State('url', 'search'),
     State('url', 'hash')]
)
def update_table(page_current, page_size, sort_by, filter, search, hash_guide):
    '''
    La funzione ritorna uno split dei risultati in base ad un filtering o a un sort da parte dell'utente. Inoltre aggiorna i risultati
    visualizzati quando il bottone next page / prev page è cliccato. (Codice preso dalla pagina dash datatable sul sorting con python)
    Inoltre carica i file targets, o scores se presente, e lo trasforma in un dataframe, cambiando il nome delle colonne per farle corrispondere
    all'id delle colonne della tabella nella pagina.
    Se non ci sono targets ritorna un avviso di errore
    '''
    job_id = search.split('=')[-1]
    job_directory = 'Results/' + job_id + '/'
    guide = hash_guide.split('#')[1]
    value = job_id
    if search is None:
        raise PreventUpdate

    filtering_expressions = filter.split(' && ')
    #filtering_expressions.append(['{crRNA} = ' + guide])     
    df = global_store(value)
    dff = df[df['crRNA'] == guide]
    print('len index before', len(dff.index))
    sort_by.insert(0, {'column_id' : 'Mismatches', 'direction': 'asc'})
    sort_by.insert(1, {'column_id' : 'BulgeSize', 'direction': 'asc'})
    #sort_by.insert(2, {'column_id': 'CFD', 'direction':'desc'})
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)].sort_values([col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False)
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    print('len index after', len(dff.index))
    #NOTE sort_by: [{'column_id': 'BulgeType', 'direction': 'asc'}, {'column_id': 'crRNA', 'direction': 'asc'}]
    #sort_by.insert(0, {'column_id' : 'Mismatches', 'direction': 'asc'})
    #sort_by.insert(0, {'column_id' : 'BulgeSize', 'direction': 'asc'})
    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )

    #Check if results are not 0
    warning_no_res = ''
    with open(job_directory + job_id + '.targets.txt') as t:
        no_result = False
        t.readline()
        last_line = t.readline()
        if (last_line is '' or last_line is '\n'):
            no_result = True

    if (no_result):
        warning_no_res = dbc.Alert("No results were found with the given parameters", color = "warning")

     
    return dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')


#For filtering
def split_filter_part(filter_part):
    '''
    Preso dal sito di dash sul filtering datatables con python
    '''
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


#Read the uploaded file and converts into bit
def parse_contents(contents):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    return decoded

#Load the table/children under the tab value
@app.callback(
    Output('div-tab-content', 'children'),
    [Input('tabs-reports', 'value'),
    Input('general-profile-table','selected_cells')],
    [State('general-profile-table', 'data'),
    State('url', 'search'),
    State('div-genome-type', 'children')]
)
def updateContentTab(value, sel_cel, all_guides, search, genome_type):
    if value is None or sel_cel is None or not sel_cel or not all_guides:
        raise PreventUpdate
    
    guide = all_guides[int(sel_cel[0]['row'])]['Guide']
    job_id = search.split('=')[-1]
    job_directory = 'Results/' + job_id + '/'

    with open('Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        mms = (next(s for s in all_params.split('\n') if 'Mismatches' in s)).split('\t')[-1]
        genome_selected = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        max_bulges = (next(s for s in all_params.split('\n') if 'Max_bulges' in s)).split('\t')[-1]

    fl = []
    fl.append(html.Br())
    fl.append(html.H5('Focus on: ' + guide))

    if value == 'tab-summary-by-guide':
        #Show Summary by Guide table
       
        df = pd.read_pickle(job_directory + job_id + '.summary_by_guide.' + guide + '.txt')
        
        df.drop( df[(df['Bulge Size'] == 0) & ((df['Bulge Type'] == 'DNA') | ((df['Bulge Type'] == 'RNA'))) | (df['Number of targets'] == 0)  ].index, inplace = True)
        more_info_col = []
        total_col = []
        for i in range(df.shape[0]):
            more_info_col.append('Show Targets')
            total_col.append(df['Bulge Size'])
        df[''] = more_info_col
        df['Total'] = df['Bulge Size'] + df['Mismatches']
        if genome_type == 'both':
            df = df.sort_values(['Total', 'Targets created by SNPs'], ascending = [True, False])
        else:
            df = df.sort_values('Total', ascending = True)
        del df['Total']
        #print (df)
        fl.append(html.Div(
                generate_table(df, 'table-summary-by-guide', guide, job_id ), style = {'text-align': 'center'}
            )
        )
        return fl
    elif value == 'tab-summary-by-sample':
        #Show Summary by Sample table
        if genome_type == 'both':
            col_names_sample = ['Sample', 'Gender', 'Population', 'Super Population',  'Number of targets', 'Targets in Sample', 'Total Targets in Population', 'Total targets in Super Population']
            df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
            df = df.sort_values('Targets in Sample', ascending = False)
            df.drop(['Number of targets'], axis = 1, inplace = True)
        else:
            col_names_sample = ['Sample', 'Gender', 'Population', 'Super Population',  'Number of targets', 'Total Targets in Population', 'Total targets in Super Population']
            df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
            df = df.sort_values('Number of targets', ascending = False)
        more_info_col = []
        for i in range(df.shape[0]):
            more_info_col.append('Show Targets')
        df[''] = more_info_col
        
        #TODO if genoma selezionato è hg19/38, con varianti, allora aggiungo queste pop (se per esempio seleziono mouse, devo mettere i ceppi)
        super_populations = [{'label':i, 'value':i} for i in population_1000gp.keys()]
        populations = []
        for k in population_1000gp.keys():
            for i in population_1000gp[k]:
                populations.append({'label':i, 'value':i})
        fl.append(
            html.Div
                (
                    [
                        dbc.Row(
                            [
                                dbc.Col(html.Div(dcc.Dropdown(options = super_populations, id = 'dropdown-superpopulation-sample', placeholder = 'Select a Super Population'))),
                                dbc.Col(html.Div(dcc.Dropdown(options = populations, id = 'dropdown-population-sample', placeholder = 'Select a Population'))),
                                dbc.Col(html.Div(html.Button('Filter', id = 'button-filter-population-sample')))
                            ]
                        ),
                    ],
                    style = {'width':'50%'}
                )
        )
        fl.append(html.Div('None,None',id = 'div-sample-filter-query', style = {'display':'none'})) #Folr keep current filter:  Superpop,Pop
        fl.append(html.Div(
                generate_table_samples(df, 'table-samples', 1, guide, job_id ), style = {'text-align': 'center'}, id = 'div-table-samples'
            )
        )
        fl.append(
            html.Div(
                [
                    html.Button('Prev', id = 'prev-page-sample'),
                    html.Button('Next', id = 'next-page-sample')
                ],
                style = {'text-align': 'center'}
            )
        )
        fl.append(html.Div('1', id= 'div-current-page-table-samples'))
        return fl
    elif value == 'tab-summary-by-position':
        #Show Summary by position table

        #Dropdown chromosomes
        try:
            onlyfile = [f for f in listdir('Genomes/' + genome_selected) if (isfile(join('Genomes/' + genome_selected, f)) and (f.endswith('.fa') or f.endswith('.fasta')))]
        except:
            onlyfile = ['chr' + str(i) + '.fa' for i in range(1,23)]
            onlyfile.append('chrX.fa')
            onlyfile.append('chrY.fa')                                              #NOTE in case no chr in GENOMES/ i put 22 chr + X Y M
            onlyfile.append('chrM.fa')
        onlyfile = [x[:x.rfind('.')] for x in onlyfile]            #removed .fa for better visualization
        chr_file = []
        chr_file_unset = []
        for chr_name in onlyfile:
            chr_name = chr_name.replace('.enriched', '')
            if '_' in chr_name:
                chr_file_unset.append(chr_name)
            else:
                chr_file.append(chr_name)
        chr_file.sort(key = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)])
        chr_file_unset.sort(key = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)])
        chr_file += chr_file_unset
        chr_file = [{'label': chr_name, 'value' : chr_name} for chr_name in chr_file]
        
        # Colonne tabella: chr, pos, target migliore, min mm, min bulges, num target per ogni categoria di mm e bulge, show targets; ordine per total, poi mm e poi bulge
        start_time = time.time()
        df = pd.read_csv( job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t', nrows = 100)   
        df.rename(columns = {'#Chromosome':'Chromosome'}, inplace = True)
        more_info_col = []
        for i in range(df.shape[0]):
            more_info_col.append('Show Targets')
        df[''] = more_info_col
        #TODO inserire failsafe se non ci sono chr, esempio elenco chr da 1 a 22
        fl.append(
            html.Div
                (
                    [
                        dbc.Row(
                            [
                                dbc.Col(html.Div(dcc.Dropdown(options = chr_file, id = 'dropdown-chr-table-position', placeholder = 'Select a chromosome'))),
                                dbc.Col(html.Div(dcc.Input(placeholder = 'Start Position', id = 'input-position-start'))),
                                dbc.Col(html.Div(dcc.Input(placeholder = 'End Position', id = 'input-position-end'))),
                                dbc.Col(html.Div(html.Button('Filter', id = 'button-filter-position')))
                            ]
                        ),
                    ],
                    style = {'width':'50%'}
                )
        )
        # print('Position dataframe ready', time.time() - start_time)
        fl.append(html.Div('None,None,None',id = 'div-position-filter-query', style = {'display':'none'})) #Folr keep current filter:  chr,pos_start,pos_end
        start_time = time.time()
        fl.append(html.Div(
                generate_table_position(df, 'table-position', 1 , int(mms), int(max_bulges), guide, job_id ), style = {'text-align': 'center'}, id = 'div-table-position'
            )
        )
        # print('Position table ready', time.time() - start_time)
        fl.append(
            html.Div(
                [
                    html.Button('Prev', id = 'prev-page-position'),
                    html.Button('Next', id = 'next-page-position')
                ],
                style = {'text-align': 'center'}
            )
        )

        fl.append(html.Div('1', id= 'div-current-page-table-position'))
        fl.append(html.Div(mms + '-' + max_bulges, id = 'div-mms-bulges-position', style = {'display':'none'}))
        return fl
    else:
        #Show Report images
        fl = []
        fl.append(html.Br())
        fl.append(html.P('Select a mismatch value'))
        fl_buttons = []
        for i in range (10):
            if (i <= int(mms)):
                fl_buttons.append(
                    html.Button(str(i) + ' mm',id = 'btn' + str(i)),       
                )
            else:
                fl_buttons.append(
                    html.Button(str(i) + ' mm',id = 'btn' + str(i), style = {'display':'none'}),       
                )
        fl.append(html.Br())

        radar_img = 'summary_single_guide_' + guide + '_' + str(0) + 'mm.png' #TODO choose between 0 mm and max used mms

        barplot_img = 'summary_histogram_' + guide + '_' + str(0) + 'mm.png'
        try:            #NOTE serve per non generare errori se il barplot non è stato fatto
            barplot_src = 'data:image/png;base64,{}'.format(base64.b64encode(open('Results/' + job_id + '/' + barplot_img, 'rb').read()).decode())
        except:
            barplot_src = ''
        try:
            barplot_href = 'assets/Img/' + job_id + '/' + barplot_img
        except:
            barplot_href = ''

        try:
            radar_src = 'data:image/png;base64,{}'.format(base64.b64encode(open('Results/' + job_id + '/' + radar_img, 'rb').read()).decode())
        except:
            radar_src = ''
        try:
            radar_href = 'assets/Img/' + job_id + '/' + radar_img
        except:
            radar_href = ''
        #TODO if genoma selezionato è hg19/38, con varianti, allora aggiungo queste pop (se per esempio seleziono mouse, devo mettere i ceppi)
        #TODO inserire un messaggio che se la ricerca è fatta sul ref, non si possono vedere le immagini coi samples
        super_populations = [{'label':i, 'value':i} for i in population_1000gp.keys()]
        populations = []
        for k in population_1000gp.keys():
            for i in population_1000gp[k]:
                populations.append({'label':i, 'value':i})
        fl.append(
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col([    #Guide part
                                
                                dbc.Row(
                                    dbc.Col(
                                        html.Div(fl_buttons)
                                    )
                                ),
                                html.Div(
                                    [

                                        dbc.Row(html.Br()),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.A(
                                                        html.Img(src = radar_src, id = 'barplot-img-guide', width="100%", height="auto"),
                                                        target="_blank",
                                                        href = radar_href
                                                    ),
                                                    width = 10
                                                )
                                            ]
                                        ),
                                        dbc.Row(html.Br()),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.A(
                                                        html.Img(src = barplot_src,id = 'radar-img-guide', width="100%", height="auto"),
                                                        target="_blank",
                                                        href = barplot_href
                                                    ),
                                                    width = 10
                                                )
                                            ]
                                        )
                                        
                                    ],
                                    id = 'div-guide-image'
                                )
                            ]),
                            dbc.Col([    #Sample part
                                
                                dbc.Row(
                                    [
                                        dbc.Col(html.Div(dcc.Dropdown(options = super_populations, id = 'dropdown-superpopulation-sample', placeholder = 'Select a Super Population'))),
                                        dbc.Col(html.Div(dcc.Dropdown(options = populations, id = 'dropdown-population-sample', placeholder = 'Select a Population'))),
                                        dbc.Col(html.Div(dcc.Dropdown( id = 'dropdown-sample', placeholder = 'Select a Sample'))),
                                    ]   #NOTE sample presenti solo se seleziono la pop
                                ),
                                html.Div(
                                    [
                                    #     dbc.Row(html.Br()),
                                    #     dbc.Row(
                                    #         [
                                    #             dbc.Col(
                                    #                 html.A(
                                    #                     html.Img(src = radar_src, id = 'barplot-img-sample', width="100%", height="auto"),
                                    #                     target="_blank",
                                    #                     href = radar_href
                                    #                 ),
                                    #                 width = 10
                                    #             ),
                                    #             dbc.Col(
                                    #                 [
                                    #                     html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('sample_img.png', 'rb').read()).decode())),
                                    #                     html.P('SAmple X', id = 'sample-name-testpage3')
                                    #                 ],
                                    #                 align="center"
                                    #             )
                                    #         ],
                                    #         no_gutters=True 
                                    #     ),
                                    #     dbc.Row(html.Br()),
                                    #     dbc.Row(
                                    #         [
                                    #             dbc.Col(
                                    #                 html.A(
                                    #                     html.Img(src = barplot_src,id = 'barplot-img-pop', width="75%", height="auto"),
                                    #                     target="_blank",
                                    #                     href = barplot_href
                                    #                 )
                                    #             )
                                    #         ]
                                    #     )
                                    ],
                                    id = 'div-sample-image'
                                )
                            ])
                        ]
                    )
                ]
            )
        )
        
        fl.append(html.Br())
        fl.append(html.Br())
        return fl
    # guide = all_guides[int(sel_cel[0]['row'])]['State']
        # return guide + value
    raise PreventUpdate



#Select figures on mms value, sample value
@app.callback(
    [Output('div-guide-image', 'children'),
    Output('div-sample-image', 'children')],
    [Input('btn0', 'n_clicks_timestamp'),
    Input('btn1', 'n_clicks_timestamp'),
    Input('btn2', 'n_clicks_timestamp'),
    Input('btn3', 'n_clicks_timestamp'),
    Input('btn4', 'n_clicks_timestamp'),
    Input('btn5', 'n_clicks_timestamp'),
    Input('btn6', 'n_clicks_timestamp'),
    Input('btn7', 'n_clicks_timestamp'),
    Input('btn8', 'n_clicks_timestamp'),
    Input('btn9', 'n_clicks_timestamp'),
    Input('dropdown-superpopulation-sample', 'value'),
    Input('dropdown-population-sample', 'value'),
    Input('dropdown-sample', 'value'),
    Input('general-profile-table', 'selected_cells')],
    [State('url', 'search'),
    State('general-profile-table', 'data')]
)
def updateImagesTabs(n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, superpopulation, population, sample, sel_cel, search, all_guides):
    if sel_cel is None :
        raise PreventUpdate
    job_id = search.split('=')[-1]
    job_directory = 'Results/' + job_id + '/'
    guide = all_guides[int(sel_cel[0]['row'])]['Guide']
    
    #search for getting job id
    # get guide with sel_cel and all_data
    guide_images = []
    sample_images = []
    
    if not n0:
        n0 = 0
    if not n1:
        n1 = 0
    if not n2:
        n2 = 0
    if not n3:
        n3 = 0
    if not n4:
        n4 = 0
    if not n5:
        n5 = 0
    if not n6:
        n6 = 0
    if not n7:
        n7 = 0
    if not n8:
        n8 = 0
    if not n9:
        n9 = 0
    btn_group = []
    btn_group.append(n0)
    btn_group.append(n1)
    btn_group.append(n2)
    btn_group.append(n3)
    btn_group.append(n4)
    btn_group.append(n5)
    btn_group.append(n6)
    btn_group.append(n7)
    btn_group.append(n8)
    btn_group.append(n9)
    
    if max(btn_group) == n0:
        mm_show = 0
    if max(btn_group) == n1:
        mm_show = 1
    if max(btn_group) == n2:
        mm_show = 2
    if max(btn_group) == n3:
        mm_show = 3
    if max(btn_group) == n4:
        mm_show = 4
    if max(btn_group) == n5:
        mm_show = 5
    if max(btn_group) == n6:
        mm_show = 6
    if max(btn_group) == n7:
        mm_show = 7
    if max(btn_group) == n8:
        mm_show = 8
    if max(btn_group) == n9:
        mm_show = 9
    if max(btn_group) == 0:
        mm_show = 0
    radar_img = 'summary_single_guide_' + guide + '_' + str(mm_show) + 'mm.png'

    barplot_img = 'summary_histogram_' + guide + '_' + str(mm_show) + 'mm.png'
    try:            #NOTE serve per non generare errori se il barplot non è stato fatto
        barplot_src = 'data:image/png;base64,{}'.format(base64.b64encode(open('Results/' + job_id + '/' + barplot_img, 'rb').read()).decode())
    except:
        barplot_src = ''
    try:
        barplot_href = 'assets/Img/' + job_id + '/' + barplot_img
    except:
        barplot_href = ''

    try:
        radar_src = 'data:image/png;base64,{}'.format(base64.b64encode(open('Results/' + job_id + '/' + radar_img, 'rb').read()).decode())
    except:
        radar_src = ''
    try:
        radar_href = 'assets/Img/' + job_id + '/' + radar_img
    except:
        radar_href = ''
    
    guide_images.extend([
        
        dbc.Row(html.Br()),
        dbc.Row(
            [
                dbc.Col(
                    html.A(
                        html.Img(src = radar_src, id = 'radar-img-guide', width="100%", height="auto"),
                        target="_blank",
                        href = radar_href
                    ),
                    width = 10
                )
            ]
        ),
        dbc.Row(html.Br()),
        dbc.Row(
            [
                dbc.Col(
                    html.A(
                        html.Img(src = barplot_src,id = 'barplot-img-guide', width="100%", height="auto"),
                        target="_blank",
                        href = barplot_href
                    ),
                    width = 10
                )
            ]
        )
    ])
    class_images = [(sample, 'Samples'), (population, 'Population'), (superpopulation, 'Superpopulation')]
    
    for c in class_images:
        if c[0]:
            try:
                first_img_source = 'data:image/png;base64,{}'.format(base64.b64encode(open(job_directory + 'summary_single_guide_' + c[0] +'_' +str(mm_show) + 'mm.png', 'rb').read()).decode())
            except:
                #create image from annotation file of samples
                subprocess.call(['cd '+job_directory +'; ../../PostProcess/radar_chart_new.py ' + guide + ' ' + str(mm_show) + ' ' + job_id + '.sample_annotation.' + guide + 
                '.' + c[1].lower() + '.txt no no no -ws -sample ' + c[0]], shell = True)
                copy_img = subprocess.Popen(['cp ' + job_directory + 'summary_single_guide_' + c[0] +'_' + guide + '_' + str(mm_show) + 'mm.png assets/Img/' + job_id], shell = True)
                copy_img.wait() #BUG se metto il copia link, mi si ricarica la pagina, forse il problema non c'è se uso gnicorn
                first_img_source = 'data:image/png;base64,{}'.format(base64.b64encode(open(job_directory + 'summary_single_guide_' + c[0] +'_' + guide + '_' + str(mm_show) + 'mm.png', 'rb').read()).decode())
            try:
                first_img_href = 'assets/Img/' + job_id + '/' + 'summary_single_guide_' + c[0] +'_' + guide + '_' + str(mm_show) + 'mm.png'
            except:
                first_img_href = ''
            sample_images.append(dbc.Row(html.Br()))

            sample_images.append(
                dbc.Row(
                [
                    dbc.Col(
                        html.A(
                            html.Img(src = first_img_source, width="100%", height="auto"),
                            target="_blank",
                            href = first_img_href
                        ),
                        width = 10
                    ),
                ],
                no_gutters=True 
            ),
            )
    return guide_images, sample_images


def generate_table(dataframe, id_table, guide='', job_id='', max_rows=2600):
    '''
    Per generare una html table. NOTE è diversa da una dash dataTable
    '''
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns]) ] +
        # Body
        [html.Tr([
            html.Td(html.A(dataframe.iloc[i][col],  href = 'result?job=' + job_id + '#' + guide +'new' + dataframe.iloc[i]['Bulge Type'] + str(dataframe.iloc[i]['Bulge Size']) + str(dataframe.iloc[i]['Mismatches']) , target = '_blank' )) if col == '' else  html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))],
        style = {'display':'inline-block'},
        id = id_table
    )

def generate_table_samples(dataframe, id_table, page ,guide='', job_id='', max_rows=10):
    '''
    Per generare una html table. NOTE è diversa da una dash dataTable
    '''
    rows_remaining = len(dataframe) - (page - 1) * max_rows
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns]) ] +
        # Body
        [html.Tr([
            html.Td(html.A(dataframe.iloc[i + (page - 1)*max_rows][col],  href = 'result?job=' + job_id + '#' + guide +'-Sample-' + dataframe.iloc[i]['Sample'] , target = '_blank' )) if col == '' else  html.Td(dataframe.iloc[i + (page - 1)*max_rows][col]) for col in dataframe.columns
        ]) for i in range(min(rows_remaining, max_rows))],
        style = {'display':'inline-block'},
        id = id_table
    )

# def generate_table_position(dataframe, id_table, page, guide = '', job_id = '', max_rows = 10): #NOTE v1 della tabella posizioni
#     '''
#     Per generare una html table. NOTE è diversa da una dash dataTable
#     '''
#     rows_remaining = len(dataframe) - (page - 1) * max_rows
   
#     return html.Table(
#         # Header
#         [html.Tr([html.Th(col) for col in dataframe.columns]) ] +
#         # Body
#         [html.Tr([
#             html.Td(html.A(dataframe.iloc[i + (page - 1)*max_rows][col],  href = 'result?job=' + job_id + '#' + guide +'-Pos-' + str(dataframe.iloc[i + (page - 1)*max_rows]['Chromosome']) + '-' +  str(dataframe.iloc[i + (page - 1)*max_rows]['Position']) , target = '_blank' )) if col == '' else  html.Td(dataframe.iloc[i + (page - 1)*max_rows][col]) for col in dataframe.columns
#         ]) for i in range(min(rows_remaining, max_rows))],
#         style = {'display':'inline-block'},
#         id = id_table
#     )

def generate_table_position(dataframe, id_table, page, mms, bulges, guide = '', job_id = '', max_rows = 10): #NOTE v2 della tabella posizioni       #TODO modifica layout righe per allinearle
    rows_remaining = len(dataframe) - (page - 1) * max_rows
    header = [html.Tr([
        html.Th('Chromosome', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Position', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Best Target', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Min Mismatch', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Min Bulge', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Bulge', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Targets by mismatch value', colSpan = str(mms +1), style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('', rowSpan = '2'),
        ])
    ]
    mms_header = []
    for mm in range (mms +1):
        mms_header.append(html.Th(str(mm) + ' MM', style = {'vertical-align':'middle', 'text-align':'center'}))
    header.append(html.Tr(mms_header))
    
    data = []
    for i in range(min(rows_remaining, max_rows)):
        first_cells = [
            html.Td(dataframe.iloc[i + (page - 1)*max_rows]['Chromosome'], rowSpan = str(bulges +1),  style = {'vertical-align':'middle', 'text-align':'center'}),
            html.Td(dataframe.iloc[i + (page - 1)*max_rows]['Position'], rowSpan = str(bulges +1),  style = {'vertical-align':'middle', 'text-align':'center'}),
            html.Td(dataframe.iloc[i + (page - 1)*max_rows]['Best Target'], rowSpan = str(bulges+1),  style = {'vertical-align':'middle', 'text-align':'center'}),
            html.Td(dataframe.iloc[i + (page - 1)*max_rows]['Min Mismatch'], rowSpan = str(bulges+1),  style = {'vertical-align':'middle', 'text-align':'center'}),
            html.Td(dataframe.iloc[i + (page - 1)*max_rows]['Min Bulge'], rowSpan = str(bulges+1),  style = {'vertical-align':'middle', 'text-align':'center'}),
            html.Th('0 Bulge', style = {'vertical-align':'middle', 'text-align':'center', 'padding-left':'0'})
        ]
        
        mm_cells = [html.Td(dataframe.iloc[i + (page - 1)*max_rows][col], style = {'vertical-align':'middle', 'text-align':'center'}) for col in dataframe.columns[5:5+mms+1]]
        data.append(html.Tr(first_cells + mm_cells + [html.Td(
                html.A('Show Targets',  href = 'result?job=' + job_id + '#' + guide +'-Pos-' + str(dataframe.iloc[i + (page - 1)*max_rows]['Chromosome']) + '-' +  str(dataframe.iloc[i + (page - 1)*max_rows]['Position']) , target = '_blank'), 
                rowSpan = str(bulges+1), style = {'vertical-align':'middle', 'text-align':'center'})
            ]))
        for b in range (bulges):
            data.append(
                html.Tr(
                    [html.Th(str(b +1) + ' Bulge', style = {'vertical-align':'middle', 'text-align':'center'} )]
                    +
                    [html.Td(dataframe.iloc[i + (page - 1)*max_rows][col]) for col in dataframe.columns[5 + (b +1) *(mms +1) : 5 + (b +1) *(mms+1) + mms +1]]
                )
            )
    
    return html.Table(header + data, style = {'display':'inline-block'}, id = id_table)


#Callback to update the population tab based on superpopulation selected
@app.callback(
    [Output('dropdown-population-sample', 'options'),
    Output('dropdown-population-sample', 'value')],
    [Input('dropdown-superpopulation-sample', 'value')]
)
def updatePopulationDrop(superpop):
    if superpop is None or superpop is '':
        raise PreventUpdate
    return [{'label':i, 'value':i} for i in population_1000gp[superpop]], None   #TODO adjust for other population file (eg mouse)

#Callback to update the sample based on population selected
@app.callback(
    [Output('dropdown-sample','options'),
    Output('dropdown-sample','value')],
    [Input('dropdown-population-sample', 'value')]
)
def updateSampleDrop(pop):
    if pop is None or pop is '':
        return [], None
    return [{'label': sam, 'value' : sam} for sam in dict_pop[pop]], None 

#Callback to update the hidden div filter
@app.callback(
    Output('div-sample-filter-query', 'children'),
    [Input('button-filter-population-sample', 'n_clicks')],
    [State('dropdown-superpopulation-sample', 'value'),
    State('dropdown-population-sample', 'value')]
)
def updateSampleFilter(n, superpopulation, population):
    if n is None:
        raise PreventUpdate
    return str(superpopulation) + ',' + str(population)

#Callback to view next/prev page on sample table
@app.callback(
    [Output('div-table-samples', 'children'),
    Output('div-current-page-table-samples', 'children')],
    [Input('prev-page-sample', 'n_clicks_timestamp'),
    Input('next-page-sample', 'n_clicks_timestamp'),
    Input('div-sample-filter-query', 'children')],
    [State('button-filter-population-sample', 'n_clicks_timestamp'),
    State('url', 'search'),
    State('general-profile-table', 'selected_cells'),
    State('general-profile-table', 'data'),
    State('div-current-page-table-samples', 'children')]
)
def filterSampleTable( nPrev, nNext, filter_q, n, search, sel_cel, all_guides, current_page):
    if sel_cel is None:
        raise PreventUpdate
    if nPrev is None and nNext is None and n is None:
        raise PreventUpdate

    if nPrev is None:
        nPrev = 0
    if nNext is None:
        nNext = 0
    if n is None:
        n = 0
    
    sup_pop = filter_q.split(',')[0]
    pop = filter_q.split(',')[1]
    if sup_pop == 'None':
        sup_pop = None
    if pop == 'None':
        pop = None
    current_page = int(current_page)
    btn_sample_section = []
    btn_sample_section.append(n)
    btn_sample_section.append(nPrev)
    btn_sample_section.append(nNext)
    job_id = search.split('=')[-1]
    job_directory = 'Results/' + job_id + '/'
    with open('Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'

    guide = all_guides[int(sel_cel[0]['row'])]['Guide']
    if genome_type == 'both':
        col_names_sample = ['Sample', 'Gender', 'Population', 'Super Population',  'Number of targets', 'Targets in Sample', 'Total Targets in Population', 'Total targets in Super Population']
    else:
        col_names_sample = ['Sample', 'Gender', 'Population', 'Super Population',  'Number of targets', 'Total Targets in Population', 'Total targets in Super Population']
    if max(btn_sample_section) == n:              #Last button pressed is filtering, return the first page of the filtered table
        if genome_type == 'both':
            df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
            df = df.sort_values('Targets in Sample', ascending = False)
            df.drop(['Number of targets'], axis = 1, inplace = True)
        else:
            df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
            df = df.sort_values('Number of targets', ascending = False)
        more_info_col = []
        for i in range(df.shape[0]):
            more_info_col.append('Show Targets')
        df[''] = more_info_col
        if (sup_pop is None or sup_pop is '') and (pop is None or pop is ''):   #No filter value selected   #TODO implementare che se cancello i filtri ritorno i valori originali
            return generate_table_samples(df, 'table-samples', 1, guide, job_id ), 1
        if pop is None or pop is '':
            df.drop(df[(~(df['Population'].isin(population_1000gp[sup_pop])))].index , inplace = True)
        else:
            df.drop(df[(df['Population'] != pop)].index , inplace = True)
        return generate_table_samples(df, 'table-samples', 1, guide, job_id ), 1
    else:
        if max(btn_sample_section) == nNext:
            current_page = current_page + 1
            if genome_type == 'both':
                df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
                df = df.sort_values('Targets in Sample', ascending = False)
                df.drop(['Number of targets'], axis = 1, inplace = True)
            else:
                df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
                df = df.sort_values('Number of targets', ascending = False)
            more_info_col = []
            for i in range(df.shape[0]):
                more_info_col.append('Show Targets')
            df[''] = more_info_col
            #Active filter
            if pop or sup_pop:
                if pop is None or pop is '':
                    df.drop(df[(~(df['Population'].isin(population_1000gp[sup_pop])))].index , inplace = True)
                else:
                    df.drop(df[(df['Population'] != pop)].index , inplace = True)

            if ((current_page - 1) * 10) > len(df): 
                current_page = current_page -1
                if current_page < 1:
                    current_page = 1
            return generate_table_samples(df, 'table-samples', current_page, guide, job_id ), current_page
        
        else:   #Go to previous page
            current_page = current_page - 1
            if current_page < 1:
                current_page = 1
            if genome_type == 'both':
                df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
                df = df.sort_values('Targets in Sample', ascending = False)
                df.drop(['Number of targets'], axis = 1, inplace = True)
            else:
                df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
                df = df.sort_values('Number of targets', ascending = False)
            more_info_col = []
            for i in range(df.shape[0]):
                more_info_col.append('Show Targets')
            df[''] = more_info_col
            if pop or sup_pop:
                if pop is None or pop is '':
                    df.drop(df[(~(df['Population'].isin(population_1000gp[sup_pop])))].index , inplace = True)
                else:
                    df.drop(df[(df['Population'] != pop)].index , inplace = True)
            return generate_table_samples(df, 'table-samples', current_page, guide, job_id ), current_page
    raise PreventUpdate

#Callback to update the hidden div filter position
@app.callback(
    Output('div-position-filter-query', 'children'),
    [Input('button-filter-position', 'n_clicks')],
    [State('dropdown-chr-table-position', 'value'),
    State('input-position-start', 'value'),
    State('input-position-end', 'value')]
)
def updatePositionFilter(n, chr, pos_start, pos_end):
    if n is None:
        raise PreventUpdate
    if pos_start is '':
        pos_start = 'None'
    if pos_end is '':
        pos_end = 'None'
    return str(chr) + ',' + str(pos_start) + ',' + str(pos_end)


#Callback to filter chr from Summary by Position table, and to show next/prev page
@app.callback(
    [Output('div-table-position', 'children'),
    Output('div-current-page-table-position', 'children')],
    [Input('prev-page-position','n_clicks_timestamp'),
    Input('next-page-position', 'n_clicks_timestamp'),
    Input('div-position-filter-query', 'children')],
    [State('button-filter-position', 'n_clicks_timestamp'),
    State('url', 'search'),
    State('general-profile-table', 'selected_cells'),
    State('general-profile-table', 'data'),
    State('div-current-page-table-position', 'children'),
    State('div-mms-bulges-position', 'children')]
)
def filterPositionTable(nPrev, nNext, filter_q, n, search, sel_cel, all_guides, current_page, mms_bulge):
    if sel_cel is None:
        raise PreventUpdate
    if nPrev is None and nNext is None and n is None:
        raise PreventUpdate
    
    if nPrev is None:
        nPrev = 0
    if nNext is None:
        nNext = 0
    if n is None:
        n = 0

    filter_q = filter_q.split(',')
    chr = filter_q[0]
    if chr == 'None':
        chr = None
    pos_begin = filter_q[1]
    if pos_begin == 'None':
        pos_begin = None
    pos_end = filter_q[2]
    if pos_end == 'None':
        pos_end = None
    
    current_page = int(current_page)
    mms = int(mms_bulge.split('-')[0])
    max_bulges = int(mms_bulge.split('-')[1])
    btn_position_section = []
    btn_position_section.append(n)
    btn_position_section.append(nPrev)
    btn_position_section.append(nNext)
    job_id = search.split('=')[-1]
    job_directory = 'Results/' + job_id + '/'
    guide = all_guides[int(sel_cel[0]['row'])]['Guide']
    if max(btn_position_section) == n:              #Last button pressed is filtering, return the first page of the filtered table
        if pos_begin is None or pos_begin is '':
            pos_begin = 0
        if pos_end is '':
            pos_end = None
        if pos_end:
            if int(pos_end) < int(pos_begin):
                pos_end = None
        df = pd.read_csv(job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t')  
        
        df.rename(columns = {'#Chromosome':'Chromosome'}, inplace = True)
        more_info_col = []
        for i in range(df.shape[0]):
            more_info_col.append('Show Targets')
        df[''] = more_info_col
        if chr is None or chr is '':
            return generate_table_position(df, 'table-position', 1, mms, max_bulges,guide, job_id ), 1
        if pos_end is None:
            df.drop(df[(df['Chromosome'] != chr) | ((df['Chromosome'] == chr) & (df['Position'] < int(pos_begin)) )].index , inplace = True)
        else:
            df.drop(df[(df['Chromosome'] != chr) | ((df['Chromosome'] == chr) & (df['Position'] < int(pos_begin)) | (df['Position'] > int(pos_end)))].index , inplace = True)
        return generate_table_position(df, 'table-position', 1, mms, max_bulges,guide, job_id ), 1
    else:
        
        if max(btn_position_section) == nNext:
            current_page = current_page + 1
            if chr:
                if pos_begin is None or pos_begin is '':
                    pos_begin = 0
                if pos_end is '':
                    pos_end = None
                if pos_end:
                    if int(pos_end) < int(pos_begin):
                        pos_end = None
                df = pd.read_csv(job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t')  
            else:
                df = pd.read_csv(job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t', nrows = current_page * 10)   
            df.rename(columns = {'#Chromosome':'Chromosome'}, inplace = True)
            more_info_col = []
            for i in range(df.shape[0]):
                more_info_col.append('Show Targets')
            df[''] = more_info_col
            if chr:
                if pos_end is None:
                    df.drop(df[(df['Chromosome'] != chr) | ((df['Chromosome'] == chr) & (df['Position'] < int(pos_begin)) )].index , inplace = True)
                else:
                    df.drop(df[(df['Chromosome'] != chr) | ((df['Chromosome'] == chr) & (df['Position'] < int(pos_begin)) | (df['Position'] > int(pos_end)))].index , inplace = True)
            if ((current_page - 1) * 10) > len(df): 
                current_page = current_page -1
                if current_page < 1:
                    current_page = 1
            return generate_table_position(df, 'table-position', current_page, mms, max_bulges,guide, job_id ), current_page
        else:                       #Go to previous page
            current_page = current_page - 1
            if current_page < 1:
                current_page = 1

            if chr:
                if pos_begin is None or pos_begin is '':
                    pos_begin = 0
                if pos_end is '':
                    pos_end = None
                if pos_end:
                    if int(pos_end) < int(pos_begin):
                        pos_end = None
                df = pd.read_csv(job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t')  
            else:
                df = pd.read_csv(job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t', nrows = current_page * 10)   
            df.rename(columns = {'#Chromosome':'Chromosome'}, inplace = True)
            more_info_col = []
            for i in range(df.shape[0]):
                more_info_col.append('Show Targets')
            df[''] = more_info_col
            if chr:
                if pos_end is None:
                    df.drop(df[(df['Chromosome'] != chr) | ((df['Chromosome'] == chr) & (df['Position'] < int(pos_begin)) )].index , inplace = True)
                else:
                    df.drop(df[(df['Chromosome'] != chr) | ((df['Chromosome'] == chr) & (df['Position'] < int(pos_begin)) | (df['Position'] > int(pos_end)))].index , inplace = True)
            return generate_table_position(df, 'table-position', current_page, mms, max_bulges,guide, job_id ), current_page

#FOR BUTTON IN TABLE
# element.style {
#     background: none;
#     border: none;
#     margin: 0;
#     padding: 0;
#     cursor: pointer;
#     font-family: monospace;
#     font-size: large;
#     font-weight: normal;
# }




#If the input guides are different len, select the ones with same length as the first
def selectSameLenGuides(list_guides):
    '''
    Se l'utente mette guide di lunghezza diversa, la funzione prende la lunghezza della prima guida e salva solo le guide con quella lunghezza
    '''
    selected_length = len(list_guides.split('\n')[0])
    same_len_guides_list = []
    for guide in list_guides.split('\n'):
        if len(guide) == selected_length:
            same_len_guides_list.append(guide)
    same_len_guides = '\n'.join(same_len_guides_list).strip()
    return same_len_guides

def resultPage(job_id):
    '''
    La funzione ritorna il layout della pagina risultati (tabella delle guide + eventuali immagini). Nella tabella delle guide
    carico il profile ottenuto dalla ricerca. Carica inoltre l'ACFD, che è il cfd score aggregato per tutti i risultati di una singola guida.
    Crea poi 10 bottoni: un numero pari a mismatches + 2  che sono visibili, il resto con style = {'display':'none'}, così ho sempre il numero
    esatto di bottoni per mismatches in base ai mms dati in input nella ricerca (serve a risolvere problemi con le callback che hanno input
    da elementi non creati. In questo caso io creo tutti i possibili bottoni ma ne rendo visibili/disponibili solo il numero corretto in base
    ai mms).
    TODO usare className per i bottoni e modificare lo stile, oppure vedere se è possibile usare un buttongroup. Vedere quale è meglio.
    TODO al momento la tabella delle guide è ordinata per acfd, rendere possibile anche l'ordinamento e il filtering da parte dell'utente,
    usare il codice presente in dash datatable filtering con python.
    '''
    value = job_id
    job_directory = 'Results/' + job_id + '/'
    warning_message = []
    if (not isdir(job_directory)):
        return html.Div(dbc.Alert("The selected result does not exist", color = "danger"))

    #Load mismatches
    with open('Results/' + value + '/Params.txt') as p:
        all_params = p.read()
        mms = (next(s for s in all_params.split('\n') if 'Mismatches' in s)).split('\t')[-1]
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
    mms = int(mms[0])
    mms_values = [{'label':i, 'value':i} for i in range(mms + 1) ]      
    
    col_profile_general = ['Total On-Targets', 'Total Off-Targets']
    for i in range(mms):
        col_profile_general.append(str(i+1) + ' Mismatches')
    col_type = ['numeric' for i in col_profile_general]
    
    
    #Load profile
    try:
        profile = pd.read_csv('Results/' + value + '/' + value + '.profile_complete.xls')   #NOTE profile_complete has ',' as separator
        if len(profile.columns) == 1:
            profile = pd.read_csv('Results/' + value + '/' + value + '.profile_complete.xls', sep='\t')
    except:
        profile = pd.read_csv('Results/' + value + '/' + value + '.profile.xls', sep = '\t')    #NOTE profile has \t as separator or ','
        if len(profile.columns) == 1:
            profile = pd.read_csv('Results/' + value + '/' + value + '.profile.xls')
    #load acfd for each guide 
    with open('Results/' + value + '/acfd.txt') as a:
        all_scores = a.read().strip().split('\n')
    
    if 'NO SCORES' not in all_scores:
        all_scores.sort()
        acfd = [float(a.split('\t')[1]) for a in all_scores]
        doench = [int(a.split('\t')[2]) for a in all_scores]
        acfd  = [int(round((100/(100 + x))*100)) for x in acfd]
        columns_profile_table = [{'name':'Guide', 'id' : 'Guide', 'type':'text'}, {'name':'CFD', 'id': 'CFD', 'type':'numeric'}, {'name':'Doench 2016', 'id': 'Doench 2016', 'type':'numeric'} ,{'name':'Total On-Targets', 'id' : 'Total On-Targets', 'type':'numeric'}, {'name':'Total Off-targets', 'id' : 'Total Off-Targets', 'type':'numeric'}]
    else:
        columns_profile_table = [{'name':'Guide', 'id' : 'Guide', 'type':'text'}, {'name':'Total On-Targets', 'id' : 'Total On-Targets', 'type':'numeric'}, {'name':'Total Off-targets', 'id' : 'Total Off-Targets', 'type':'numeric'}]

    keep_column = ['GUIDE', 'ONT', 'OFFT']
    for i in range (mms):
        #columns_profile_table.append({'name': str(i+1) + ' Mismatches', 'id':str(i+1) + ' Mismatches', 'type':'numeric'})
        keep_column.append(str(i+1) + 'MM')
    
    profile = profile[keep_column]
    rename_columns = {'GUIDE':'Guide',"ONT":'Total On-Targets', 'OFFT':'Total Off-Targets'}
    col_targetfor = 'Targets for '
    for i in range(mms):
        rename_columns[str(i+1) + 'MM'] = str(i+1) + ' Mismatches'
        col_targetfor = col_targetfor + str(i) + '-'
    col_targetfor = col_targetfor + str(mms)
    col_targetfor = col_targetfor + ' mismatches'
    columns_profile_table.append({'name': col_targetfor, 'id' : 'col_targetfor', 'type':'text'})
    profile.rename(columns = rename_columns, inplace = True)    #Now profile is Guide, Total On-targets, ...
    col_to_add = []
    tmp_col_to_add = []
    for row in profile.itertuples():
        for i in range (mms+1):
            if i == 0:
                tmp_col_to_add.append(str(profile['Total On-Targets'][row[0]]))
            else:
                tmp_col_to_add.append(str(profile[str(i) + ' Mismatches'][row[0]]))
        col_to_add.append(' - '.join(tmp_col_to_add))
        tmp_col_to_add = []
        
    profile['col_targetfor'] = col_to_add
    
    if genome_type == 'var':
        columns_profile_table.append({'name':'Targets in samples', 'id':'Targets in samples', 'type':'numeric'})
        column_sample_total = []
        for guide in profile.Guide.unique():
            with open ('Results/' + value + '/' + value + '.summary_by_samples.' + guide + '.txt', 'r') as sample_list:
                sample_total = sample_list.readline().strip().split('\t')[1]
                column_sample_total.append(sample_total)
        profile['Targets in samples'] = column_sample_total
    
    
    final_list = []    
    final_list.append(
        html.H3('Result Summary')
    )
   

    
    profile = profile.sort_values('Guide')
    profile['CFD'] = acfd
    profile['Doench 2016'] = doench
    
    profile = profile.sort_values(['CFD', 'Doench 2016'], ascending = [False, False])
    final_list.append(html.P('Select a guide by clicking on a row to view more information'))
    final_list.append(
        html.Div(
            dash_table.DataTable(
                id = 'general-profile-table',
                #page_size=PAGE_SIZE,
                columns = columns_profile_table,
                data = profile.to_dict('records'),
                selected_cells = [{'row':0, 'column':0}],
                css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],
                page_current= 0,
                page_size= 10,
                page_action='custom',

                filter_action='custom',
                filter_query='',

                sort_action='custom',
                sort_mode='multi',
                sort_by=[],
                style_table={
                    'max-height': '200px'
                    #'overflowY': 'scroll',
                }
            )
            ,id = 'div-general-profile-table')
    )

    final_list.append(html.Br())
    
    if genome_type == 'ref':
        final_list.append(
        dcc.Tabs(id="tabs-reports", value='tab-summary-by-guide', children=[
            dcc.Tab(label='Summary by Guide', value='tab-summary-by-guide'),
            dcc.Tab(label='Summary by Position', value='tab-summary-by-position'),
            dcc.Tab(label='Graphical Summary', value='tab-summary-graphical'),
        ])
    )
        
    else:
        final_list.append(
            dcc.Tabs(id="tabs-reports", value='tab-summary-by-guide', children=[
                dcc.Tab(label='Summary by Guide', value='tab-summary-by-guide'),
                dcc.Tab(label='Summary by Sample', value='tab-summary-by-sample'),
                dcc.Tab(label='Summary by Position', value='tab-summary-by-position'),
                dcc.Tab(label='Graphical Summary', value='tab-summary-graphical'),
            ])
        )
    final_list.append(html.Div(id = 'div-tab-content'))

    final_list.append(html.Div(genome_type, style = {'display':'none'}, id = 'div-genome-type'))
    result_page = html.Div(final_list, style = {'margin':'1%'})
    return result_page


#Update color on selected row
@app.callback(
    Output('general-profile-table', 'style_data_conditional'),
    [Input('general-profile-table', 'selected_cells')],
    [State('general-profile-table', 'data')]
)
def colorSelectedRow(sel_cel, all_guides):
    if sel_cel is None or not sel_cel or not all_guides:
        raise PreventUpdate
    guide = all_guides[int(sel_cel[0]['row'])]['Guide']
    return [
        {
            'if': {
                    'filter_query': '{Guide} eq "' + guide + '"', 
                    #'column_id' :'{#Bulge type}',
                    #'column_id' :'{Total}'
                },
                #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                'background-color':'rgba(0, 0, 255,0.15)'#'rgb(255, 102, 102)'
                
            }
    ]

# Filtering e sorting per la pagina principale delle guide
@app.callback(
    [Output('general-profile-table', 'data'),
    Output('general-profile-table', 'selected_cells')],
    [Input('general-profile-table', "page_current"),
     Input('general-profile-table', "page_size"),
     Input('general-profile-table', 'sort_by'),
     Input('general-profile-table', 'filter_query')],
    [State('url', 'search')]    
)
def update_table_general_profile(page_current, page_size, sort_by, filter, search):
    job_id = search.split('=')[-1]
    
    with open('Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        mms = int((next(s for s in all_params.split('\n') if 'Mismatches' in s)).split('\t')[-1])
    
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
    
    filtering_expressions = filter.split(' && ')
    #Get guide from guide.txt
    with open('Results/' + job_id + '/guides.txt') as g:
        guides = g.read().strip().split('\n')
        guides.sort()

    #load acfd for each guide 
    with open('Results/' + job_id + '/acfd.txt') as a:
        all_scores = a.read().strip().split('\n')
    
    #Load scores
    if 'NO SCORES' not in all_scores:
        all_scores.sort()
        acfd = [float(a.split('\t')[1]) for a in all_scores]
        doench = [int(a.split('\t')[2]) for a in all_scores]
        acfd  = [int(round((100/(100 + x))*100)) for x in acfd] 
    #     columns_profile_table = [{'name':'Guide', 'id' : 'Guide', 'type':'text'}, {'name':'CFD', 'id': 'CFD', 'type':'numeric'}, {'name':'Doench 2016', 'id': 'Doench 2016', 'type':'numeric'} ,{'name':'Total On-Targets', 'id' : 'Total On-Targets', 'type':'numeric'}, {'name':'Total Off-targets', 'id' : 'Total Off-Targets', 'type':'numeric'}]
    # else:
    #     columns_profile_table = [{'name':'Guide', 'id' : 'Guide', 'type':'text'}, {'name':'Total On-Targets', 'id' : 'Total On-Targets', 'type':'numeric'}, {'name':'Total Off-targets', 'id' : 'Total Off-Targets', 'type':'numeric'}]

    # col_targetfor = 'Targets for '
    # for i in range(mms):
    #     col_targetfor = col_targetfor + str(i) + '-'

    # col_targetfor = col_targetfor + str(mms)
    # col_targetfor = col_targetfor + ' mismatches'
    # columns_profile_table.append({'name': col_targetfor, 'id' : 'col_targetfor', 'type':'text'})

    #Get target counting from summary by guide -> select only bulge type X rows
    column_on_target = []
    column_off_target = []
    column_sep_by_mm_value = []
    for g in guides:
        df_profile = pd.read_pickle('Results/' + job_id + '/' + job_id + '.summary_by_guide.' + g + '.txt')
        column_on_target = int(df_profile[(df_profile.Mismatches == 0) & (df_profile['Bulge Type'] == 'X')].iloc[0]['Number of targets'])
        zero_to_n_mms = df_profile[(df_profile['Bulge Type'] == 'X')]['Number of targets'].to_list()
        column_sep_by_mm_value.append(' - '.join(str(int(x)) for x in zero_to_n_mms))
        column_off_target.append(int(sum(zero_to_n_mms[1:])))
    if 'NO SCORES' not in all_scores:
        data_guides = {'Guide': guides, 'CFD':acfd, 'Doench 2016':doench, 'Total On-Targets':column_on_target, 'Total Off-Targets':column_off_target, 'col_targetfor': column_sep_by_mm_value}
    else:
        data_guides = {'Guide': guides, 'Total On-Targets':column_on_target, 'Total Off-Targets':column_off_target, 'col_targetfor': column_sep_by_mm_value}
   
    dff = pd.DataFrame(data_guides)

            

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

    #Calculate sample count
    
    data_to_send=dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')
    return data_to_send, [{'row':0, 'column':0}]

@cache.memoize()
def global_store_subset(value, bulge_t, bulge_s, mms, guide):
    '''
    Caching dei file targets per una miglior performance di visualizzazione
    '''
    if value is None:
        return ''
    df = pd.read_csv( 'Results/' + value + '/' + value + '.' + bulge_t + '.' + bulge_s + '.' + mms + '.' + guide +'.txt', sep = '\t', header = None)
    #df.rename(columns = {"#Bulge type":'Bulge Type', "#Bulge_type":'Bulge Type', 'Bulge_Size':'Bulge Size'}, inplace = True)
    return df


def guidePagev3(job_id, hash):
    guide = hash[:hash.find('new')]
    mms = hash[-1:]
    bulge_s = hash[-2:-1]
    if 'DNA' in hash:
        bulge_t = 'DNA'
    elif 'RNA' in hash:
        bulge_t = 'RNA'
    else:
        bulge_t = 'X'
    
    value = job_id
    if (not isdir('Results/' + job_id)):
        return html.Div(dbc.Alert("The selected result does not exist", color = "danger"))
    with open('Results/' + value + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
    final_list = []
    final_list.append(html.H3('Selected Guide: ' + guide))
    final_list.append(html.P('List of Targets found for the selected guide. Select a row to view other possible configurations of the target.'))
    if genome_type == 'ref':
        col_list = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Cluster Position' ,'Direction', 'Mismatches', 'Bulge Size', 'Total'] 
        col_type = ['text','text','text','text','numeric', 'numeric','text','numeric', 'numeric', 'numeric']
        file_to_grep = '.targets.cluster.txt'
    elif genome_type == 'var':
        col_list = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Cluster Position' ,'Direction', 'Mismatches', 'Bulge Size', 'Total', 'Min_mismatches', 'Max_mismatches', 'PAM disruption'] 
        col_type = ['text','text','text','text','numeric', 'numeric','text','numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'text']
        # file_to_grep = 'targets.cluster.minmaxdisr'
        file_to_grep = '.final.txt'
    else:
        col_list = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Cluster Position','Direction', 'Mismatches', 'Bulge Size', 'Total', 'Min_mismatches', 'Max_mismatches', 'PAM disruption', 'PAM creation', 'Variant unique', 'Samples Summary']#, 'Samples']
        col_type = ['text','text','text','text','numeric','text', 'text','numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'text', 'text', 'text', 'text', 'text']#, 'text']
        file_to_grep = '.final.txt'
    cols = [{"name": i, "id": i, 'type':t, 'hideable':True} for i,t in zip(col_list, col_type)]
    job_directory = 'Results/' + job_id + '/'
    
    start = time.time()
    guide_grep_result = job_directory + job_id + '.' + bulge_t + '.' + bulge_s + '.' + mms + '.' + guide + '.txt'
    if not os.path.exists(guide_grep_result):    #Example    job_id.X.0.4.guide.txt
        # subprocess.call(['LC_ALL=C fgrep ' + guide + ' ' + job_directory + job_id + file_to_grep + ' | LC_ALL=C fgrep ' + bulge_t + ' | awk \'$8==' + mms + ' && $9==' + bulge_s + '\' > ' + guide_grep_result], shell = True)
        subprocess.call(['LC_ALL=C fgrep ' + guide + ' ' + job_directory + job_id + file_to_grep + ' | LC_ALL=C fgrep ' + bulge_t + ' | awk -v mm="' + mms + '" -v b="'+bulge_s+'" -f PostProcess/extract_subcluster.awk > ' + guide_grep_result], shell = True)
    global_store_subset(job_id, bulge_t, bulge_s, mms,guide)
    #subset_targets = pd.read_csv('example_todo_delete.txt', sep = '\t')
    #data_dict = subset_targets.to_dict('records')
    print('Grep e load:', time.time() - start)
    final_list.append(          
        html.Div( 
            dash_table.DataTable(
                id='table-subset-target', 
                columns=cols, 
                #data = subset_targets.to_dict('records'),
                virtualization = True,
                fixed_rows={ 'headers': True, 'data': 0 },
                #fixed_columns = {'headers': True, 'data':1},
                style_cell={'width': '150px'},
                page_current=0,
                page_size=PAGE_SIZE,
                page_action='custom',
                sort_action='custom',
                sort_mode='multi',
                sort_by=[],
                filter_action='custom',
                filter_query='',
                style_table={
                    'max-height': '600px'
                    #'overflowY': 'scroll',
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'Samples'},
                        'textAlign': 'left'
                    }
                ],
                css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],
                export_format = 'csv'                
            ),
            id = 'div-result-table',
        )
    )
    final_list.append(html.Br())
    final_list.append(
        html.Div(
            id = 'div-second-table-subset-targets'
        )
    )
    
    return html.Div(final_list, style = {'margin':'1%'})

#Send the data when next or prev button is clicked on the result table
@app.callback(
    [Output('table-subset-target', 'data'),
    Output('table-subset-target', 'style_data_conditional')],
    [Input('table-subset-target', "page_current"),
     Input('table-subset-target', "page_size"),
     Input('table-subset-target', "sort_by"),
     Input('table-subset-target', 'filter_query')],
     [State('url', 'search'),
     State('url', 'hash')]
)
def update_table_subset(page_current, page_size, sort_by, filter, search, hash_guide):
    '''
    La funzione ritorna uno split dei risultati in base ad un filtering o a un sort da parte dell'utente. Inoltre aggiorna i risultati
    visualizzati quando il bottone next page / prev page è cliccato. (Codice preso dalla pagina dash datatable sul sorting con python)
    Inoltre carica i file targets, o scores se presente, e lo trasforma in un dataframe, cambiando il nome delle colonne per farle corrispondere
    all'id delle colonne della tabella nella pagina.
    Se non ci sono targets ritorna un avviso di errore
    '''
    job_id = search.split('=')[-1]
    job_directory = 'Results/' + job_id + '/'
    #guide = hash_guide.split('#')[1]
    value = job_id
    if search is None:
        raise PreventUpdate
    filtering_expressions = filter.split(' && ')
    #filtering_expressions.append(['{crRNA} = ' + guide])   
    guide = hash_guide[1:hash_guide.find('new')]
    mms = hash_guide[-1:]
    bulge_s = hash_guide[-2:-1]
    if 'DNA' in hash_guide:
        bulge_t = 'DNA'
    elif 'RNA' in hash_guide:
        bulge_t = 'RNA'
    else:
        bulge_t = 'X'  
    df = global_store_subset(value, bulge_t, bulge_s, mms, guide)
    dff = df
    dff.rename(columns ={0:'Bulge Type', 1:'crRNA', 2:'DNA', 3:'Chromosome', 4:'Position', 5:'Cluster Position', 6:'Direction',
        7:'Mismatches', 8:'Bulge Size', 9:'Total', 10:'Min_mismatches', 11:'Max_mismatches', 12: 'PAM disruption', 13:'PAM creation', 14 : 'Variant unique', 15:'Samples', 16:'Correct Guide',17:'Top Subcluster'} , inplace = True)
    #TODO cambiare nome colonne se ref, var , both
    # sort_by.insert(0, {'column_id' : 'Mismatches', 'direction': 'asc'})
    # sort_by.insert(1, {'column_id' : 'Bulge Size', 'direction': 'asc'})
    #sort_by.insert(2, {'column_id': 'CFD', 'direction':'desc'})
    
    #Remove not top1 subcluster:
    dff.drop( df[(df['Top Subcluster'] == 's')].index, inplace = True)

    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)].sort_values([col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False)
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    #NOTE sort_by: [{'column_id': 'BulgeType', 'direction': 'asc'}, {'column_id': 'crRNA', 'direction': 'asc'}]
    #sort_by.insert(0, {'column_id' : 'Mismatches', 'direction': 'asc'})
    #sort_by.insert(0, {'column_id' : 'BulgeSize', 'direction': 'asc'})
    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )
   

    cells_style = [
                        {
                        'if': {
                                'filter_query': '{Variant unique} eq y',
                                #'filter_query': '{Direction} eq +', 
                                #'column_id' :'Bulge Type'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        },
                        # {#TODO colora altro colore quelle con pam creation
                        # 'if': {
                        #         'filter_query': '{Chromosome} eq "chr2"',
                        #         #'filter_query': '{Direction} eq +', 
                        #         #'column_id' :'Bulge Type'
                        #     },
                        #     #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                        #     'background-color':'rgba(255, 69, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        # },
                        # {
                        #     'if': {
                        #             'filter_query': '{Variant unique} eq n',           
                        #             'column_id' :'Bulge Type'
                        #         },
                        #         'border-left': '5px solid rgba(26, 26, 255, 0.9)',

                        # }
                        
                ]
    
    #Calculate sample count
    
    data_to_send=dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')
    for row in data_to_send:
        summarized_sample_cell = dict()
        for s in row['Samples'].split(','):
            if s == 'n':
                break
            try:
                summarized_sample_cell[dict_pop_to_superpop[dict_sample_to_pop[s]]] += 1
            except:
                summarized_sample_cell[dict_pop_to_superpop[dict_sample_to_pop[s]]] = 1
        if summarized_sample_cell:
            row['Samples Summary'] = ', '.join([str(summarized_sample_cell[sp]) + ' ' + sp for sp in summarized_sample_cell])
        else:
            row['Samples Summary'] = 'n'

    return data_to_send, cells_style

#Create second table for subset targets page, and show corresponding samples
@app.callback(
    Output('div-second-table-subset-targets', 'children'),
    [Input('table-subset-target', 'active_cell')],
    [State('table-subset-target', 'data'),
    State('table-subset-target', 'columns'),
    State('url', 'search')]
)
def loadFullSubsetTable(active_cel, data, cols, search):
    if active_cel is  None:
        raise PreventUpdate
    fl = []
    job_id = search.split('=')[-1]
    #Show sample list
    fl.append(html.Br())
    # fl.append(html.H4('Samples list'))
    
    # sample_list = data[active_cel['row']]['Samples'].split(',')
    # for i in range(int(len(sample_list)/20) + 1):
    #     fl.append(html.P(', '.join(sample_list[20*i:20*i+20])))     #TODO migliorare mettendo elenco puntato con popolazioni
    
    #Table for subtop cluster
    fl.append(html.Br())
    df = global_store_subset(job_id, data[active_cel['row']]['Bulge Type'], str(data[active_cel['row']]['Bulge Size']), str(data[active_cel['row']]['Mismatches']), data[active_cel['row']]['crRNA'])
    df.rename(columns ={0:'Bulge Type', 1:'crRNA', 2:'DNA', 3:'Chromosome', 4:'Position', 5:'Cluster Position', 6:'Direction',
        7:'Mismatches', 8:'Bulge Size', 9:'Total', 10:'Min_mismatches', 11:'Max_mismatches', 12: 'PAM disruption', 13:'PAM creation', 14 : 'Variant unique', 15:'Samples', 16:'Correct Guide',17:'Top Subcluster'} , inplace = True)
    #TODO cambiare nome colonne se ref, var , both
    df.drop(df[(~( df['Cluster Position'] == int(data[active_cel['row']]['Cluster Position']))) | (~( df['Chromosome'] == data[active_cel['row']]['Chromosome']))].index, inplace = True)
    # print(df)
    fl.append(
        html.Div(
            dash_table.DataTable(
                id='second-table-subset-targets', 
                columns=cols, 
                data = df.to_dict('records'),
                virtualization = True,
                fixed_rows={ 'headers': True, 'data': 0 },
                #fixed_columns = {'headers': True, 'data':1},
                style_cell={'width': '150px'},
                page_current=0,
                page_size=PAGE_SIZE,
                page_action='custom',
                sort_action='custom',
                sort_mode='multi',
                sort_by=[],
                filter_action='custom',
                filter_query='',
                style_table={
                    'max-height': '600px'
                    #'overflowY': 'scroll',
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'Samples'},
                        'textAlign': 'left'
                    }
                ],
                css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],
                style_data_conditional = [{
                        'if': {
                                'filter_query': '{Variant unique} eq y',
                                #'filter_query': '{Direction} eq +', 
                                #'column_id' :'Bulge Type'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        },
                        {#TODO colora altro colore quelle con pam creation
                        'if': {
                                'filter_query': '{Variant unique} eq y && {Pam creation}  != "n"',
                                #'filter_query': '{Direction} eq +', 
                                #'column_id' :'Bulge Type'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(255, 69, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        },
                        {#TODO fixare
                        'if': {
                                'filter_query': '{Top subcluster} eq t',         
                                # 'column_id' :'BulgeType'
                            },
                            'border-left': '5px solid rgba(26, 26, 255, 0.9)',
                            'font-weight':'bold'
                            

                        } 
                ]         
            ),
        )
    )

    return  fl

@cache.memoize()
def global_store_general(path_file_to_load):
    '''
    Caching dei file targets per una miglior performance di visualizzazione
    '''
    if path_file_to_load is None:
        return ''
    df = pd.read_csv( path_file_to_load , sep = '\t', header = None)
    #df.rename(columns = {"#Bulge type":'Bulge Type', "#Bulge_type":'Bulge Type', 'Bulge_Size':'Bulge Size'}, inplace = True)
    return df

#Return the targets found for the selected sample
def samplePage(job_id, hash):
    guide = hash[:hash.find('-Sample-')]
    sample = hash[hash.rfind('-') + 1:]
    if (not isdir('Results/' + job_id)):
        return html.Div(dbc.Alert("The selected result does not exist", color = "danger"))

    with open('Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'

    final_list = []
    final_list.append(
        #html.P('List of Targets found for the selected Sample - ' + sample + ' - and guide - ' + guide + ' -')
        html.H3('Selected Sample: ' + sample)
    )
    final_list.append(html.P('List of Targets found for the selected sample'))
    # col_list = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Direction', 'Mismatches', 'Bulge Size', 'Total', 'Min_mismatches', 'Max_mismatches', 'PAM disruption', 'PAM creation', 'Variant unique', 'Samples']
    
    if genome_type == 'var':
        col_list = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Cluster Position' ,'Direction', 'Mismatches', 'Bulge Size', 'Total', 'Min_mismatches', 'Max_mismatches', 'PAM disruption',  'Samples Summary']#'Samples', 'Correct Guide'] 
        col_type = ['text','text','text','text','numeric', 'numeric','text','numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'text', 'text']
    else:
        col_list = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Cluster Position','Direction', 'Mismatches', 'Bulge Size', 'Total', 'Min_mismatches', 'Max_mismatches', 'PAM disruption', 'PAM creation', 'Variant unique',  'Samples Summary']# 'Samples', 'Correct Guide']
        col_type = ['text','text','text','text','numeric','numeric','text', 'numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'text', 'text', 'text','text']
    
    file_to_grep = '.top_1.samples.txt'
    sample_grep_result = 'Results/'+ job_id + '/' + job_id + '.' + sample + '.' + guide + '.txt'
    if not os.path.exists(sample_grep_result):    #Example    job_id.HG001.guide.txt
        subprocess.call(['LC_ALL=C fgrep ' + guide + ' ' + 'Results/'+ job_id + '/' + job_id + file_to_grep + ' | LC_ALL=C fgrep ' + sample + ' > ' + sample_grep_result], shell = True)

    #df = pd.read_csv('Results/'+ job_id + '/' + job_id + '.' + sample + '.' + guide + '.txt', sep = '\t', names = col_list, header = None)
    #df.drop(df.columns[[-1,]], axis=1, inplace=True)         #NOTE Drop the Correct Guide column
    
    # df.drop(df.columns[[-1,]], axis=1, inplace=True)         #NOTE comment to show the sample column (maybe not informative in this view)
    # del col_list[-1]                                         #NOTE comment to show the sample column (maybe not informative in this view)
    cols = [{"name": i, "id": i, 'type':t, 'hideable':True} for i,t in zip(col_list, col_type)]
    
    final_list.append(          #TODO add margin bottom 1rem to toggle button and prev-next buttons
        html.Div( 
            dash_table.DataTable(
                id='table-sample-target', 
                columns=cols, 
                #data = df.to_dict('records'),
                virtualization = True,
                fixed_rows={ 'headers': True, 'data': 0 },
                #fixed_columns = {'headers': True, 'data':1},
                style_cell={'width': '150px'},
                page_current=0,
                page_size=PAGE_SIZE,
                page_action='custom',
                sort_action='custom',
                sort_mode='multi',
                sort_by=[],
                filter_action='custom',
                filter_query='',
                style_table={
                    'max-height': '600px'
                    #'overflowY': 'scroll',
                },
                style_data_conditional=[
                    {
                        'if': {
                                'filter_query': '{Variant unique} eq y', 
                                #'column_id' :'{#Bulge type}',
                                #'column_id' :'{Total}'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        }
                ],
                css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],
                # css= [{ 'selector': 'td.row--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.row--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],
                
            ),
            id = 'div-result-table',
        )
    )
    return html.Div(final_list, style = {'margin':'1%'})

#Filter and sorting sample targets
@app.callback(
    Output('table-sample-target', 'data'),
    [Input('table-sample-target', "page_current"),
     Input('table-sample-target', "page_size"),
     Input('table-sample-target', 'sort_by'),
     Input('table-sample-target', 'filter_query')],
    [State('url', 'search'),
     State('url', 'hash')]    
)
def update_table_sample(page_current, page_size, sort_by, filter, search, hash):
    job_id = search.split('=')[-1]
    hash = hash.split('#')[1]
    guide = hash[:hash.find('-Sample-')]
    sample = hash[hash.rfind('-') + 1:]
    with open('Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
    
    filtering_expressions = filter.split(' && ')
    dff = global_store_general('Results/'+ job_id + '/' + job_id + '.' + sample + '.' + guide + '.txt')

    #TODO inserire colonne corrette in base al tipo di ricerca
    dff.rename(columns ={0:'Bulge Type', 1:'crRNA', 2:'DNA', 3:'Chromosome', 4:'Position', 5:'Cluster Position', 6:'Direction',
        7:'Mismatches', 8:'Bulge Size', 9:'Total', 10:'Min_mismatches', 11:'Max_mismatches', 12: 'PAM disruption', 13:'PAM creation', 14 : 'Variant unique', 15:'Samples', 16:'Correct Guide',17:'Top Subcluster'} , inplace = True)
    dff.drop(dff.columns[[-1,]], axis=1, inplace=True)         #NOTE Drop the Correct Guide column
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

    #Calculate sample count
    
    data_to_send=dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')
    for row in data_to_send:
        summarized_sample_cell = dict()
        for s in row['Samples'].split(','):
            if s == 'n':
                break
            try:
                summarized_sample_cell[dict_pop_to_superpop[dict_sample_to_pop[s]]] += 1
            except:
                summarized_sample_cell[dict_pop_to_superpop[dict_sample_to_pop[s]]] = 1
        if summarized_sample_cell:
            row['Samples Summary'] = ', '.join([str(summarized_sample_cell[sp]) + ' ' + sp for sp in summarized_sample_cell])
        else:
            row['Samples Summary'] = 'n'
    return data_to_send

#Return the targets for the selected cluster
def clusterPage(job_id, hash):
    guide = hash[:hash.find('-Pos-')]
    chr_pos = hash[hash.find('-Pos-') + 5:]
    chromosome = chr_pos.split('-')[0]
    position = chr_pos.split('-')[1]
    if (not isdir('Results/' + job_id)):
        return html.Div(dbc.Alert("The selected result does not exist", color = "danger"))
    with open('Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
    final_list = []
    final_list.append(
        html.H3('Selected Position: ' + chromosome + ' - ' + position)
    )
    final_list.append(html.P('List of Targets found for the selected position'))
    
    if genome_type == 'ref':
        col_list = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Cluster Position' ,'Direction', 'Mismatches', 'Bulge Size', 'Total', 'Correct Column'] 
        col_type = ['text','text','text','text','numeric', 'numeric','text','numeric', 'numeric', 'numeric']
        file_to_grep = '.targets.cluster.txt'
    elif genome_type == 'var':
        col_list = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Cluster Position' ,'Direction', 'Mismatches', 'Bulge Size', 'Total', 'Min_mismatches', 'Max_mismatches', 'PAM disruption', 'Samples Summary']#'Samples', #'Correct Column'] 
        col_type = ['text','text','text','text','numeric', 'numeric','text','numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'text']
        # file_to_grep = 'targets.cluster.minmaxdisr'
        file_to_grep = '.final.txt'
    else:
        col_list = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Cluster Position','Direction', 'Mismatches', 'Bulge Size', 'Total', 'Min_mismatches', 'Max_mismatches', 'PAM disruption', 'PAM creation', 'Variant unique', 'Samples Summary']#'Samples', 'Correct Column']
        col_type = ['text','text','text','text','numeric','text','numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'text', 'text', 'text', 'text', 'text']
        file_to_grep = '.final.txt'
    
    cluster_grep_result = 'Results/'+ job_id + '/' + job_id + '.' + chromosome + '_' + position + '.' + guide +'.txt'
    if not os.path.exists(cluster_grep_result):    #Example    job_id.chr3_100.guide.txt
        subprocess.call(['LC_ALL=C fgrep ' + guide + ' ' + 'Results/'+ job_id + '/' + job_id + file_to_grep + ' | awk \'$6==' + position + ' && $4==\"' + chromosome + '\"\' > ' + cluster_grep_result], shell = True)
      
        
    # df = pd.read_csv('Results/' + job_id + '/' + job_id + '.' + chromosome + '_' + position + '.' + guide +  '.txt', sep = '\t', names = col_list)
    # df.drop(df.columns[[-1,]], axis=1, inplace=True)         #NOTE Drop the Correct Guide column
    cols = [{"name": i, "id": i, 'type':t, 'hideable':True} for i,t in zip(col_list, col_type)]
    
    final_list.append(          
        html.Div( 
            dash_table.DataTable(
                id='table-position-target', 
                columns=cols, 
                #data = df.to_dict('records'),
                virtualization = True,
                fixed_rows={ 'headers': True, 'data': 0 },
                #fixed_columns = {'headers': True, 'data':1},
                style_cell={'width': '150px'},
                page_current=0,
                page_size=PAGE_SIZE,
                page_action='custom',
                sort_action='custom',
                sort_mode='multi',
                sort_by=[],
                filter_action='custom',
                filter_query='',
                style_table={
                    'height': '600px'
                    #'overflowY': 'scroll',
                },
                style_data_conditional=[
                    {
                        'if': {
                                'filter_query': '{Variant unique} eq y', 
                                #'column_id' :'{#Bulge type}',
                                #'column_id' :'{Total}'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        }
                ],
                export_format = 'csv',
                css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],
                
            ),
            id = 'div-result-table',
        )
    )
    return html.Div(final_list, style = {'margin':'1%'})

#Filter/sort cluster
#Filter and sorting sample targets
@app.callback(
    Output('table-position-target', 'data'),
    [Input('table-position-target', "page_current"),
     Input('table-position-target', "page_size"),
     Input('table-position-target', 'sort_by'),
     Input('table-position-target', 'filter_query')],
    [State('url', 'search'),
     State('url', 'hash')]    
)
def update_table_cluster(page_current, page_size, sort_by, filter, search, hash):
    job_id = search.split('=')[-1]
    hash = hash.split('#')[1]
    guide = hash[:hash.find('-Pos-')]
    chr_pos = hash[hash.find('-Pos-') + 5:]
    chromosome = chr_pos.split('-')[0]
    position = chr_pos.split('-')[1]
    
    with open('Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
    
    filtering_expressions = filter.split(' && ')
    dff = global_store_general('Results/' + job_id + '/' + job_id + '.' + chromosome + '_' + position + '.' + guide +  '.txt')

    #TODO inserire colonne corrette in base al tipo di ricerca
    dff.rename(columns ={0:'Bulge Type', 1:'crRNA', 2:'DNA', 3:'Chromosome', 4:'Position', 5:'Cluster Position', 6:'Direction',
        7:'Mismatches', 8:'Bulge Size', 9:'Total', 10:'Min_mismatches', 11:'Max_mismatches', 12: 'PAM disruption', 13:'PAM creation', 14 : 'Variant unique', 15:'Samples', 16:'Correct Guide',17:'Top Subcluster'} , inplace = True)
    dff.drop(dff.columns[[-1,]], axis=1, inplace=True)         #NOTE Drop the Correct Guide column
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

    #Calculate sample count
    
    data_to_send=dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')
    for row in data_to_send:
        summarized_sample_cell = dict()
        for s in row['Samples'].split(','):
            if s == 'n':
                break
            try:
                summarized_sample_cell[dict_pop_to_superpop[dict_sample_to_pop[s]]] += 1
            except:
                summarized_sample_cell[dict_pop_to_superpop[dict_sample_to_pop[s]]] = 1
        if summarized_sample_cell:
            row['Samples Summary'] = ', '.join([str(summarized_sample_cell[sp]) + ' ' + sp for sp in summarized_sample_cell])
        else:
            row['Samples Summary'] = 'n'
    return data_to_send

if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run_server(host='0.0.0.0', debug=True, port=8080)
    cache.clear()       #delete cache when server is closed

    #BUG quando faccio scores, se ho dei char IUPAC nei targets, nel terminale posso vedere 150% 200% etc perche' il limite massimo e' basato su wc -l dei targets, ma possono aumentare se ho molti
    #Iupac
    #TODO se cancello il chr nel filter by position, non vedo nessun risultato -> fare in modo che metta risultati originali -> da controllare con risultati più grandi
    #BUG quando visualizzo per samples, la colonna pam creation/ pam disruption possono risultare non accurate in quanto non ho iupac ma il
    #carattere esatto. Inoltre alcuni samples non possono esistere in quanto la pam non è NGG (o quella selezionata dall'utente)
    #BUG nel filtering se ho, in min mismatch etc, la stringa '-', che non è considerata numero
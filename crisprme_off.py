'''
CRISPRme performs predictive analysis and result assessment on population and individual specific CRISPR/Cas experiments. 
CRISPRme enumerates on- and off-target accounting simultaneously for substitutions, DNA/RNA bulges and common genetic variants from the 1000 
genomes project. CRISPRme is based on CRISPRitz (Cancellieri, Samuele, et al. "Crispritz: rapid, high-throughput, and variant-aware in silico off-target site identification for crispr genome editing." Bioinformatics (2019).) 
a software tool for population target analyses. CRISPRme is devoted to individual specific on- and off-target analyses.

Documentation updated up to 07/07/2020

Launch crisprme:

+ python3 crisprme_off.py
+ gunicorn -b :8080 crisprme_off:app.server

Generate docs:

+ pdoc crisprme_off.py -o docsCrisprme/ --force --html
'''
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
from additional_pages import help_page
from additional_pages import contacts_page
from additional_pages import genomes_page as gen_page
import re                                   #For sort chr filter values
import concurrent.futures                           #For workers and queue
import math
from PostProcess.supportFunctions.loadSample import associateSample
from PostProcess import CFDGraph
from additional_pages import get_genomes
try:
    from GUI import GUImessage as Gmsg
except ImportError:
    pass
import webbrowser as wb     #Open CRISPRme on browser

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True

from tkinter import filedialog, END, IntVar, messagebox

#Warning symbol \u26A0
app_location = os.path.realpath(__file__)
app_main_directory = os.path.dirname(app_location) + '/'    #This for scripts
current_working_directory = os.getcwd() + '/'               #This for files

exeggutor = concurrent.futures.ProcessPoolExecutor(max_workers=2)

PAGE_SIZE = 10                    #number of entries in each page of the table in view report
BARPLOT_LEN = 4                   #number of barplots in each row of Populations Distributions
#Columns for dash datatable in REF search
COL_REF = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Cluster Position' ,'Direction', 'Mismatches', 'Bulge Size', 'Total', 'Annotation Type']
COL_REF_TYPE = ['text','text','text','text','numeric', 'numeric','text','numeric', 'numeric', 'numeric', 'text']
COL_REF_RENAME = {0:'Bulge Type', 1:'crRNA', 2:'DNA', 3:'Chromosome', 4:'Position', 5:'Cluster Position', 6:'Direction',
                7:'Mismatches', 8:'Bulge Size', 9:'Total',10:'Correct Guide', 11:'Annotation Type'}
#Columns for dash datatable in VAR and BOTH search
COL_BOTH = ['Bulge Type', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Cluster Position','Direction', 'Mismatches', 'Bulge Size', 'Total', 'PAM Creation', 'Samples Summary', 'Annotation Type']
COL_BOTH_TYPE = ['text','text','text','text','numeric','numeric', 'text','numeric', 'numeric', 'numeric', 'text', 'text', 'text']
COL_BOTH_RENAME = {0:'Bulge Type', 1:'crRNA', 2:'DNA', 3:'Chromosome', 4:'Position', 5:'Cluster Position', 6:'Direction',
        7:'Mismatches', 8:'Bulge Size', 9:'Total', 10:'PAM Creation', 11 : 'Variant Unique', 12:'Samples', 13:'Annotation Type', 14:'Correct Guide'}
GENOME_DATABASE = ['Reference', 'Enriched', 'Samples', 'Dictionary', 'Annotation']
ONLINE = False              #NOTE change to True for online version, False for offline
if ONLINE:
    DISPLAY_OFFLINE = 'none'
    DISPLAY_ONLINE = ''
else:
    DISPLAY_OFFLINE = ''
    DISPLAY_ONLINE = 'none'
VALID_CHARS = {'a', 'A', 't', 'T', 'c', 'C','g', 'G',
            "R",
            "Y",
            "S",
            "W",
            "K",
            "M",
            "B" ,
            "D" ,
            "H" ,
            "V" ,
            "r",
            "y",
            "s",
            "w",
            "k",
            "m",
            "b" ,
            "d" ,
            "h" ,
            "v"
            }
URL = 'http://157.27.85.10:8050'       #Change for online version
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'CRISPRme'
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
# population_1000gp = {
#     'EAS':['CHB', 'JPT', 'CHS', 'CDX', 'KHV'],
#     'EUR':['CEU', 'TSI', 'FIN', 'GBR', 'IBS'],
#     'AFR':['YRI', 'LWK', 'GWD', 'MSL', 'ESN', 'ASW', 'ACB'],
#     'AMR':['MXL', 'PUR', 'CLM', 'PEL'],
#     'SAS':['GIH', 'PJL', 'BEB', 'STU', 'ITU']
# }
# dict_pop_to_superpop = {'CHB':'EAS', 'JPT':'EAS', 'CHS':'EAS', 'CDX':'EAS', 'KHV':'EAS',
#                     'CEU':'EUR', 'TSI':'EUR', 'FIN':'EUR', 'GBR':'EUR', 'IBS':'EUR',
#                     'YRI':'AFR', 'LWK':'AFR', 'GWD':'AFR', 'MSL':'AFR', 'ESN':'AFR', 'ASW':'AFR', 'ACB':'AFR',
#                     'MXL':'AMR', 'PUR':'AMR', 'CLM':'AMR', 'PEL':'AMR',
#                     'GIH':'SAS', 'PJL':'SAS', 'BEB':'SAS', 'STU':'SAS', 'ITU':'SAS'
# }
#List of all samples
# pop_file = pd.read_excel(os.path.dirname(os.path.realpath(__file__)) + '/PostProcess/20130606_sample_info.xlsx')
# all_samples = pop_file.Sample.to_list()
# all_pop = pop_file.Population.to_list()
# dict_pop = dict()
# dict_sample_to_pop = dict()
# for  pos, i in enumerate(all_pop):
    # try:
    #     dict_pop[i].append(all_samples[pos])
    # except:
    #     dict_pop[i] = [all_samples[pos]]
    
    # dict_sample_to_pop[all_samples[pos]] = i
# dropdown_all_samples = [{'label': sam, 'value' : sam} for sam in all_samples]
#Dropdown available genomes
def availableGenomes():
    '''
    Returns a list of dictionaries of the available genomes in the 'Genomes' directory.

    ***Returns***

    + **gen_dir** (*list* of {'label': genome, 'value': genome}): list containing a series of dictionaries, one for each directory (genome) found in
    the 'Genomes' directory. Used as input parameter for the 'options' element of a Dash Droplist 
    '''
    onlydir = [f for f in listdir(current_working_directory + 'Genomes') if isdir(join(current_working_directory + 'Genomes', f))]
    onlydir = [x.replace('_', ' ') for x in onlydir]
    gen_dir = []
    for dir in onlydir:
        gen_dir.append({'label': dir, 'value' : dir})
    return gen_dir

#Dropdown available PAM
def availablePAM():
    '''
    Returns a list of dictionaries of the available PAMs in the 'PAM' directory.

    ***Returns***
    
    + **pam_file** (*list* of {'label': pam, 'value': pam}): list containing a series of dictionaries, one for each PAM file found in
        the 'PAM' directory. Used as input parameter for the 'options' element of a Dash Droplist
    '''
    onlyfile = [f for f in listdir(current_working_directory + 'pam') if isfile(join(current_working_directory + 'pam', f))]
    onlyfile = [x.replace('.txt', '') for x in onlyfile]            #removed .txt for better visualization
    pam_file = []
    for pam_name in onlyfile:
        if 'tempPAM' in pam_name:   #Skip the temp pam used for updating dictionaries
            pass
        else:
            pam_file.append({'label':pam_name, 'value':pam_name})
    return pam_file

#Available mismatches and bulges
if ONLINE:
    set_max_mms = 7
    set_max_bulges = 3
else:
    set_max_mms = 7             #NOTE modify value for increasing/decreasing max mms or bulges available on Dropdown selection
    set_max_bulges = 3

av_mismatches = [{'label': i, 'value': i} for i in range(0, set_max_mms)]
av_bulges = [{'label': i, 'value': i} for i in range(0, set_max_bulges)]
av_guide_sequence = [{'label': i, 'value': i} for i in range(15, 26)]
search_bar = dbc.Row(
    [
        #dbc.Col(dbc.Input(type="search", placeholder="Search")),
        dbc.Col(dbc.NavLink(
            html.A('HOME', href = URL, target = '_blank', style = {'text-decoration':'none', 'color':'white'}), 
            active = True, 
            className= 'testHover', style = {'text-decoration':'none', 'color':'white', 'font-size':'1.5rem'})),
        dbc.Col(dbc.NavLink(
            html.A('MANUAL', href = URL + '/user-guide',target = '_blank', style = {'text-decoration':'none', 'color':'white'}), 
            active = True, 
            className= 'testHover', style = {'text-decoration':'none', 'color':'white', 'font-size':'1.5rem'})),
        dbc.Col(dbc.NavLink(
            html.A('CONTACTS', href = URL + '/contacts', target = '_blank', style = {'text-decoration':'none', 'color':'white'}),
            active = True, 
            className= 'testHover', style = {'text-decoration':'none', 'color':'white', 'font-size':'1.5rem'})),
        dbc.Col(dbc.NavLink(
            html.A('GENOMES', href = URL + '/genomes', target = '_blank', style = {'text-decoration':'none', 'color':'white'}),
            active = True, 
            className= 'testHover', style = {'text-decoration':'none', 'color':'white', 'font-size':'1.5rem', 'display':DISPLAY_OFFLINE})),
        dbc.Col(dbc.NavLink(
            html.A('HISTORY', href = URL + '/history', target = '_blank', style = {'text-decoration':'none', 'color':'white'}),
            active = True, 
            className= 'testHover', style = {'text-decoration':'none', 'color':'white', 'font-size':'1.5rem', 'display':DISPLAY_OFFLINE}))
    ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)
PLOTLY_LOGO = 'assets/37143442.png'#"https://images.plot.ly/logo/new-branding/plotly-logomark.png"   


navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src=PLOTLY_LOGO, height="60px")),
                    dbc.Col(dbc.NavbarBrand("CRISPRme", className="ml-2", style = {'font-size': '30px'}))
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
def indexPage():
    '''
    Creates the layout of the main page ('/'). The creation of the main page is put under a function in order to reload the genome and pam dropdown
    if a new genome is added, simply by reloading the page.

    ***Returns***

    + **index_page** (*list*): list of html, dcc and dbc components for the layout.
    '''
    final_list = []
    final_list.extend([
        html.Div([
            'CRISPRme  performs  predictive analysis and result assessment on population and individual specific CRISPR/Cas experiments.' +  
            ' CRISPRme enumerates on- and off-target accounting simultaneously for  substitutions, DNA/RNA bulges and common genetic variants from the 1000 genomes project.'+
            ' CRISPRme is based on CRISPRitz [1] a software tool for population target analyses.'  
        + ' CRISPRme is devoted to individual specific on- and off-target analyses.'
        ]),
        ])

    final_list.append(
        html.Div(
            [
                # html.P(['Download the offline version here: ', html.A('InfOmics/CRISPRitz', href = 'https://github.com/InfOmics/CRISPRitz', target="_blank"), ' or ', html.A('Pinellolab/CRISPRitz', href = 'https://github.com/pinellolab/CRISPRitz', target="_blank") ])
                html.Br()
            ]
        )
    )
    checklist_div = html.Div(
        [
            dbc.FormGroup(
                [
                    dbc.Checkbox(
                        id="checkbox-gecko", className="form-check-input", checked = True
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
        style = {'width':'450px'} #NOTE same as text-area
    )
    tab_sequence_content = html.Div(
        [
            html.P(['Search crRNAs by inserting one or more genomic sequences.', html.P('Chromosome ranges can also be supplied')],
            style = {'word-wrap': 'break-word'}), 

            dcc.Textarea(id = 'text-sequence', placeholder = '>sequence 1\nAAGTCCCAGGACTTCAGAAGagctgtgagaccttggc\n>sequence2\nchr1:11,130,540-11,130,751', style = {'width':'450px', 'height':'160px', 'font-family':'monospace', 'font-size':'large'}),
            dbc.FormText('Note: a maximum number of 1000 characters can be provided', color = 'secondary')
        ],
        style = {'width':'450px'} #NOTE same as text-area
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
                                    html.P([html.Button(html.P("Load example", style={'color':'rgb(46,140,187)','text-decoration-line': 'underline', 'font-size':'initial'}), id='example-parameters',
                                                style={ 'border': 'None', 'text-transform': 'capitalize','height':'12','font-weight': '500', 'padding': '0 0px','textcolor':'blu'}), ' - ',
                                    #html.Br(),
                                    html.Button(html.P(children="Reset", style={'color':'rgb(46,140,187)','text-decoration-line': 'underline','font-size':'initial'}), id='remove-parameters',
                                                style={'border': 'None', 'text-transform': 'capitalize','height':'12','font-weight': '500', 'padding': '0 0px'})])
                                ], style = {'display':DISPLAY_ONLINE})
                            ], className = 'flex-div-insert-delete-example'), 
                            
                            html.P(html.P('Select a genome') ),
                            html.Div(
                                dcc.Dropdown(options = availableGenomes(), clearable = False, id = "available-genome",) #style = {'width':'75%'})
                            ),
                            dbc.FormText('Note: Genomes enriched with variants are indicated with a \'+\' symbol', color='secondary'),
                            
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.P(html.P('Select PAM')),
                                            html.Div(
                                                dcc.Dropdown(options = availablePAM(), clearable = False, id = 'available-pam')
                                            )
                                        ],
                                        style = {'flex':'0 0 100%', 'margin-top': '10%'}
                                    )
                                ],
                                id = 'div-pam',
                                className = 'flex-div-pam'
                            ),
                            html.Br(),
                            html.Button("Add New Genome", id = 'add-genome', style = {'margin-right':'5px', 'display':DISPLAY_OFFLINE}),
                            html.Div('', id = 'genome-job', style = {'display':'none'}),
                            html.Button("Update dictionary", id = 'update-dict', style = {'margin-left':'5px', 'display':DISPLAY_OFFLINE}),
                            html.Div('', id = 'dict-job', style = {'display':'none'}),
                            html.Div(
                                [
                                    html.Ul(
                                        [html.Li(
                                            [html.A('Contact us', href = URL + '/contacts', target="_blank"),' to request new genomes availability in the dropdown list'],
                                            style = {'margin-top':'5%', 'display': DISPLAY_ONLINE}
                                        ),
                                        ],
                                        style = {'list-style':'inside'}
                                    ),
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
                                style = {'display': DISPLAY_ONLINE}
                            ),
                            dbc.Fade(
                                [
                                    dbc.FormGroup(
                                        [
                                            dbc.Label("Email", html_for="example-email"),
                                            dbc.Input(type="email", id="example-email", placeholder="Enter email", className='exampleEmail')
                                        ]
                                    )
                                ],
                                id = 'fade', is_in= False, appear= False, 
                            ),
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
    final_list.append(html.Br())
    final_list.append(html.P('[1] Cancellieri, Samuele, et al. \"Crispritz: rapid, high-throughput, and variant-aware in silico off-target site identification for crispr genome editing.\" Bioinformatics (2019).'))
    final_list.append(
        html.P(['Download CRISPRitz here: ', html.A('InfOmics/CRISPRitz', href = 'https://github.com/InfOmics/CRISPRitz', target="_blank"), ' or ', html.A('Pinellolab/CRISPRitz', href = 'https://github.com/pinellolab/CRISPRitz', target="_blank") ])
    )
    index_page = html.Div(final_list, style = {'margin':'1%'})
    return index_page

#Load Page
final_list = []
final_list.append(
    html.Div(
        html.Div(
            html.Div(
                [
                    html.P('Job submitted. Copy this link to view the status and the result page '),
                    html.Div(
                        html.P('link', id = 'job-link', style = {'margin-top':'0.75rem', 'font-size':'large'}),
                        style = {'border-radius':'5px','border':'2px solid', 'border-color':'blue' ,'width':'100%','display':'inline-block', 'margin':'5px'}
                    ),
                    html.P('Results will be kept available for 3 days')
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
                                html.Li('Processing data'),
                                #html.Li('Annotating result'),
                                html.Li('Generating report')
                            ]
                        ),
                        style = {'flex':'0 0 20%'}
                    ),
                    html.Div(
                        html.Ul(
                            [
                                html.Li('To do', style = {'color':'red'}, id = 'search-status'),
                                html.Li('To do', style = {'color':'red'}, id = 'post-process-status'),
                                #html.Li('To do', style = {'color':'red'}, id = 'annotate-result-status'),
                                html.Li('To do', style = {'color':'red'}, id = 'generate-report-status')
                            ],
                            style = {'list-style-type':'none'}
                        )
                    )
                ],
                className = 'flex-status'
            ),
            html.Div(
                [
                    dcc.Link('View Results', style = {'visibility':'hidden'}, id = 'view-results', href = URL),
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


#Test page, go to /test-page to see 
def test_page():
    final_list = []
    final_list.append(html.Div(id='test-div-for-button'))
    final_list.append(
        html.H3('Genomes')
    )
    final_list.append(
        html.P('Select one of the two available Tabs and fill in the field to add a new Genome or to update and existing dictionary.')
    )

    #Check if an already processing add new genome is currently active. If yes, set the button to be disabled
    already_processing = False
    status_label = 'Status: No Job Submitted'
    status_value = 0
    style_disabled = {}
    if isfile(current_working_directory + 'Genomes/' + 'aggiunta_nuovo_genoma.txt' ):
        already_processing = True
        style_disabled = {'background-color':'darkgrey'}
        with open(current_working_directory + 'Genomes/' + 'aggiunta_nuovo_genoma.txt') as info_status:
            status_general = next(info_status).strip().split(' ') #Get current step number [0] and step name [1] on accessing page for first time
            status_label = 'Status: ' + status_general[1]
            status_value = int(status_general[0]) * 25

    new_genome_content = html.Div(
        [
            html.Br(),
            html.P('1) Select a Reference Genome'),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(html.Button('Select Reference Genome Directory', id = 'button-select-refgenome')),
                                    dbc.Col(html.P('Selected: None', id = 'selected-referencegenome'))
                                ]
                            )  
                        ]
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(html.Button('Select PAM File', id = 'button-select-pam')),
                                    dbc.Col(html.P('Selected: None', id = 'selected-pamfile'))
                                ]
                            )  
                        ]
                    ),
                    
                ]
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(html.Button('Select Annotation File', id = 'button-select-annotation')), 
                                    dbc.Col(html.P('Selected: None', id = 'selected-annotationfile'))
                                ]
                            ),
                            
                        ]
                    ),
                    dbc.Col(
                            dbc.Row(
                                [
                                    dbc.Col(dcc.Input(placeholder = 'Select number of max Bulges', type = 'number', min = 0, id = 'input-max-bulges'))
                                ]
                            )
                        )

                ]
            ),
            html.Hr(),
            html.P('2) (Optional) Enrich the previously selected Reference Genome with samples informations'),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(html.Button('Select VCFs Directory', id = 'button-select-vcf')),
                                    dbc.Col(html.P('Selected: None', id = 'selected-vcf'))
                                ]
                            )  
                        ]
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(html.Button('Select Samples ID File', id = 'button-select-sampleID')), 
                                    dbc.Col(html.P('Selected: None', id = 'selected-sampleIDfile'))
                                ]
                            ),
                            
                        ]
                    )
                ]
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Col(html.P('Enriched Genome Name')),
                                dbc.Col(dcc.Input(placeholder = 'Example: 1000genomeproject', id = 'input-enriched-name'))
                            ]
                        )
                    )
                ]
            ),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(
                        html.Button('Start add new genome', id = 'button-add-new-genome', disabled = already_processing, style = style_disabled)
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                dbc.Col(
                                    html.P(status_label, id = 'status-add-new-genome')
                                )
                            ),
                            dbc.Row(
                                dbc.Col(
                                    html.Div(
                                        [
                                            dbc.Progress(value = status_value, id = 'progress-add-new-genome'),
                                            dcc.Interval(interval = 30*1000,id='interval-add-new-genome')
                                        ]
                                    )
                                )
                            )
                        ]
                    )
                ]
            )
        ]
    )

    update_dictionary_content = html.Div() #TODO finire con layout simile a quello per aggiungere nuovo genoma

    final_list.append(
        dbc.Tabs(
            [
                dbc.Tab(new_genome_content, label='Add New Genome', tab_id= 'add-genome-tab'),
                dbc.Tab(update_dictionary_content, label='Update Dictionary', tab_id = 'update-dictionary')
            ],
            active_tab='add-genome-tab',
            id = 'tabs-new-genome-or-dictionary'
        )
    )

    final_list.append(html.Div(id = 'div-targetoutput', style = {'display':'none'}))
    return html.Div(final_list, style = {'margin':'1%'})
# test_page = html.Div(final_list, style = {'margin':'1%'})

#TEST PAGE 2
final_list = []

test_page2 = html.Div(final_list, style = {'margin':'1%'})

#TEST page3 for new result page
final_list = []

test_page3 = html.Div(final_list, style = {'margin':'1%'})

#ABOUT PAGE

about_page =  html.Div(help_page.helpPage(), style = {'margin':'1%'})
#Contacts page
final_list = []
contacts_page =  html.Div(contacts_page.contactPage(), style = {'margin':'1%'})



##################################################CALLBACKS##################################################
#Test callbacks


#General function for selecting a Directory or a file
def openDialog(n, type_ask, start_dir = './'):
    if n is None:
        raise PreventUpdate
    root = tk.Tk()
    root.withdraw()
    if type_ask == 'D':
        selected = filedialog.askdirectory(initialdir = current_working_directory + start_dir)
    else:
        selected = filedialog.askopenfilename(initialdir = current_working_directory + start_dir)
    root.destroy()
    if selected == '' or selected == '()':
        selected = 'None'
    return str(selected)

#Callbacks for generating filebrowser for addition of new genome
@app.callback(
    Output('selected-referencegenome', 'children'),
    [Input('button-select-refgenome','n_clicks')]
)
def fileDialogRefGenome(n):
    return 'Selected: ' + openDialog(n, 'D','Genomes')

@app.callback(
    Output('selected-pamfile', 'children'),
    [Input('button-select-pam','n_clicks')]
)
def fileDialogPam(n):
    return 'Selected: ' + openDialog(n, 'F') 

@app.callback(
    Output('selected-annotationfile', 'children'),
    [Input('button-select-annotation','n_clicks')]
)
def fileDialogAnnotation(n):
    return 'Selected: ' + openDialog(n, 'F','annotations') 

@app.callback(
    Output('selected-vcf', 'children'),
    [Input('button-select-vcf','n_clicks')]
)
def fileDialogVCF(n):
    return 'Selected: ' + openDialog(n, 'D')

@app.callback(
Output('selected-sampleIDfile', 'children'),
[Input('button-select-sampleID','n_clicks')]
)
def fileDialogSamplesID(n):
    return 'Selected: ' + openDialog(n, 'F','samplesID')  

#Callback creazione nuovo genoma
@app.callback(
    Output('div-targetoutput','children'),
    [Input('button-add-new-genome', 'n_clicks')]
)
def startAddNewGenome(n):
    if n is None:
        raise PreventUpdate
    #TODO: prende gli state dei valori selezionati dall'utente e controlla se sono stati tutti selezionati, altrimenti fa comparire un 
    #avviso che manca qualcosa (cfr. funzione checkInput, ma basta solo avere l'elenco dei campi da compilare)
    #...
    #...

    #input corretti
    #Faccio un subprocess.Popen facendo partire lo script per generare il nuovo genoma
    #Lo script.sh crea un file nella cartella Genomes chiamato 'status_creation_nomegenoma.txt' dove nomegenoma è ref o enr in base alla
    #selezione dell'utente
    #In questo script faccio echo dei vari step in cui sono in questo momento con l'analisi, in modo poi da leggere questo file e con un interval
    #dire all'utente a che punto siamo
    print('Button clicked')
    subprocess.Popen([app_main_directory + 'PostProcess/aggiunta_genoma_test_script.sh', current_working_directory])
    return ''

#Callback per aggiornare la barra progresso
@app.callback(
    [Output('progress-add-new-genome', 'value'),
    Output('status-add-new-genome','children'),
    Output('button-add-new-genome', 'disabled'),
    Output('button-add-new-genome', 'style')],
    [Input('interval-add-new-genome','n_intervals'),
    Input('button-add-new-genome','n_clicks')]
)
def updateStatusCreateNewGenome(n, n_button):   
    if n is None and n_button is None:
        raise PreventUpdate
    

    context = dash.callback_context.triggered[0]['prop_id'].split('.')[0] #id of input that triggered callback
    if context == 'button-add-new-genome':
        return 0, 'Status: Copy Genome', True,  {'background-color':'darkgrey'}
    #TODO questa funzione legge il file creato dalla funzione startAddNewGenome e in base allo step in cui siamo (Copia file, indicizzazione, enrichment etc)
    #ritorna in output una valore della barra (eg +25 per ogni step fatto) e lo step a cui siamo (eg Status: Enrichment Genome)
    
    #controlla se esiste il file aggiunta nuovo genoma, e aggiorna la barra e mette il bottone a Disabled = True
    if isfile(current_working_directory + 'Genomes/aggiunta_nuovo_genoma.txt'):
        with open(current_working_directory + 'Genomes/aggiunta_nuovo_genoma.txt') as info_status:
            a = next(info_status).strip().split(' ') #Get current step number [0] and step name [1]
            if 'Done' == a[1]:
                subprocess.run(['rm', current_working_directory + 'Genomes/' + 'aggiunta_nuovo_genoma.txt'])
                return 100, 'Status: Done', False, {}
        return str(int(a[0]) * 25), 'Status: ' + a[1], True,  {'background-color':'darkgrey'}
    return 0 , 'Status: No Job Submitted', False, {}
#################################################
#Fade in/out email
@app.callback(
    Output("fade", "is_in"),
    [Input("checklist-advanced", "value")],
    [State("fade", "is_in")],
)
def toggle_fade(selected_options, is_in):
    '''
    Manages the fading of the InputBox for the email when the option 'Notify me by email' is selected/deselected.

    ***Args***

    + [**selected_options**] **checklist-advanced** (*value*): list of IDs of the options checked
    + [**is_in**] **fade** (*is_in*): True if the Input email element is displayed, False otherwise

    ***Returns***

    + **fade** (*is_in*): True in order to show the Input email element, False to hide it
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
    Inserts an example value in all fields to show the user an example result, or reset the input fields. NOT available in OFFLINE version.
    
    ***Args***

    + [**nI**] **example-parameters** (*n_clicks_timestamp*): button that inserts the example values
    + [**nR**] **remove-parameters** (*n_clicks_timestamp*): button that removes the values and resets all the fields

    ***Returns***

    + **available-genome** (*value*): 'hg38 ref+hg38 1000genomeproject' as input example, or '' to reset the value
    + **available-pam** (*value*): '20bp-NGG-SpCas9' as input example, or '' to reset the value
    + **text-guides** (*value*): 'GAGTCCGAGCAGAAGAAGAA\\nCCATCGGTGGCCGTTTGCCC' as input example, or '' to reset the value
    + **mms** (*value*): '4' as input example, or '' to reset the value
    + **dna** (*value*): '1' as input example, or '' to reset the value
    + **rna** (*value*): '1' as input example, or '' to reset the value
    + **len-guide-sequence-ver** (*value*): '20' as input example, or '' to reset the value
    + **text-sequence** (*value*): '>sequence\\nTACCCCAAACGCGGAGGCGCCTCGGGAAGGCGAGGTGGGCAAGTTCAATGCCAAGCGTGACGGGGGA' as input example,
    or '' to reset the value
    '''

    if (nI is None) and (nR is None):
        raise PreventUpdate

    if nI is None:
        nI = 0

    if nR is None:
        nR = 0
    
    if nI > 0:
        if nI > nR:
            return 'hg38 ref+hg38 1000genomeproject', '20bp-NGG-SpCas9', 'GAGTCCGAGCAGAAGAAGAA\nCCATCGGTGGCCGTTTGCCC', '4', '1', '1', '20', '>sequence\nTACCCCAAACGCGGAGGCGCCTCGGGAAGGCGAGGTGGGCAAGTTCAATGCCAAGCGTGACGGGGGA'


    if nR > 0:
        if nR > nI:
            return '', '', '', '', '', '', '', ''
    
    # return '', '', '', '', '', '', ''

#If selected genome has a '+', update advanced options comparison with reference
@app.callback(
    Output('checkbox-ref-comp', 'checked'),
    [Input('available-genome', 'value')]
)
def suggestComparison(value):
    '''
    Update to Checked the Option 'Compare your results with the corresponding reference genome' if an Enriched Genome is selected ('+' is in the
    name of the genome)

    ***Args***

    + [**value**] **available-genome** (*value*): the name of the genome selected by the user in the Dropdown

    ***Returns***

    + **checkbox-ref-comp** [*checked*]: True if an Enriched genome is selected
    '''
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
    Checks email validity (i.e. an '@' is present) and changes the border to green or red accordingly.

    ***Args***
    
    + [**val**] **example-email** (*value*): string of the email

    ***Returns***

    + **example-email** (*style*): dictionary of the style for the Input email: change border to red (if no '@' in **val**) or to green
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
    Manages the fading of the Dropdown for the guide length when the tab 'Sequence' is active.

    ***Args***

    + [**current_tab**] **tabs** (*active_tab*): string of the ID of the current active tab
    + [**is_in**] **fade-len-guide** (*is_in*): True if the Dropdown guide length element is displayed, False otherwise

    ***Returns***

    + **fade-len-guide** (*is_in*): True in order to show the Dropdown guide length element, False to hide it
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
    Checks the presence and correctness of the input fields, changing their border to red if it's missing and displaying a Modal element with 
    a list of the missing inputs. The callback is triggered when the user clicks on the 'Submit' button or when the modal is closed 
    (by the 'Close' button or by clicking on-screen when the Modal element is open)
    
    ***Args***

    + [**n**] **check-job** (*n_clicks*): button that starts the job after checking the correctness of the input
    + [**n_close**] **close** (*n_clicks*): button that closes the opened modal
    + [**genome_selected**] **available-genome** (*value*): string of the selected genome from the Dropdown. `None` if not selected, '' if selected
    and then deleted
    + [**pam**] **available-pam** (*value*): string of the selected PAM from the Dropdown. `None` if not selected, '' if selected
    and then deleted
    + [**text_guides**] **text-guides** (*value*): string of the input guides from the Textarea. `None` if not selected, '' if selected
    and then deleted
    + [**mms**] **mms** (*value*): int of the selected mismatch value. `None` if not selected, '' if selected
    and then deleted
    + [**dna**] **dna** (*value*): int of the selected DNA bulge value. `None` if not selected, '' if selected
    and then deleted
    + [**rna**] **rna** (*value*): int of the selected RNA bulge value. `None` if not selected, '' if selected
    and then deleted
    + [**len_guide_seq**] **len-guide-sequence-ver** (*value*): int value of the length of the guides (available when 'Sequence' tab is active). `None` if not selected, '' if selected
    and then deleted
    + [**active_tab**] **tabs** (*active_tab*): string of the ID of the active tab ('Guide' or 'Sequence')
    + [**is_open**] **modal** (*is_open*): True if the modal is displayed, false otherwise

    ***Returns***

    + **submit-job** (*n_clicks*): reset the click counter (`None`) if some inputs are missing, else put to `1` in order to trigger the `changeUrl()`
    function and proceed with the job
    + **modal** (*is_open*): `True` if some inputs are missing, `False` otherwise
    + **available-genome** (*className*): string containing the name of the css class for the red-border ('missing-input'), indicating a missing input. `None` if 
    input is ok
    + **available-pam** (*className*): string containing the name of the css class for the red-border ('missing-input'), indicating a missing input. `None` if 
    input is ok
    + **text-guides** (*style*): dictionary for the style element (NOTE not updated if input is missing)
    + **mms** (*className*): string containing the name of the css class for the red-border ('missing-input'), indicating a missing input. `None` if 
    input is ok
    + **dna** (*className*): string containing the name of the css class for the red-border ('missing-input'), indicating a missing input. `None` if 
    input is ok
    + **rna** (*className*): string containing the name of the css class for the red-border ('missing-input'), indicating a missing input. `None` if 
    input is ok
    + **len-guide-sequence-ver** (*className*): string containing the name of the css class for the red-border ('missing-input'), indicating a missing input. `None` if 
    input is ok
    + **warning-list** (*children*): html.Div for the Modal component, listing the missing inputs
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
    
    if genome_selected is None or genome_selected == '':
        genome_update = classname_red
        update_style = True
        miss_input_list.append('Genome')
    if pam is None or pam == '':
        pam_update = classname_red
        update_style = True
        miss_input_list.append('PAM')
    # if text_guides is None or text_guides == '':
        # text_update = {'width':'450px', 'height':'160px','border': '1px solid red'}
        # update_style = True
        # miss_input_list.append('crRNA sequence(s)')
    if mms is None or str(mms) == '':
        mms_update = classname_red
        update_style = True
        miss_input_list.append('Allowed Mismatches')
    if dna is None or str(dna) == '':
        dna_update = classname_red
        update_style = True
        miss_input_list.append('Bulge DNA size')
    if rna is None or str(rna) == '':
        rna_update = classname_red
        update_style = True
        miss_input_list.append('Bulge RNA size')
    if (len_guide_seq is None or str(len_guide_seq) == '') and ('sequence-tab' in active_tab):
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
    Main function that generates the inputs for the Post/Process/submit_job.final.sh script and launches the search analysis.

    ***Args***
    
    + [**n**] **submit-job** (*n_clicks*): this value comes from the output of the `checkInput()` function. If `1`, it means that the inputs are
    correct, and the function can proceed. If `None` it means that some inputs are missing, so a `raise PreventUpdate` is returned.
    + [**href**] **url** (*href*): string for the href part of the url. NOTE not used
    + [**genome_selected**] **available-genome** (*value*): string for the selected genome
    + [**pam**] **available-pam** (*value*): string for the selected PAM
    + [**text_guides**] **text-guides** (*value*): string for the input guides
    + [**mms**] **mms** (*value*): int for the mismatch selected
    + [**dna**] **dna** (*value*): int for the DNA bulge selected
    + [**rna**] **rna** (*value*): int for the RNA bbulge selected
    + [**gecko_opt**] **checkbox-gecko** (*checked*): bool for the GeCKO Checkbox 
    + [**genoma_ref_opt**] **checkbox-ref-comp** (*checked*): bool for the reference genome comparison
    + [**adv_opts**] **checklist-advanced** (*value*): list of advanced options selected (NOTE only email)
    + [**dest_email**] **example-email** (*value*): string of the input email
    + [**active_tab**] **tabs** (*active_tab*): string of the ID of the active tab ('Guide' or 'Sequence')
    + [**text_sequence**] **text-sequence** (*value*): string of the input sequence
    + [**len_guide_sequence**] **len-guide-sequence-ver** (*value*): int of the selected guide len (available only if 'Sequence' tab is active)

    ***Returns***

    + **url** (*pathname*): string '/load' to go to the Load Page
    + **url** (*search*): string '?job=' + the job ID, to check the status of the specific job 

    ***Details***
    
    + 1) (NOTE already done in `checkInput()`) The function checks the validity of the input parameters.
    + 2) In order to differentiante various analysis submissions, an ID is given to each analysis (Job ID), consisting of a string of 10 alphanumeric
    characters (A-Z 0-9). If a generated ID is already assigned, retry and compute another one. Every 7 iterations, add +1 to the length of the
    ID, up to a maximum of 20 chars. Then the JobID directory is created and inside is created a `queue.txt` file in order to implement a job queue
    + 3) The parameters used as input for the submit_job.final.sh script are created based on user input:
        + Email: the email address, link for the results and start date are written in `Genomes/JobID/email.txt`
        + PAM: get PAM len and direction (beginning or end), in order to write the correct files for pam and guides used in Crispritz.
        + Guides: if the 'Sequence' tab is selected, the input is processed in the `extract_seq` module, that returns a list of guides. Non valid 
        characters are then eliminated, along with the exceeding guides (only 1000 guides are acceptable). The guides are then modified by adding
        N characters, following PAM type input (check Crispritz), and saved into file `Genomes/JobID/guides.txt`. The PAM is also saved in the 
        `Genomes/JobID/pam.txt` file, following the Crispritz standard
        + Indexing: if the selected Genome-PAM has no index in `genome_library`, set a flag to calculate the index when submitting the job. The PAM
        used for indexing is `Genomes/JobID/pam_indexing.txt`
        + Params file: the informations about the job are saved into the `Params.txt` file
        + Annotation: based on the selected genome reference part, the annotation is chosen from the `annotations` directory
        + Sample: based on the enriched genome selected, the sampleID file is chosen from the `samplesID` directory 
        + Dictionary: based on the enriched genome selected, the Dictionary for sample extraction is selected from the `dictionaries` directory
    + 4) If the input is equal to an already calculated analysis, then the function modify the job id to the one of the already existing analysis
    (even if it's completed/currently submitted/in queue), update the `email` file and the `log` file (in order to reset the 3 days availability on the server)
    + Launch the submit_job.final.sh script using `exeggutor`, to a max of 2 concurrent jobs, the others are put into a queue
    '''
    if n is None:
        raise PreventUpdate
    
    # 1) Check input, else give simple input
    if genome_selected is None or genome_selected == '':
        genome_selected = 'hg38_ref'
    if pam is None or pam == '':
        pam = '20bp-NGG-SpCas9'
    if text_guides is None or text_guides == '':
        text_guides = 'GAGTCCGAGCAGAAGAAGAA\nCCATCGGTGGCCGTTTGCCC'
    else:
        text_guides = text_guides.strip()
        if ( not all(len(elem) == len(text_guides.split('\n')[0]) for elem in text_guides.split('\n'))):
            text_guides = selectSameLenGuides(text_guides)
    if (len_guide_sequence is None or str(len_guide_sequence) == '') and ('sequence-tab' in active_tab):
        len_guide_sequence = 20
    if (text_sequence is None or text_sequence == '') and ('sequence-tab' in active_tab):
        text_sequence = '>sequence\nTACCCCAAACGCGGAGGCGCCTCGGGAAGGCGAGGTGGGCAAGTTCAATGCCAAGCGTGACGGGGGA'
    
    # 2) Get random string for job id
    n_it = 10
    len_id = 10
    for i in range(n_it):
        assigned_ids = [o for o in os.listdir(current_working_directory + 'Results/') if os.path.isdir(os.path.join(current_working_directory + 'Results/',o))]
        job_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = len_id))
        if job_id not in assigned_ids:
            break
        if i > 7:
            i = 0
            len_id += 1 
            if len_id > 20:
                break
    result_dir = current_working_directory + 'Results/' + job_id
    subprocess.run(['mkdir ' + result_dir], shell = True)
    #NOTE test command per queue
    subprocess.run(['touch ' + current_working_directory + 'Results/' + job_id + '/queue.txt'], shell = True)

    # 3) Set parameters
    generate_index_ref = False
    generate_index_enr = False
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
    if 'email' in adv_opts and dest_email is not None and len(dest_email.split('@')) > 1 and dest_email.split('@')[-1] != '':
        send_email = True
        with open(result_dir + '/email.txt', 'w') as e:
            e.write(dest_email + '\n')
            e.write(URL + '/load?job=' + job_id + '\n')
            e.write(datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S") + '\n')
            #e.write('Job done. Parameters: etc etc')
            e.close()
    
    
    genome_selected = genome_selected.replace(' ', '_')
    genome_ref = genome_selected.split('+')[0]              # + char to separate ref and enr, eg Human_Genome_ref+Human_Genome_1000_genome_project
    if genome_ref == genome_selected:
        ref_comparison = False
    #NOTE Indexed genomes names are PAM + _ + bMax + _ + genome_selected
    
    pam_len = 0
    with open(current_working_directory + 'pam/' + pam + '.txt') as pam_file:
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
            name = name_and_seq[:name_and_seq.find('\n')]
            seq = name_and_seq[name_and_seq.find('\n'):]
            seq = seq.strip().split()
            seq = ''.join(seq)
            # name, seq = name_and_seq.strip().split('\n')    
            if 'chr' in seq:
                extracted_seq = extract_seq.extractSequence(name, seq, genome_ref.replace(' ', '_'))
            else:
                extracted_seq = seq.strip()
            
            guides.extend(convert_pam.getGuides(extracted_seq, pam_char, len_guide_sequence, pam_begin))
            text_guides = '\n'.join(guides).strip()
    
    text_guides = text_guides.upper()
    for g in text_guides.split('\n'):
        for c in g:
            if c not in VALID_CHARS:
                text_guides = text_guides.replace(c,'')
    if len(text_guides.split('\n')) > 1000:
        text_guides = '\n'.join(text_guides.split('\n')[:1000]).strip()
    len_guides = len(text_guides.split('\n')[0])
    #Adjust guides by adding Ns to make compatible with Crispritz
    if (pam_begin):
        pam_to_file = pam_char + ('N' * len_guides) + ' ' + index_pam_value
        pam_to_indexing = pam_char + ('N' * 25) + ' ' + index_pam_value
    else:
        pam_to_file = ('N' * len_guides) + pam_char + ' ' + index_pam_value
        pam_to_indexing = ('N' * 25) + pam_char + ' ' + index_pam_value

    save_pam_file = open(result_dir + '/pam.txt', 'w')
    save_pam_file.write(pam_to_file)
    save_pam_file.close()
    pam = result_dir + '/pam.txt'
        
    guides_file = result_dir + '/guides.txt'
    if text_guides is not None and text_guides != '':
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

    #Check if index exists, otherwise set generate_index to true
    genome_indices_created =  [f for f in listdir(current_working_directory + 'genome_library') if isdir(join(current_working_directory + 'genome_library', f))]
    genome_idx = ''
    genome_idx_ref = ''
    for gidx in genome_indices_created:
        if pam_char in gidx and genome_selected in gidx:
            if int(gidx.split('_')[1]) >= int(max_bulges):
                if '+' in gidx:
                    genome_idx = gidx
                genome_idx_ref = gidx.split('+')[0]
                
    if genome_idx == '':
        if int(max_bulges) > 0:
            generate_index_enr = True
            with open(result_dir + '/pam_indexing.txt', 'w+') as pam_id_file:
                pam_id_file.write(pam_to_indexing)
        genome_idx = pam_char + '_' + str(max_bulges) + '_' + genome_selected
    if genome_idx_ref == '':
        if int(max_bulges) > 0:
            generate_index_ref = True
            with open(result_dir + '/pam_indexing.txt', 'w+') as pam_id_file:
                pam_id_file.write(pam_to_indexing)
        genome_idx_ref = pam_char + '_' + str(max_bulges) + '_' + genome_selected.split('+')[0]

    if genome_ref == genome_selected:
        generate_index_enr = False
    # genome_idx = pam_char + '_' + '2' + '_' + genome_selected   
    # genome_idx_ref = genome_idx.split('+')[0]
    
    #Create Params.txt file
    with open(result_dir + '/Params.txt', 'w') as p:           
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

    # 4) Check if input parameters (mms, bulges, pam, guides, genome) are the same as a previous search
    all_result_dirs = [f for f in listdir(current_working_directory + 'Results') if isdir(join(current_working_directory + 'Results', f))]
    all_result_dirs.remove(job_id)
    #all_result_dirs.remove('test')
    for check_param_dir in all_result_dirs:
        if os.path.exists(current_working_directory + 'Results/' + check_param_dir + '/Params.txt'):
            #if os.path.exists(current_working_directory + 'Results/' + check_param_dir + '/log.txt'):
                #with open(current_working_directory + 'Results/' + check_param_dir + '/log.txt') as log:
                    #if ('Job\tDone' in log.read()):
            if (filecmp.cmp(current_working_directory + 'Results/' + check_param_dir + '/Params.txt', result_dir + '/Params.txt' )):
                    guides1 = open(current_working_directory + 'Results/' + check_param_dir + '/guides.txt').read().split('\n')
                    guides2 = open(current_working_directory + 'Results/' + job_id + '/guides.txt').read().split('\n')
                    if (collections.Counter(guides1) == collections.Counter(guides2)):
                        if os.path.exists(current_working_directory + 'Results/' + check_param_dir + '/log.txt'):
                            adj_date = False
                            with open(current_working_directory + 'Results/' + check_param_dir + '/log.txt') as log:
                                log_content = log.read().strip()
                                if ('Job\tDone' in log_content):
                                    adj_date = True
                                    log_content = log_content.split('\n')
                                    new_date = subprocess.Popen(['echo $(date)'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True)
                                    out, err = new_date.communicate()
                                    rewrite = '\n'.join(log_content[:-1]) + '\nJob\tDone\t' + out.decode('UTF-8').strip()
                            if adj_date:
                                with open(current_working_directory + 'Results/' + check_param_dir + '/log.txt' ,'w+') as log:
                                    log.write(rewrite)
                                    #Send mail
                                if send_email:
                                    with open(current_working_directory + 'Results/' + job_id + '/email.txt' ,'w+') as e:
                                        e.write(dest_email + '\n')
                                        e.write(URL + '/load?job=' + check_param_dir + '\n')
                                        e.write(datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S") + '\n')
                                    #Send mail with file in job_id dir with link to job already done, note that job_id directory will be deleted
                                    subprocess.call(['python3 ' + app_main_directory + 'send_mail.py ' + current_working_directory + 'Results/' + job_id ], shell = True)

                            elif send_email:
                                #Job is not finished, add this user email to email.txt and when job is done send to both
                                if os.path.exists(current_working_directory + 'Results/' + check_param_dir + '/email.txt'):
                                    with open(current_working_directory + 'Results/' + check_param_dir + '/email.txt' ,'a+') as e:
                                        e.write('--OTHEREMAIL--')
                                        e.write(dest_email + '\n')
                                        e.write(URL + '/load?job=' + check_param_dir + '\n')
                                        e.write(datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S") + '\n')
                                else:
                                    with open(current_working_directory + 'Results/' + check_param_dir + '/email.txt' ,'w+') as e:
                                        e.write(dest_email + '\n')
                                        e.write(URL + '/load?job=' + check_param_dir + '\n')
                                        e.write(datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S") + '\n')
                                    

                            subprocess.call(['rm -r ' + current_working_directory + 'Results/' + job_id], shell = True)
                            return '/load','?job=' + check_param_dir
                        else:
                            #We may have entered a jobdir that was in queue
                            if os.path.exists(current_working_directory + 'Results/' + check_param_dir + '/queue.txt'):
                                if send_email:
                                    if os.path.exists(current_working_directory + 'Results/' + check_param_dir + '/email.txt'):
                                        with open(current_working_directory + 'Results/' + check_param_dir + '/email.txt' ,'a+') as e:
                                            e.write('--OTHEREMAIL--')
                                            e.write(dest_email + '\n')
                                            e.write(URL + '/load?job=' + check_param_dir + '\n')
                                            e.write(datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S") + '\n')
                                    else:
                                        with open(current_working_directory + 'Results/' + check_param_dir + '/email.txt' ,'w+') as e:
                                            e.write(dest_email + '\n')
                                            e.write(URL + '/load?job=' + check_param_dir + '\n')
                                            e.write(datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S") + '\n')
                                return '/load','?job=' + check_param_dir

    #Annotation
    if (not search and not search_index):
        annotation = False      

    #Generate report
    if (not search and not search_index):
        report = False         
    
    genome_type = 'ref'     #Indicates if search is 'ref', 'var' or 'both'
    if '+' in genome_selected:
        genome_type = 'var'
    if ref_comparison:
        genome_type = 'both'    

    #Get annotation file, already with the absolute path. TODO currently only one annotation per genome
    #Also get dictionary and sample dictionary files
    annotation_file = [f for f in listdir(current_working_directory + 'annotations/') if isfile(join(current_working_directory + 'annotations/', f)) and f.startswith(genome_ref)][0]
    
    if genome_type == 'ref':
        sample_list = None
        dictionary_directory = None
    else:
        sample_list = current_working_directory + 'samplesID/samples_' + genome_selected + '.txt'
        dictionary_directory = current_working_directory + 'dictionaries/dictionary_' + genome_selected

    command = app_main_directory + 'PostProcess/./submit_job.final.sh ' + current_working_directory + 'Results/' + job_id + ' ' + current_working_directory +  'Genomes/' + genome_selected + ' ' + current_working_directory + 'Genomes/' + genome_ref + ' ' + current_working_directory + 'genome_library/' + genome_idx + (
        ' ' + pam + ' ' + guides_file + ' ' + str(mms) + ' ' + str(dna) + ' ' + str(rna) + ' ' + str(search_index) + ' ' + str(search) + ' ' + str(annotation) + (
            ' ' + str(report) + ' ' + str(gecko_comp) + ' ' + str(ref_comparison) + ' ' + current_working_directory +  'genome_library/' + genome_idx_ref + ' ' + str(send_email) + ' '  + current_working_directory +  'annotations/' + annotation_file + 
            ' ' + genome_type + ' ' + app_main_directory + ' ' + str(dictionary_directory) + ' ' + str(sample_list) + ' ' + str(generate_index_ref) + ' ' + str(generate_index_enr) + ' ' + current_working_directory))

    exeggutor.submit(subprocess.run, command, shell=True)
    return '/load','?job=' + job_id

#When url changed, load new page
@app.callback(
    [Output('page-content', 'children'),
    Output('job-link', 'children')],
    [Input('url', 'href'), Input('url','pathname'), Input('url','search')],[State('url','hash')]
)
def changePage( href, path, search, hash_guide):
    '''
    Change the page layout based on the URL.

    ***Args***

    + [**href**] **url** (*href*): string containing the whole address, eg 'http://127.0.0.1:8080/result?job=QV99PN6XDL#CCATCGGTGGCCGTTTGCCCNNNnewX00'
    + [**path**] **url** (*pathname*): string containing the page, eg '/result'
    + [**search**] **url** (*search*): string containing the job ID, eg '?job=QV99PN6XDL'
    + [**hash_guide**] **url** (*hash*): string containing the view result query, eg '#CCATCGGTGGCCGTTTGCCCNNNnewX00'

    ***Returns***

    + **page-content** (*children*): the layout of the page, based on the URL. 
        + '/': returns the index page (main page)
        + '/load': returns the load page. Called after submitting a job
        + '/result': returns the result page. Based on the job ID in the **search** parameter, the user can also access to:
            + '#GUIDEnew': returns the table visualizing the targets based on Bulge and Mismatch values
            + '-Sample-': returns the table visualizing the targets for each sample
            + '-Pos-': returns the table visualizing the targets based on the selected chromosome position
        + '/user-guide': returns the help page
        + '/contacts': returns the contacts page
        + '/history': returns the history page. Available only offline
        + '/genomes': returns the genomes page. Available only offline
    + **job-link** (*children*): the link displayed to the user in the '/load' page, used to access the status of the job. By saving this URL the
    the user can monitor the status of the job and see the corresponding '/result' page
    '''

    if path == '/load':
        return load_page, URL + '/load' + search 
    if path == '/result':
        job_id = search.split('=')[-1]
        if hash_guide is None or hash_guide == '':
            return resultPage(job_id), URL + '/load' + search
        if 'new' in hash_guide:         #TODO cambiare nome alla pagina delle guide
            return guidePagev3(job_id, hash_guide.split('#')[1]), URL + '/load' + search
        if '-Sample-' in hash_guide:   
            return samplePage(job_id, hash_guide.split('#')[1]), URL + '/load' + search
        if '-Pos-' in hash_guide:
            return clusterPage(job_id, hash_guide.split('#')[1]), URL + '/load' + search
        return resultPage(job_id), URL + '/load' + search
    if path == '/test-page':
        return test_page(), URL + '/load' + search
    if path == '/test-page2':
        return test_page2, URL + '/load' + search
    if path == '/test-page3':
        return test_page3, URL + '/load' + search
    if path == '/user-guide':
        return about_page, URL + '/load' + search
    if path == '/contacts':
        return contacts_page, URL + '/load' + search
    if path == '/history':
        if ONLINE:
            return indexPage(), ''
        return historyPage(), URL + '/load' + search
    if path == '/genomes':
        if ONLINE:
            return indexPage(), ''
        genomes_page = html.Div(gen_page.genomesPage(current_working_directory), style = {'margin':'1%'})
        return genomes_page, URL + '/load' + search
    return indexPage(), ''

#Check end job
@app.callback(
    [Output('view-results', 'style'),
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
    The Interval component of the '/load' page calls this function every 3 seconds. The function checks the status of the submitted job by means
    of the log and output file created and updated by the submit_job.final.sh script, and notifies the user about the current status ('To Do', 'Done' etc.) 
    When the job is completed, a link directing to the '/result' page is shown. If the job doesn't exists or is in the queue,
    a notification will appear. 

    ***Args***

    + [**n**] **load-page-check** (*n_intervals*): element of the Interval component that shows the number of time it has been fired
    + [**dir_name**] **url** (*search*): string containing the job ID, eg '?job=QV99PN6XDL'

    ***Returns***

    + **view-results** (*style*): dictionary for the style element of the link that redirects to the '/result' page. If the job is completed
    then the {'visibility':'visible'} is returned, else {'visibility':'visible'} 
    + **search-status** (*children*): html.P() that contains the status of the search phase. Can be:
        + To Do, red
        + Done, green
        + Currently ongoing, orange
        + Not Available, red
    + **generate-report-status** (*children*): html.P() that contains the status of the generate report. Can be as above
    + **post-process-status** (*children*): html.P() that contains the status of the post process phase. Can be as above
    + **view-results** (*href*): link that redirects to the '/result' page
    + **no-directory-error** (*children*): Alert component that notify the user that the result is not present in the server, or is in the queue
    '''

    if n is None:
        raise PreventUpdate    
    
    onlydir = [f for f in listdir(current_working_directory + 'Results') if isdir(join(current_working_directory + 'Results', f))]
    current_job_dir = current_working_directory + 'Results/' +  dir_name.split('=')[-1] + '/'
    if dir_name.split('=')[-1] in onlydir:
        onlyfile = [f for f in listdir(current_job_dir) if isfile(join(current_job_dir, f))]
        if os.path.exists(current_job_dir + 'guides.txt'):
            with open(current_job_dir + 'guides.txt') as guides:
                n_guides = len(guides.read().strip().split('\n'))
        else:
            n_guides = -1
        if 'log.txt' in onlyfile:
            with open(current_job_dir + 'log.txt') as log:
                all_done = 0
                
                search_status = html.P('To do', style = {'color':'red'})
                report_status = html.P('To do', style = {'color':'red'})
                post_process_status = html.P('To do', style = {'color':'red'})
                current_log = log.read()

                if ('Search-index\tDone' in current_log and 'Search\tDone' in current_log):
                    search_status = html.P('Done', style = {'color':'green'})
                    all_done = all_done + 1
                elif os.path.exists(current_job_dir + 'output.txt'):                #Extract % of search done from output.txt
                    with open(current_job_dir + 'output.txt', 'r') as output_status:
                        line = output_status.read().strip()
                        if 'Indexing_Reference' in line:
                            search_status = html.P('Indexing Reference Genome...' + ' ' + 'Step [1/2]', style = {'color':'orange'})
                        if 'Indexing_Enriched' in line:
                            search_status = html.P('Indexing Enriched Genome...' + ' ' + 'Step [2/2]', style = {'color':'orange'})
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
                            if n_guides < 0:
                                report_status = html.P('Generating Report...', style = {'color':'orange'}) 
                            else:
                                status_message = round((len(line.split('\n')) - 1) / n_guides, 2)
                                report_status = html.P(str(status_message * 100) + '%', style = {'color':'orange'})
                if ('PostProcess\tDone' in current_log):
                    post_process_status = html.P('Done', style = {'color':'green'})
                    all_done = all_done + 1
                elif os.path.exists(current_job_dir + 'output.txt'):                #Extract % of search done
                    with open(current_job_dir + 'output.txt', 'r') as output_status:
                        line = output_status.read().strip()
                        if 'PostProcess_output' in line:
                            line = line.split('\n')
                            if line[-1] == 'PostProcess_output':
                                post_process_status = html.P('Processing data...', style = {'color':'orange'})    
                            else:
                                if 'Annotating...' in line:
                                    last_percent = line[-1].rfind('%')
                                    if last_percent > 0:
                                        last_percent = line[line[:last_percent].rfind(' '): last_percent]
                                        status_message = last_percent + '%'
                                    else:
                                        status_message = 'Annotating...'
                                else:
                                    status_message = line[-1]
                                post_process_status = html.P(status_message, style = {'color':'orange'})
                if all_done == 3 or 'Job\tDone' in current_log:
                    return {'visibility':'visible'},  search_status, report_status, post_process_status ,'/result?job=' + dir_name.split('=')[-1], ''
                else:
                    return {'visibility':'hidden'},  search_status, report_status, post_process_status,'', ''
        elif 'queue.txt' in onlyfile:
            return {'visibility':'hidden'},  html.P('To do', style = {'color':'red'}), html.P('To do', style = {'color':'red'}), html.P('To do', style = {'color':'red'}),'', dbc.Alert("Job submitted. Current status: in queue", color = "info")
    return {'visibility':'hidden'},  html.P('Not available', style = {'color':'red'}), html.P('Not available', style = {'color':'red'}), html.P('Not available', style = {'color':'red'}) ,'', dbc.Alert("The selected result does not exist", color = "danger")

#Perform expensive loading of a dataframe and save result into 'global store'
#Cache are in the Cache directory
@cache.memoize()
def global_store(value):
    '''
    Caching of files, mainly the ones for the 'Show Targets' tables, to improve loading speed. NOTE that if two files have the same name, then the
    generated cache will be the same, so a regular cleaning of the 'Cache' directory is mandatory.

    ***Args***

    + **value**: string of the job ID to load 

    ***Returns***

    + **df**: dataframe for the 'Show Targets' table
    '''
    if value is None:
        return ''
    target = [f for f in listdir(current_working_directory + 'Results/' + value) if isfile(join(current_working_directory + 'Results/'+value, f)) and f.endswith('scores.txt') ]
    if not target:
        target = [f for f in listdir(current_working_directory + 'Results/' + value) if isfile(join(current_working_directory + 'Results/'+value, f)) and f.endswith('targets.txt') ]
    
    df = pd.read_csv(current_working_directory + 'Results/' +value + '/' + target[0], sep = '\t')
    df.rename(columns = {"#Bulge type":'BulgeType', '#Bulge_type':'BulgeType','Bulge Size': 'BulgeSize', 'Bulge_Size': 'BulgeSize', 'Doench 2016':'Doench2016','Doench_2016':'Doench2016'}, inplace = True)
    return df


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
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    guide = hash_guide.split('#')[1]
    value = job_id
    if search is None:
        raise PreventUpdate

    filtering_expressions = filter.split(' && ')
    #filtering_expressions.append(['{crRNA} = ' + guide])     
    df = global_store(value)
    dff = df[df['crRNA'] == guide]

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

    #NOTE sort_by: [{'column_id': 'BulgeType', 'direction': 'asc'}, {'column_id': 'crRNA', 'direction': 'asc'}]
    #sort_by.insert(0, {'column_id' : 'Mismatches', 'direction': 'asc'})
    #sort_by.insert(0, {'column_id' : 'BulgeSize', 'direction': 'asc'})
    if len(sort_by):
        dff = dff.sort_values(
            ['Samples' if col['column_id'] == 'Samples Summary' else col['column_id'] for col in sort_by],
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
        if (last_line == '' or last_line == '\n'):
            no_result = True

    if (no_result):
        warning_no_res = dbc.Alert("No results were found with the given parameters", color = "warning")

     
    return dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')


#For filtering
def split_filter_part(filter_part):
    '''
    Split the input filter, used for Dash DataTables. See https://dash.plotly.com/datatable/filtering
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
    '''
    Read the uploaded file and converts into bit
    '''
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
    '''
    Load the layout based on the selected Tab in the '/result' page

    ***Args***

    + [**value**] **tabs-reports** (*value*): string representing the ID of the active Tab
    + [**sel_cel**] **general-profile-table** (*selected_cells*): list contaning the selected row of the main guide table
    + [**all_guides**] **general-profile-table** (*data*): list of all the rows that are currenty displayed in the main guide table
    + [**search**] **url** (*search*): string containing the job ID, eg '?job=QV99PN6XDL'
    + [**genome_type**] **div-genome-type** (*children*): string containing the type of the search ('ref', 'var' or 'both')

    ***Returns***

    + **div-tab-content** (*children*): return the layout based on the selected Tab:
        + 'tab-summary-by-guide': show the general table of the targets divided by Bulge and Mismatch values
        + 'tab-summary-by-sample': show the general table of the targets divided by sample
        + 'tab-summary-by-position': show the general table of the targets divided by chromosome and position
        + 'tab-summary-graphical': show the graphical report. A total of 10 Buttons, one for each mms value, are created, but only some of them
        are set to be visible (the number of mms selected by the user)
    '''

    if value is None or sel_cel is None or not sel_cel or not all_guides:
        raise PreventUpdate
    
    guide = all_guides[int(sel_cel[0]['row'])]['Guide']
    job_id = search.split('=')[-1]
    job_directory = current_working_directory + 'Results/' + job_id + '/'

    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        mms = (next(s for s in all_params.split('\n') if 'Mismatches' in s)).split('\t')[-1]
        genome_selected = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        max_bulges = (next(s for s in all_params.split('\n') if 'Max_bulges' in s)).split('\t')[-1]

    fl = []
    fl.append(html.Br())
    fl.append(html.H5('Focus on: ' + guide))

    if value == 'tab-summary-by-guide': #BUG se cambio guida selezionata due volte mi cambia il mms mettendo a 0, provare con un div nascosto
        #Show Summary by Guide table
        fl.append(
            html.P(
                ['Summary table counting the number of targets found in the Enriched Genome for each combination of Bulge Type, Bulge Size and Mismatch. Select \'Show Targets\' to view the corresponding list of targets. ', 
                # html.A('Click here', href = URL + '/data/' + job_id + '/' + job_id + '.targets.' + guide + '.zip' ,target = '_blank', id = 'download-full-list' ), ' to download the full list of targets.'
                ]
                )
        )
        fl.append(
            html.Div(
                html.Button(html.A('Download Full list of targets', href = URL + '/data/' + job_id + '/' + job_id + '.targets.' + guide + '.zip' ,target = '_blank', style = {'text-decoration':'none', 'color':'black'} )),
                style = {'display':DISPLAY_ONLINE}
            )
        )
        fl.append(
            html.Div(
                html.Button('Open Result Directory', id = 'button-open-result-directory'),
                style = {'display':DISPLAY_OFFLINE}
            )
        )
        fl.append(html.Div(guide,id = 'div-open-result-directory', style = {'display':'none'}))
        fl.append(html.Br())
        df = pd.read_pickle(job_directory + job_id + '.summary_by_guide.' + guide + '.txt')
        if genome_type == 'both':
            df.drop( df[(df['Bulge Size'] == 0) & ((df['Bulge Type'] == 'DNA') | ((df['Bulge Type'] == 'RNA'))) | ((df['Targets in Reference'] == 0) & (df['Targets in Enriched'] == 0))  ].index, inplace = True)
        elif genome_type == 'var': 
            df.drop( df[(df['Bulge Size'] == 0) & ((df['Bulge Type'] == 'DNA') | ((df['Bulge Type'] == 'RNA'))) | ((df['Targets in Enriched'] == 0))  ].index, inplace = True)
            del df['Targets in Reference']
        else:
            df.drop( df[(df['Bulge Size'] == 0) & ((df['Bulge Type'] == 'DNA') | ((df['Bulge Type'] == 'RNA'))) | ((df['Targets in Reference'] == 0))  ].index, inplace = True)
        more_info_col = []
        total_col = []
        for i in range(df.shape[0]):
            more_info_col.append('Show Targets')
            total_col.append(df['Bulge Size'])

        #Swap pam creation and Combined column
        if genome_type == 'both':   #TODO fixare per var e ref
            df['Combined'] = df['Targets in Reference'] + df['Targets in Enriched']
            #['Guide' 'Bulge Type' 'Bulge Size' 'Mismatches' 'Targets in Reference', 'Targets in Enriched' 'PAM Creation' 'Combined']
            df = df[['Guide' , 'Bulge Type', 'Mismatches', 'Bulge Size' , 'Targets in Reference', 'Targets in Enriched', 'Combined', 'PAM Creation']]
        df[''] = more_info_col
        df['Total'] = df['Bulge Size'] + df['Mismatches']
        if genome_type == 'both' and genome_type == 'var':
            df = df.sort_values(['Total', 'Targets in Enriched'], ascending = [True, False])
        else:
            df = df.sort_values('Total', ascending = True)
        del df['Total']
        del df['Guide']
        fl.append(html.Div(
                generate_table(df, 'table-summary-by-guide', genome_type, guide, job_id ), style = {'text-align': 'center'}
            )
        )
        return fl
    elif value == 'tab-summary-by-sample':
        #Show Summary by Sample table
        fl.append(
            html.P('Summary table counting the number of targets found in the Enriched Genome for each sample. Filter the table by selecting the Population or Superpopulation desired from the dropdowns.')
        )
        if genome_type == 'both':
            col_names_sample = ['Sample', 'Gender', 'Population', 'Super Population',  'Targets in Reference', 'Targets in Enriched', 'Targets in Population', 'Targets in Super Population', 'PAM Creation', 'Class']
            df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
            df = df.sort_values('Targets in Enriched', ascending = False)
            df.drop(['Targets in Reference'], axis = 1, inplace = True)
        else:
            col_names_sample = ['Sample', 'Gender', 'Population', 'Super Population',  'Targets in Reference', 'Targets in Enriched', 'Targets in Population', 'Targets in Super Population', 'PAM Creation', 'Class']
            df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
            df = df.sort_values('Targets in Enriched', ascending = False)
            df.drop(['Targets in Reference'], axis = 1, inplace = True)
            df.drop(['Class'], axis = 1, inplace = True)
        more_info_col = []
        for i in range(df.shape[0]):
            more_info_col.append('Show Targets')
        df[''] = more_info_col
        
        population_1000gp = associateSample.loadSampleAssociation(job_directory + 'sampleID.txt')[2]
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
                                #dbc.Col(html.Div(dcc.Dropdown( id = 'dropdown-sample', placeholder = 'Select a Sample'))),
                                dbc.Col(html.Div(dcc.Input(id = 'input-sample', placeholder = 'Select a Sample' ))),
                                dbc.Col(html.Div(html.Button('Filter', id = 'button-filter-population-sample')))
                            ]
                        ),
                    ],
                    style = {'width':'50%'}
                )
        )
        fl.append(html.Div('None,None,None',id = 'div-sample-filter-query', style = {'display':'none'})) #Folr keep current filter:  Superpop,Pop
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
        max_page = len(df.index)
        max_page = math.floor(max_page / 10) + 1
        fl.append(html.Div('1/' + str(max_page), id= 'div-current-page-table-samples'))
        return fl
    elif value == 'tab-summary-by-position':
        #Show Summary by position table
        fl.append(
            html.P('Summary table containing all the targets found in a specific position of the genome. For each position, the enriched target with the lowest Mismatch + Bulge count is shown (if no target was found in the Enriched Genome, the correspondig reference one is shown), along with his Mismatch and Bulge Size values.' + 
            ' The subtable \'Targets in Cluster by Mismatch Value\' represents the number of targets found in that position for a particular Mismatch-Bulge Size pair.')
        )

        fl.append(
            html.P('Filter the table by selecting the chromosome of interest and writing the start and/or end position of the region to view.')
        )
        #Dropdown chromosomes
        try:
            onlyfile = [f for f in listdir(current_working_directory + 'Genomes/' + genome_selected) if (isfile(join(current_working_directory + 'Genomes/' + genome_selected, f)) and (f.endswith('.fa') or f.endswith('.fasta')))]
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
        #Show first 'normal' chromosomes (chr1) then the others (chr1_KI270706v1_random)
        chr_file.sort(key = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)])
        chr_file_unset.sort(key = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)])
        chr_file += chr_file_unset
        chr_file = [{'label': chr_name, 'value' : chr_name} for chr_name in chr_file]
        
        # Colonne tabella: chr, pos, target migliore, min mm, min bulges, num target per ogni categoria di mm e bulge, show targets; ordine per total, poi mm e poi bulge
        start_time = time.time()
        df = pd.read_csv( job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t')   
        df.rename(columns = {'#Chromosome':'Chromosome'}, inplace = True)
        more_info_col = []
        for i in range(df.shape[0]):
            more_info_col.append('Show Targets')
        df[''] = more_info_col
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
        fl.append(html.Div('None,None,None',id = 'div-position-filter-query', style = {'display':'none'})) #Folr keep current filter:  chr,pos_start,pos_end
        start_time = time.time()
        fl.append(html.Div(
                generate_table_position(df, 'table-position', 1 , int(mms), int(max_bulges), guide, job_id ), style = {'text-align': 'center'}, id = 'div-table-position'
            )
        )
        fl.append(
            html.Div(
                [
                    html.Button('Prev', id = 'prev-page-position'),
                    html.Button('Next', id = 'next-page-position')
                ],
                style = {'text-align': 'center'}
            )
        )
        max_page = len(df.index)
        max_page = math.floor(max_page / 10) + 1
        fl.append(html.Div('1/' + str(max_page), id= 'div-current-page-table-position'))
        fl.append(html.Div(mms + '-' + max_bulges, id = 'div-mms-bulges-position', style = {'display':'none'}))
        return fl
    else:
        #Show Report images
        samp_style = {}
        if genome_type == 'ref':
            samp_style = {'display':'none'}
        
        fl.append(html.Br())
        
        fl_buttons = []
        for i in range (10):
            if (i <= int(mms)): #TODO change into (i <= (int(mms) + int(max_bulges)))
                fl_buttons.append(
                    html.Button(str(i) + ' mm',id = 'btn' + str(i)),       
                )
            else:
                fl_buttons.append(
                    html.Button(str(i) + ' mm',id = 'btn' + str(i), style = {'display':'none'}), #Hide buttons for mms non selected
                )
        
        fl.append(html.Br())

        radar_img = 'summary_single_guide_' + guide + '_' + str(0) + 'mm.png'

        barplot_img = 'summary_histogram_' + guide + '_' + str(0) + 'mm.png'
        try:            #NOTE serve per non generare errori se il barplot non è stato fatto
            barplot_src = 'data:image/png;base64,{}'.format(base64.b64encode(open(current_working_directory + 'Results/' + job_id + '/' + barplot_img, 'rb').read()).decode())
        except:
            barplot_src = ''
        try:
            barplot_href = 'assets/Img/' + job_id + '/' + barplot_img
        except:
            barplot_href = ''

        try:
            radar_src = 'data:image/png;base64,{}'.format(base64.b64encode(open(current_working_directory + 'Results/' + job_id + '/' + radar_img, 'rb').read()).decode())
        except:
            radar_src = ''
        try:
            radar_href = 'assets/Img/' + job_id + '/' + radar_img
        except:
            radar_href = ''
        
        if genome_type != 'ref':
            population_1000gp = associateSample.loadSampleAssociation(job_directory + 'sampleID.txt')[2]
        
            super_populations = [{'label':i, 'value':i} for i in population_1000gp.keys()]
            populations = []
            for k in population_1000gp.keys():
                for i in population_1000gp[k]:
                    populations.append({'label':i, 'value':i})
        else:
            super_populations = []
            populations = [] 

        fl.append(
            html.Div(
                [   dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P('Select Mismatch Value'),
                                    dbc.Row(
                                        html.Div(fl_buttons),
                                    )
                                ]
                            ),
                            dbc.Col(
                                [
                                    html.P('Select Individual Data', style = samp_style ),
                                    dbc.Row([
                                    dbc.Col(html.Div(dcc.Dropdown(options = super_populations, id = 'dropdown-superpopulation-sample', placeholder = 'Select a Super Population', style = samp_style))),
                                    dbc.Col(html.Div(dcc.Dropdown(options = populations, id = 'dropdown-population-sample', placeholder = 'Select a Population', style = samp_style))),
                                    dbc.Col(html.Div(dcc.Dropdown( id = 'dropdown-sample', placeholder = 'Select a Sample', style = samp_style))),
                                    ])
                                ]
                            )
                        ]
                    ),
                ]
            )
        )
        fl.append(html.Hr())
        fl.append(
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col([    #Guide part
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
                                    html.Div(
                                        [
                                        
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

        #TODO codice per l'integrazione del CFD graph. When .CFDGraph.txt will be integrated, remove the try/except
        
        cfd_path = job_directory + job_id +'.CFDGraph.txt'
        if not isfile(cfd_path): #No file found
            return fl
        
        fl.extend(
            CFDGraph.CFDGraph(cfd_path)
        )

        return fl
    # guide = all_guides[int(sel_cel[0]['row'])]['State']
        # return guide + value
    raise PreventUpdate


#Open in browser the result directory
@app.callback(
    Output('div-open-result-directory', 'children'),
    [Input('button-open-result-directory', 'n_clicks')],
    [State('url', 'search'),
    State('div-open-result-directory', 'children')]
)
def openResultDirectory(n, search, guide):
    '''
    Opens a new tab where the final list of off-targets is shown (NOT available when ONLINE mode is selected)

    ***Args***

    + [**n**] **button-open-result-directory** (*n_cliks*): number of times the button was pressed
    + [**search**] **url** (*search*): string containing the job ID, eg '?job=QV99PN6XDL'
    + [**guide**] **div-open-result-directory** (*children*): string of the currently selected guide

    ***Returns***

    + Opens a new tab showing the off-target list of jobID.targets.GUIDE.txt final file
    '''
    if n is None or ONLINE:
        raise PreventUpdate
    job_id = search.split('=')[-1]  #TODO decidere se aprire tutta la cartella, solo il file, e nel secondo caso creare copia submit job che non rimuova .targets.GUIDE.txt
    wb.open_new_tab(current_working_directory + 'Results/' + job_id + '/' + job_id + '.targets.' + guide + '.txt')
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
    '''
    Loads the images on the Graphical Report based on the selected mismatch value and/or sample, population, superpopulation value.

    ***Args***

    + [**n_**] **btn_** (*n_clicks_timestam*): string of the timestamp of the last time the button was pressed.
    + [**superpopulation**] **dropdown-superpopulation-sample** (*value*): string of the selected superpopulation
    + [**population**] **dropdown-population-sample** (*value*): string of the selected population
    + [**sample**] **dropdown-sample** (*value*): string of the selected sample
    + [**sel_cel**] **general-profile-table** (*selected_cells*): list contaning the selected row of the main guide table
    + [**search**] **url** (*search*): string containing the job ID, eg '?job=QV99PN6XDL'
    + [**all_guides**] **general-profile-table** (*data*): list of all the rows that are currenty displayed in the main guide table

    ***Returns***

    + **div-guide-image** (*children*): returns barplot and radarchart of the selected guide
    + **div-sample-image** (*children*): returns radarchart specific for sample/pop/superpop of the selected guide

    ***Details***

    + The function sort all the timestamps of the buttons (can be up to 10 buttons, one for each mms value) and select the one that was clicked last.
    Since it is not possible in the current Dash version to create callbacks of components that are not available in the app.layout, but the buttons
    are created dynamically (we do not know how many mms the user selects), we create 10 buttons and show only the ones corresponding to the number
    of selected mms, the others are hidden using `{'display':'none'}`. In this way we can create this callback even when we do not know how may mms
    the user will set.
    + If the image for a specific sample/pop/superpop is not available, the function calls `crispritz.py generate-report` in order to create the image 
    + The corresponding image is then loaded from the `assets/Img/jobID` directory, in order to be also available to be opened in a new tab (by
    clicking on it)
    '''

    if sel_cel is None :
        raise PreventUpdate
    job_id = search.split('=')[-1]
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    guide = all_guides[int(sel_cel[0]['row'])]['Guide']
    
    guide_images = []
    sample_images = []
    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        gecko_comp = (next(s for s in all_params.split('\n') if 'Gecko' in s)).split('\t')[-1]

    gecko_string = ''
    if gecko_comp == 'True':
        gecko_string = '-gecko'
    
    #Initialize to 0 Buttons not pressed
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
    
    #Check last pressed button
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
    try:            #NOTE if the image is not available, show nothing
        barplot_src = 'data:image/png;base64,{}'.format(base64.b64encode(open(current_working_directory + 'Results/' + job_id + '/' + barplot_img, 'rb').read()).decode())
    except:
        barplot_src = ''
    try:
        barplot_href = 'assets/Img/' + job_id + '/' + barplot_img
    except:
        barplot_href = ''

    try:
        radar_src = 'data:image/png;base64,{}'.format(base64.b64encode(open(current_working_directory + 'Results/' + job_id + '/' + radar_img, 'rb').read()).decode())
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
    
    #If the user selects a sample/pop/superpop not already processed, call crispritz generate-report and create the image
    for c in class_images:
        if c[0]:
            try:
                first_img_source = 'data:image/png;base64,{}'.format(base64.b64encode(open(job_directory + 'summary_single_guide_' + c[0] +'_' + guide + '_' + str(mm_show) + 'mm.png', 'rb').read()).decode())
            except:
                #create image from annotation file of samples
                subprocess.call(['cd '+job_directory +';'+
                ' crispritz.py generate-report ' + guide + ' -mm ' + str(mm_show) + ' -annotation ' + job_id + '.sample_annotation.' + guide +
                '.' + c[1].lower() + '.txt '+ gecko_string +' -ws -sample ' + c[0]], shell = True)
                
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


def generate_table(dataframe, id_table, genome_type, guide='', job_id='', max_rows=2600):
    '''
    Generates an html.Table for the Summary by Guide section.

    ***Args***

    + **dataframe**: dataframe containing the data to display
    + **id_table**: string that identifies the ID of the new generated html.Table
    + **genome_type**: string containing the type of the search ('ref', 'var' or 'both')
    + **guide**: string of the selected guide
    + **job_id**: string of the current jobID
    + **max_rows**: int of the max number of rows of the table

    ***Returns***

    + html.Table() containing data for the Summary by Guide section
    '''
    if genome_type == 'both':
        header = [html.Tr([
            html.Th('Bulge Type', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
            html.Th('Mismatches', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
            html.Th('Bulge Size', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
            html.Th('Targets found in Genome', colSpan = str(3), style = {'vertical-align':'middle', 'text-align':'center'}),
            html.Th('PAM Creation', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
            html.Th('', rowSpan = '2'),
            ])
        ]
    # 'Bulge Type' 'Mismatches' 'Bulge Size' 'Targets in Reference' 'Targets in Enriched' 'Combined' 'PAM Creation' ''
    
        header.append(html.Tr([html.Th(x, style = {'vertical-align':'middle', 'text-align':'center'}) for x in ['Reference', 'Enriched','Combined']]))
    else:
        header = [html.Tr([html.Th(col, style = {'vertical-align':'middle', 'text-align':'center'}) for col in dataframe.columns])]
    return html.Table(
        # Header
        # [html.Tr([html.Th(col) if col != 'Targets in Enriched' else html.Th(html.Abbr(col, title = 'Counting of targets that are generated by the insertion of a IUPAC nucleotide of a sample', 
        # style = {'text-decoration':'underline'})) for col in dataframe.columns])] +
        # [html.Tr([html.Th(col, rowSpan = 2) if 'Targets' not in col or 'Combined' not in col else html.Th('Targets') for col in dataframe.columns])] +
        header  + 
        # Body
        [html.Tr([
            html.Td(html.A(dataframe.iloc[i][col],  href = 'result?job=' + job_id + '#' + guide +'new' + dataframe.iloc[i]['Bulge Type'] + str(dataframe.iloc[i]['Bulge Size']) + str(dataframe.iloc[i]['Mismatches']) , target = '_blank' ), style = {'vertical-align':'middle', 'text-align':'center'}) if col == '' else  html.Td(dataframe.iloc[i][col],style = {'vertical-align':'middle', 'text-align':'center'}) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))],
        style = {'display':'inline-block'},
        id = id_table
    )

def generate_table_samples(dataframe, id_table, page ,guide='', job_id='', max_rows=10):
    '''
    Generates an html.Table for the Summary by Sample section.

    ***Args***

    + **dataframe**: dataframe containing the data to display
    + **id_table**: string that identifies the ID of the new generated html.Table
    + **page**: int containing the current page of the table
    + **guide**: string of the selected guide
    + **job_id**: string of the current jobID
    + **max_rows**: int of the max number of rows of the table

    ***Returns***

    + html.Table() containing data for the Summary by Sample section
    '''
    rows_remaining = len(dataframe) - (page - 1) * max_rows
    return html.Table(
        # Header
        # [html.Tr([html.Th(col) if col != 'Targets in Enriched'  else html.Th(html.Abbr(col, title = 'Counting of targets that are generated by the insertion of a IUPAC nucleotide of a sample',
        # style = {'text-decoration':'underline'})) for col in dataframe.columns]) ] +  
        [html.Tr([html.Th(col) for col in dataframe.columns]) ] +
        # Body
        [html.Tr([
            html.Td(html.A(dataframe.iloc[i + (page - 1)*max_rows][col],  href = 'result?job=' + job_id + '#' + guide +'-Sample-' + dataframe.iloc[i  + (page - 1)*max_rows]['Sample'] , target = '_blank' )) if col == '' else  html.Td(dataframe.iloc[i + (page - 1)*max_rows][col]) for col in dataframe.columns
        ]) for i in range(min(rows_remaining, max_rows))],
        style = {'display':'inline-block'},
        id = id_table
    )

def generate_table_position(dataframe, id_table, page, mms, bulges, guide = '', job_id = '', max_rows = 10): #NOTE v2 della tabella posizioni       #TODO modifica layout righe per allinearle
    '''
    Generates an html.Table for the Summary by Position section.

    ***Args***

    + **dataframe**: dataframe containing the data to display
    + **id_table**: string that identifies the ID of the new generated html.Table
    + **page**: int containing the current page of the table
    + **mms**: int value of the max allowed mismatched
    + **bulges**: int value of the max allowed bulges
    + **guide**: string of the selected guide
    + **job_id**: string of the current jobID
    + **max_rows**: int of the max number of rows of the table

    ***Returns***

    + html.Table() containing data for the Summary by Position section
    '''
    rows_remaining = len(dataframe) - (page - 1) * max_rows
    header = [html.Tr([
        html.Th('Chromosome', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Position', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Best Target', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Min Mismatch', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Min Bulge', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Bulge', rowSpan = '2', style = {'vertical-align':'middle', 'text-align':'center'}),
        html.Th('Targets in Cluster by Mismatch Value', colSpan = str(mms +1), style = {'vertical-align':'middle', 'text-align':'center'}),
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
    [Input('dropdown-superpopulation-sample', 'value')],
    [State('url', 'search')]
)
def updatePopulationDrop(superpop, search):
    '''
    Update the Dropdown containing the Population list based on the selected Superpopulation.

    ***Args***

    + [**superpop**] **dropdown-superpopulation-sample** (*value*): string of the selected Superpopulation
    + [**search**] **url** (*search*): string containing the job ID, eg '?job=QV99PN6XDL'

    ***Returns***

    + **dropdown-population-sample** (*options*): list of dictionaries for the option element of the Population dropdown
    + **dropdown-population-sample** (*value*): currently selected value (reinitialized to be empty)
    '''
    if superpop is None or superpop == '':
        raise PreventUpdate
    job_id = search.split('=')[-1]
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    population_1000gp = associateSample.loadSampleAssociation(job_directory + 'sampleID.txt')[2]
    return [{'label':i, 'value':i} for i in population_1000gp[superpop]], None 

#Callback to update the sample based on population selected
@app.callback(
    [Output('dropdown-sample','options'),
    Output('dropdown-sample','value')],
    [Input('dropdown-population-sample', 'value')],
    [State('url', 'search')]
)
def updateSampleDrop(pop, search):
    '''
    Update the Dropdown containing the Sample list based on the selected Population.

    ***Args***

    + [**pop**] **dropdown-population-sample** (*value*): string of the selected Population
    + [**search**] **url** (*search*): string containing the job ID, eg '?job=QV99PN6XDL'

    ***Returns***

    + **dropdown-sample** (*options*): list of dictionaries for the option element of the Sample dropdown
    + **dropdown-sample** (*value*): currently selected value (reinitialized to be empty)
    '''
    if pop is None or pop == '':
        return [], None
    job_id = search.split('=')[-1]
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    dict_pop = associateSample.loadSampleAssociation(job_directory + 'sampleID.txt')[3]
    return [{'label': sam, 'value' : sam} for sam in dict_pop[pop]], None 

#Callback to update the hidden div filter
@app.callback(
    Output('div-sample-filter-query', 'children'),
    [Input('button-filter-population-sample', 'n_clicks')],
    [State('dropdown-superpopulation-sample', 'value'),
    State('dropdown-population-sample', 'value'),
    State('input-sample', 'value')]
)
def updateSampleFilter(n, superpopulation, population, sample):
    '''
    Update the filter (superpop,pop,sample) for the filtering of the Summary by Sample table

    ***Args***

    + [**n**] **button-filter-population-sample** (*n_clicks*): int for the number of times the button was clicked
    + [**superpopulation**] **dropdown-superpopulation-sample** (*value*): string containing the selected Superpopulation
    + [**population**] **dropdown-population-sample** (*value*): string containing the selected Population
    + [**sample**] **input-sample** (*value*): string containing the Sample, given in input by the user

    ***Returns***

    + **div-simple-filter-query** (**children**): string in the format of 'superpop,pop,sample', or 'None' if a parameter was not provided (eg
    'EU,TSI,None')
    '''
    if n is None:
        raise PreventUpdate
    return str(superpopulation) + ',' + str(population) + ',' + str(sample).replace(' ','').upper()

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
    '''
    Filtering/changing page of the table in the Summary by Sample tab.

    ***Args***
    + [**nPrev**] **prev-page-sample** (*n_clicks_timestamp*): int timestamp of last click on Previous Page button
    + [**nNext**] **next-page-sample** (*n_clicks_timestamp*): int timestamp of last click on Next Page button
    + [**filter_q**] **div-sample-filter-query** (*children*): string of the filter query
    + [**n**] **button-filter-population-sample** (*n_clicks_timestamp*): int timestamp of the Apply Filter button
    + [**search**] **url** (*search*): string containing the job ID, eg '?job=QV99PN6XDL'
    + [**sel_cel**] **general-profile-table** (*selected_cells*): list contaning the selected row of the main guide table
    + [**all_guides**] **general-profile-table** (*data*): list of all the rows that are currenty displayed in the main guide table
    + [**current_page**] **div-current-page-table-samples** (*children*): string containing the current page of the table (eg '1/15')

    ***Returns***

    + **div-table-samples** (*children*): html.Table with filtering applied and/or next/previous page of data
    + **div-current-page-table-samples** (*children*): string of the currently displayed page
    '''
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
    samp = filter_q.split(',')[2]
    if sup_pop == 'None':
        sup_pop = None
    if pop == 'None':
        pop = None
    if samp == 'None' or samp == 'NONE':
        samp = None
    current_page = current_page.split('/')[0]
    current_page = int(current_page)
    btn_sample_section = []
    btn_sample_section.append(n)
    btn_sample_section.append(nPrev)
    btn_sample_section.append(nNext)
    job_id = search.split('=')[-1]
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    population_1000gp = associateSample.loadSampleAssociation(job_directory + 'sampleID.txt')[2]
    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
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
        col_names_sample = ['Sample', 'Gender', 'Population', 'Super Population',  'Targets in Reference', 'Targets in Enriched', 'Targets in Population', 'Targets in Super Population', 'PAM Creation', 'Class']
    else:
        col_names_sample = ['Sample', 'Gender', 'Population', 'Super Population',  'Targets in Reference', 'Targets in Enriched', 'Targets in Population', 'Targets in Super Population', 'PAM Creation', 'Class']       
    if max(btn_sample_section) == n:              #Last button pressed is filtering, return the first page of the filtered table
        if genome_type == 'both':
            df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
            df = df.sort_values('Targets in Enriched', ascending = False)
            df.drop(['Targets in Reference'], axis = 1, inplace = True)
        else:
            df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
            df = df.sort_values('Targets in Reference', ascending = False)
            df.drop(['Targets in Reference'], axis = 1, inplace = True)
            df.drop(['Class'], axis = 1, inplace = True) 
        more_info_col = []
        for i in range(df.shape[0]):
            more_info_col.append('Show Targets')
        df[''] = more_info_col
        if (sup_pop is None or sup_pop == '') and (pop is None or pop == '') and (samp is None or samp == ''):   #No filter value selected
            max_page = len(df.index)
            max_page = math.floor(max_page / 10) + 1
            return generate_table_samples(df, 'table-samples', 1, guide, job_id ), '1/' + str(max_page)
        if samp is None or samp == '':
            if pop is None or pop == '':
                df.drop(df[(~(df['Population'].isin(population_1000gp[sup_pop])))].index , inplace = True)
            else:
                df.drop(df[(df['Population'] != pop)].index , inplace = True)
        else:
            df.drop(df[(df['Sample'] != samp)].index , inplace = True)
        max_page = len(df.index)
        max_page = math.floor(max_page / 10) + 1
        return generate_table_samples(df, 'table-samples', 1, guide, job_id ), '1/' + str(max_page)
    else:
        if max(btn_sample_section) == nNext:
            current_page = current_page + 1
            if genome_type == 'both':
                df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
                df = df.sort_values('Targets in Enriched', ascending = False)
                df.drop(['Targets in Reference'], axis = 1, inplace = True)
            else:
                df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
                df = df.sort_values('Targets in Reference', ascending = False)
                df.drop(['Targets in Reference'], axis = 1, inplace = True)
                df.drop(['Class'], axis = 1, inplace = True) 
            more_info_col = []
            for i in range(df.shape[0]):
                more_info_col.append('Show Targets')
            df[''] = more_info_col
            #Active filter
            if pop or sup_pop or samp:
                if samp is None or samp == '':
                    if pop is None or pop == '':
                        df.drop(df[(~(df['Population'].isin(population_1000gp[sup_pop])))].index , inplace = True)
                    else:
                        df.drop(df[(df['Population'] != pop)].index , inplace = True)
                else:
                    df.drop(df[(df['Sample'] != samp)].index , inplace = True)

            if ((current_page - 1) * 10) > len(df): 
                current_page = current_page -1
                if current_page < 1:
                    current_page = 1
            max_page = len(df.index)
            max_page = math.floor(max_page / 10) + 1
            return generate_table_samples(df, 'table-samples', current_page, guide, job_id ), str(current_page) + '/' + str(max_page)
        
        else:   #Go to previous page
            current_page = current_page - 1
            if current_page < 1:
                current_page = 1
            if genome_type == 'both':
                df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
                df = df.sort_values('Targets in Enriched', ascending = False)
                df.drop(['Targets in Reference'], axis = 1, inplace = True)
            else:
                df = pd.read_csv(job_directory + job_id + '.summary_by_samples.' + guide + '.txt', sep = '\t', names = col_names_sample, skiprows = 1)
                df = df.sort_values('Targets in Reference', ascending = False)
                df.drop(['Targets in Reference'], axis = 1, inplace = True)
                df.drop(['Class'], axis = 1, inplace = True) 
            more_info_col = []
            for i in range(df.shape[0]):
                more_info_col.append('Show Targets')
            df[''] = more_info_col
            if pop or sup_pop or samp:
                if samp is None or samp == '':
                    if pop is None or pop == '':
                        df.drop(df[(~(df['Population'].isin(population_1000gp[sup_pop])))].index , inplace = True)
                    else:
                        df.drop(df[(df['Population'] != pop)].index , inplace = True)
                else:
                    df.drop(df[(df['Sample'] != samp)].index , inplace = True)
            max_page = len(df.index)
            max_page = math.floor(max_page / 10) + 1
            return generate_table_samples(df, 'table-samples', current_page, guide, job_id ), str(current_page) + '/' + str(max_page)
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
    if pos_start == '':
        pos_start = 'None'
    if pos_end == '':
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
    
    current_page = current_page.split('/')[0]
    current_page = int(current_page)
    mms = int(mms_bulge.split('-')[0])
    max_bulges = int(mms_bulge.split('-')[1])
    btn_position_section = []
    btn_position_section.append(n)
    btn_position_section.append(nPrev)
    btn_position_section.append(nNext)
    job_id = search.split('=')[-1]
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    guide = all_guides[int(sel_cel[0]['row'])]['Guide']
    if max(btn_position_section) == n:              #Last button pressed is filtering, return the first page of the filtered table
        if pos_begin is None or pos_begin == '':
            pos_begin = 0
        if pos_end == '':
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
        if chr is None or chr == '':
            max_page = len(df.index)
            max_page = math.floor(max_page / 10) + 1
            return generate_table_position(df, 'table-position', 1, mms, max_bulges,guide, job_id ), '1/' + str(max_page)
        if pos_end is None:
            df.drop(df[(df['Chromosome'] != chr) | ((df['Chromosome'] == chr) & (df['Position'] < int(pos_begin)) )].index , inplace = True)
        else:
            df.drop(df[(df['Chromosome'] != chr) | ((df['Chromosome'] == chr) & (df['Position'] < int(pos_begin)) | (df['Position'] > int(pos_end)))].index , inplace = True)
        max_page = len(df.index)
        max_page = math.floor(max_page / 10) + 1
        return generate_table_position(df, 'table-position', 1, mms, max_bulges,guide, job_id ), '1/'+ str(max_page)
    else:
        
        if max(btn_position_section) == nNext:
            current_page = current_page + 1
            if chr:
                if pos_begin is None or pos_begin == '':
                    pos_begin = 0
                if pos_end == '':
                    pos_end = None
                if pos_end:
                    if int(pos_end) < int(pos_begin):
                        pos_end = None
                df = pd.read_csv(job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t')  
            else:
                df = pd.read_csv(job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t')#, nrows = current_page * 10)   
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
            max_page = len(df.index)
            max_page = math.floor(max_page / 10) + 1
            return generate_table_position(df, 'table-position', current_page, mms, max_bulges,guide, job_id ), str(current_page) + '/' + str(max_page)
        else:                       #Go to previous page
            current_page = current_page - 1
            if current_page < 1:
                current_page = 1

            if chr:
                if pos_begin is None or pos_begin == '':
                    pos_begin = 0
                if pos_end == '':
                    pos_end = None
                if pos_end:
                    if int(pos_end) < int(pos_begin):
                        pos_end = None
                df = pd.read_csv(job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t')  
            else:
                df = pd.read_csv(job_directory + job_id + '.summary_by_position.' + guide +'.txt', sep = '\t')#, nrows = current_page * 10)   
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
            
            max_page = len(df.index)
            max_page = math.floor(max_page / 10) + 1
            return generate_table_position(df, 'table-position', current_page, mms, max_bulges,guide, job_id ), str(current_page) + '/' + str(max_page)


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
    '''
    value = job_id
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    warning_message = []
    if (not isdir(job_directory)):
        return html.Div(dbc.Alert("The selected result does not exist", color = "danger"))

    #Load mismatches
    with open(current_working_directory + 'Results/' + value + '/Params.txt') as p:
        all_params = p.read()
        mms = (next(s for s in all_params.split('\n') if 'Mismatches' in s)).split('\t')[-1]
        bulge_dna = (next(s for s in all_params.split('\n') if 'DNA' in s)).split('\t')[-1]
        bulge_rna = (next(s for s in all_params.split('\n') if 'RNA' in s)).split('\t')[-1]
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        max_bulges = (next(s for s in all_params.split('\n') if 'Max_bulges' in s)).split('\t')[-1]

    genome_name = genome_type_f
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
        genome_name = genome_name.split('_')[0] + ' Variants'
    else:
        genome_name = genome_name.split('_')[0] + ' Reference'
    if 'True' in ref_comp:
        genome_type = 'both'
    mms = int(mms[0])    
    
    #load acfd for each guide 
    with open(current_working_directory + 'Results/' + value + '/acfd.txt') as a:
        all_scores = a.read().strip().split('\n')
    
    list_error_guides = []
    if os.path.exists(current_working_directory + 'Results/' + value + '/guides_error.txt'):
        with open(current_working_directory + 'Results/' + value + '/guides_error.txt') as error_g:
            for e_g in error_g:
                list_error_guides.append(e_g.strip())

    col_targetfor = '('
    for i in range(1, mms + int(max_bulges)):
        col_targetfor = col_targetfor + str(i) + '-'
    col_targetfor = col_targetfor + str(mms + int(max_bulges))
    col_targetfor = col_targetfor + ' Mismatches + Bulges)'
    
    columns_profile_table = [ 
        {'name':['', 'Guide'], 'id':'Guide', 'type':'text'},
        {'name':['', 'CFD'], 'id':'CFD', 'type':'text'},
        {'name':['', 'Doench 2016'], 'id':'Doench 2016', 'type':'text'},    #Doench, only for REF or VAR
        {'name':['Doench 2016', 'Reference'], 'id':'Reference', 'type':'text'},        #REF Doench, only for Both
        {'name':['Doench 2016', 'Enriched'], 'id':'Enriched', 'type':'text'},          #VAR Doench, only for Both
        {'name':['', 'On-Targets Reference'], 'id':'On-Targets Reference', 'type':'text'},
        {'name':['', 'On-Targets Enriched'], 'id':'On-Targets Enriched', 'type':'text'},
        {'name':['', 'Samples in Class 0 - 0+ - 1 - 1+'], 'id':'Samples in Class 0 - 0+ - 1 - 1+', 'type':'text'},
        {'name':['', 'Genome'], 'id':'Genome', 'type':'text'},
        {'name':['Off-targets for Mismatch (MM) + Bulge (B) Value', 'Total'], 'id':'Total', 'type':'text'}
        ]    #Column of headers . Remove the entries accordingly when checking type of genome
    
    for i in range (1, mms + int(max_bulges) + 1):
        columns_profile_table.append({'name':['Off-targets for Mismatch (MM) + Bulge (B) Value', str(i) + ' MM + B'], 'id': str(i) + ' MM + B', 'type':'text'})
    remove_indices = set()
    
    if 'NO SCORES' in all_scores:
        # remove_indices.update([1,2,3,4])    #Remove CFD and Doench header
        remove_indices.update('CFD', 'Doench 2016', 'Reference', 'Enriched')
    
    if genome_type == 'ref':
        # remove_indices.update([3,4,6,7])
        remove_indices.update(['Reference', 'Enriched', 'On-Targets Enriched', 'Samples in Class 0 - 0+ - 1 - 1+' ])
    elif genome_type == 'both':
        # remove_indices.update([6])
        remove_indices.update(['Doench 2016','On-Targets Enriched'])
    else:
        # remove_indices.update([3,4,5,7])
        remove_indices.update(['Reference', 'Enriched', 'On-Targets Reference', 'Samples in Class 0 - 0+ - 1 - 1+'])
    
    #Remove headers not used in selected search result
    columns_profile_table = [i for j, i in enumerate(columns_profile_table) if columns_profile_table[j]['id'] not in remove_indices]      
    
    final_list = []    
    if list_error_guides:
        final_list.append(
            dbc.Alert(
                [
                    'Warning: Some guides have too many targets! ',
                    html.A("Click here", href= URL + "/data/" + job_id + '/guides_error.txt', className="alert-link"),
                    ' to view them'
                ], color='warning')
        )
    final_list.append(
        html.H3('Result Summary - ' + genome_name + ' - Mismatches ' + str(mms) + ' - DNA ' + bulge_dna + ' - RNA ' + bulge_rna)
    )
   
    add_to_description = html.P(
        'General summary for the given guides. For each guide, the number of Off-Targets found for each Mismatch + Bulge value is shown.'
    )
    if genome_type == 'both':
        add_to_description = html.P(
            [
                'General summary for the given guides. For each guide, the number of ',  
                html.Span(
                    "Samples for each Class is provided",
                    id="tooltip-sample-class",
                    style={"textDecoration": "underline", "cursor": "pointer"}
                ),
                ', along with the number of Off-Targets found for each Mismatch + Bulge value, for both Reference and Enriched Genomes.',
                dbc.Tooltip(
                    [
                        html.Div([html.P([html.B('Class 0:'), ' Samples that does not have any On-Targets']),
                        html.P([html.B('Class 0+:'), ' Samples that have a subset of the Reference Genome On-Targets']),
                        html.P([html.B('Class 1:'), ' Samples that have the same On-Targets as the Reference Genome']),
                        html.P([html.B('Class 1+:'), ' Samples that creates at least a new On-Target, that is not present in the Reference Genome'])], 
                        style = {'display':'inline-block'})
                    ],
                    target="tooltip-sample-class", style = {'font-size': '12px'}
                )
            ]
        )
    final_list.append(add_to_description)
    final_list.append(
        html.Div(
            dash_table.DataTable(
                id = 'general-profile-table',
                #page_size=PAGE_SIZE,
                columns = columns_profile_table,
                merge_duplicate_headers=True,
                #fixed_rows={ 'headers': True, 'data': 0 },
                #data = profile.to_dict('records'),
                selected_cells = [{'row':0, 'column':0}],
                css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],
                page_current= 0,
                page_size= 10,
                page_action='custom',
                #virtualization = True,
                filter_action='custom',
                filter_query='',

                sort_action='custom',
                sort_mode='multi',
                sort_by=[],
                style_table={
                    'max-height': '260px',
                    'overflowY': 'scroll',
                },
                style_data={
                    'whiteSpace': 'pre',
                    'height': 'auto',
                    'font-size':'1.30rem'
                },
                style_data_conditional = [
                    {
                        'if': {
                                'column_id' :'Genome'
                            },
                            'font-weight':'bold',
                            'textAlign': 'center'
                            
                    }
                ]
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
        #Barplot for population distributions
        final_list.append(
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(html.Button("Show/Hide Target Distribution in SuperPopulations", id="btn-collapse-populations")),
                            # dbc.Col(html.A('Download full list of targets', target = '_blank', id = 'download-full-list' ))
                        ]
                    ),
                    dbc.Collapse(
                        dbc.Card(dbc.CardBody(
                            html.Div(id = 'content-collapse-population')
                        )),
                        id="collapse-populations",
                    ),
                ]
            )
        )
        final_list.append(html.Br())
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
                
            },
            {
                'if': {
                        'column_id' :'Genome'
                    },
                    'font-weight':'bold',
                    'textAlign': 'center'
                    
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
    
    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        mms = int((next(s for s in all_params.split('\n') if 'Mismatches' in s)).split('\t')[-1])
        max_bulges = int((next(s for s in all_params.split('\n') if 'Max_bulges' in s)).split('\t')[-1])
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
    
    filtering_expressions = filter.split(' && ')
    
    #Get error guides
    list_error_guides = []
    if os.path.exists(current_working_directory + 'Results/' + job_id + '/guides_error.txt'):
        with open(current_working_directory + 'Results/' + job_id + '/guides_error.txt') as error_g:
            for e_g in error_g:
                list_error_guides.append(e_g.strip())
    
    #Get guide from guide.txt
    with open(current_working_directory + 'Results/' + job_id + '/guides.txt') as g:
        guides = g.read().strip().split('\n')
        guides.sort()

    #load acfd for each guide 
    with open(current_working_directory + 'Results/' + job_id + '/acfd.txt') as a:
        all_scores = a.read().strip().split('\n')
    
    #Load scores
    if 'NO SCORES' not in all_scores:
        all_scores.sort()
        acfd = [float(a.split('\t')[1]) for a in all_scores if a.split('\t')[0] not in list_error_guides]
        doench = [int(a.split('\t')[2]) for a in all_scores if a.split('\t')[0] not in list_error_guides]
        if genome_type == 'both':
            doench_enr = [int(a.split('\t')[3]) for a in all_scores if a.split('\t')[0] not in list_error_guides]
        acfd  = [int(round((100/(100 + x))*100)) for x in acfd] 

    #Get target counting from summary by guide
    column_on_target = []
    column_off_target_ref = []
    column_sample_class = []
    column_total = []
    if genome_type == 'ref' or genome_type == 'var':
        for g in guides:
            one_to_n_mms = []
            df_profile = pd.read_pickle(current_working_directory + 'Results/' + job_id + '/' + job_id + '.summary_by_guide.' + g + '.txt')
            on_t_ref = int(df_profile[(df_profile.Mismatches == 0) & (df_profile['Bulge Type'] == 'X')].iloc[0]['Targets in Reference'])
            try: #For VAR, read enriched values
                on_t_enr = int(df_profile[(df_profile.Mismatches == 0) & (df_profile['Bulge Type'] == 'X')].iloc[0]['Targets in Enriched']) 
                column_on_target.append(str(on_t_enr))
            except: #For REF, read only reference values
                column_on_target.append(str(on_t_ref))
            
            for i in range (1, mms + 1 + int(max_bulges)):         #For column Targets for 1-2 Total (Mismatches + Bulges), sum values for row with same total
                try:    #For VAR
                    one_to_n_mms.append(sum(df_profile[((df_profile['Mismatches'] + df_profile['Bulge Size']) == i)]['Targets in Enriched'].to_list()))
                except: #For REF
                    one_to_n_mms.append(sum(df_profile[((df_profile['Mismatches'] + df_profile['Bulge Size']) == i)]['Targets in Reference'].to_list()))
            column_total.append(int(sum(one_to_n_mms)))
            column_off_target_ref.append([int(x) for x in one_to_n_mms])  #[[1, 5, 10], [3, 7, 20]]       each internal list is the number of off-target for a guide, divided by value (from 1 to mm+max_bulge)
    else:
        #NOTE  USO IL CONTEGGIO PRESO DA jobid.general_target_count.txt
        with open(current_working_directory + 'Results/' + job_id + '/' + job_id + '.general_target_count.txt') as general_count:
            header_general = next(general_count) #skip header
            general_count_content = general_count.read().strip().split('\n')
            general_count_content.sort(key = lambda x : x[0])
        guides = []
        column_on_target_old = dict()      #will contain GUIDE -> 3(1 - 2), then later, in column_on_target, only the 1 will be kept
        for tmp in general_count_content:
            tmp = tmp.split('\t')   #[GUIDE, total_onT (onT_ref - onTvar), total_offT_ref ( - - - ), total_offT_var ( - - -)]
            guides.append(tmp[0])
            column_on_target_old[tmp[0]] = tmp[1]      #tmp[1] =  3(1 - 2)
            a = tmp[2].replace('(','').replace(')','').replace('-','').replace('  ',' ').strip().split(' ') # ottengo in a[0] il total, da a[1:] il numero di targets per 1 2 3 ... Total del REF
            b = tmp[3].replace('(','').replace(')','').replace('-','').replace('  ',' ').strip().split(' ') # ottengo in a[0] il total, da a[1:] il numero di targets per 1 2 3 ... Total del VAR
            column_total.append(a[0] + '\n' + b[0] + '\n' + str(int(a[0]) + int(b[0])))
            column_off_target_ref.append(
                [a[x] + '\n' + b[x] + '\n' + str(int(a[x]) + int(b[x])) for x in range(len(a))][1:]     #[1:] to skip total value
            )   # in the end i obtain [ ['1\n3\n5', '12\n21\n54'] , ['0\n3\n4', '12\n25\n34']], one list per guide, inside each list string for each total value
            
        with open(current_working_directory + 'Results/' + job_id + '/' + job_id + '.SampleClasses.txt') as samp_classes:
            header_classes = next(samp_classes).strip().split('\t')[1:]     #List of Guides
            for line in samp_classes:
                if 'Total for Class' in line:       #Last line
                    value_classes = line.strip().split('\t')[1:]           #List of values of classes for each guide
        #NOTE just for changing '-' to ' - '
        for pos_vc, vc in enumerate(value_classes):
            value_classes[pos_vc] = ' - '.join(vc.split('-'))
        
        dict_classes = dict(zip(header_classes, value_classes))
        column_on_target = []
        for g in guides:
            column_sample_class.append(dict_classes[g]) 
            column_on_target.append(column_on_target_old[g].split('(')[-1].split('-')[0])

    data_guides = dict()
    data_guides['Guide'] = guides
    if 'NO SCORES' not in all_scores:
        data_guides['CFD'] = acfd
        if genome_type == 'both':
            data_guides['Reference'] = doench
            data_guides['Enriched'] = doench_enr
        else:
            data_guides['Doench 2016'] = doench

    if genome_type == 'ref' or genome_type == 'both':
        data_guides['On-Targets Reference'] = column_on_target
        data_guides['Genome'] = 'REFERENCE'     #NOTE if genome_type == 'both', it will be updated
    else:
        data_guides['On-Targets Enriched'] = column_on_target
        data_guides['Genome'] = 'ENRICHED'

    if genome_type == 'both':
        data_guides['Samples in Class 0 - 0+ - 1 - 1+'] = column_sample_class
        data_guides['Genome'] = 'REFERENCE\nENRICHED\nCOMBINED'
    data_guides['Total'] = column_total
    for i in range (1, mms + int(max_bulges) + 1):  #add count target for each total value
        data_guides[str(i) + ' MM + B'] = [str(x[i-1]) for x in column_off_target_ref]      #NOTE i-1 since i starts from 1

    dff = pd.DataFrame(data_guides)
    
    if 'NO SCORES' not in all_scores:
        try:
            dff = dff.sort_values(['CFD', 'Doench 2016'], ascending = [False, False])
        except: #for BOTH
            dff = dff.sort_values(['CFD', 'Enriched'], ascending = [False, False])
    else:
        try:
            dff = dff.sort_values('On-Targets Reference', ascending = True)
        except:
            dff = dff.sort_values('On-Targets Enriched', ascending = True)

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
            ['Samples' if col['column_id'] == 'Samples Summary' else col['column_id'] for col in sort_by],
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


#Open/close barplot for population distribution
@app.callback(
    Output("collapse-populations", "is_open"),
    [Input("btn-collapse-populations", "n_clicks")],
    [State("collapse-populations", "is_open")],
)
def toggleCollapseDistributionPopulations(n, is_open):
    if n:
        return not is_open
    return is_open

#Load barplot of population distribution for selected guide
@app.callback(
    Output('content-collapse-population', 'children'),
    [Input('general-profile-table', 'selected_cells')],
    [State('general-profile-table', 'data'),
    State('url','search')]
)
def loadDistributionPopulations(sel_cel, all_guides, job_id):
    if sel_cel is None or not sel_cel or not all_guides:
        raise PreventUpdate
    guide = all_guides[int(sel_cel[0]['row'])]['Guide']
    job_id = job_id.split('=')[-1]

    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        mms = int((next(s for s in all_params.split('\n') if 'Mismatches' in s)).split('\t')[-1])
        max_bulges = int((next(s for s in all_params.split('\n') if 'Max_bulges' in s)).split('\t')[-1])

    distributions = [dbc.Row(html.P('On- and Off-Targets distributions in the Reference and Enriched Genome. For the Enriched Genome, the targets are divided into 5 SuperPopulations (EAS, EUR, AFR, AMR, SAS).', style = {'margin-left':'0.75rem'}))]

    for i in range(math.ceil((mms + max_bulges + 1) / BARPLOT_LEN)):
        all_images = []
        for mm in range (i * BARPLOT_LEN, (i + 1) * BARPLOT_LEN ):
            if mm < (mms + max_bulges + 1):
                try:
                    all_images.append(
                        dbc.Col(  
                            [   
                                html.A(
                                    html.Img(
                                        src = 'data:image/png;base64,{}'.format(base64.b64encode(open(current_working_directory + 'Results/' + job_id + '/populations_distribution_' + guide + '_' + str(mm) + 'total.png', 'rb').read()).decode()),
                                        id = 'distribution-population' + str(mm), width="100%", height="auto"
                                    ),
                                    target="_blank",
                                    href = 'assets/Img/' + job_id + '/' + 'populations_distribution_' + guide + '_' + str(mm) + 'total.png'
                                ),
                                html.Div(html.P('Distribution ' + str(mm) + ' Mismatches + Bulges ', style = {'display':'inline-block'} ),style = {'text-align':'center'})
                            ]
                        )
                    )
                except:
                    all_images.append(
                        dbc.Col(
                            [
                                html.Div(html.P('No Targets found with ' + str(mm) + ' Mismatches + Bulges' , style = {'display':'inline-block'}), style = {'text-align':'center'}),
                                # html.Div(html.P('Distribution ' + str(mm) + ' Mismatches + Bulges ', style = {'display':'inline-block'} ),style = {'text-align':'center'})
                            ],
                            align = 'center'
                        )
                    )
            else:
                all_images.append(dbc.Col(html.P('')))
        
        distributions.append(
            html.Div(
                [
                    dbc.Row(
                        all_images
                    )
                ]
            )
        )
    return distributions

@cache.memoize()
def global_store_subset(value, bulge_t, bulge_s, mms, guide):
    '''
    Caching dei file targets per una miglior performance di visualizzazione
    '''
    if value is None:
        return ''
    #Skiprows = 1 to skip header of file
    df = pd.read_csv( current_working_directory + 'Results/' + value + '/' + value + '.' + bulge_t + '.' + bulge_s + '.' + mms + '.' + guide +'.txt', sep = '\t', header = None) #, skiprows = 1)
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
    add_header = ' - Mismatches ' + str(mms)
    if bulge_t != 'X':
        add_header += ' - ' + str(bulge_t) + ' ' + str(bulge_s) 
    value = job_id
    if (not isdir(current_working_directory + 'Results/' + job_id)):
        return html.Div(dbc.Alert("The selected result does not exist", color = "danger"))
    with open(current_working_directory + 'Results/' + value + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    style_hide_reference = {'display':'none'}
    value_hide_reference = []
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
        style_hide_reference = {}
        value_hide_reference = ['hide-ref']
    final_list = []
    final_list.append(html.H3('Selected Guide: ' + guide + add_header))
    final_list.append(
        html.P(
            [
                        'List of Targets found for the selected guide. Select a row to view other possible configurations of the target, along with the corresponding samples list.', # 'Select a row to view the target IUPAC character scomposition. The rows highlighted in red indicates that the target was found only in the genome with variants.',
                        dcc.Checklist(options = [{'label': 'Hide Reference Targets', 'value': 'hide-ref'}], id='hide-reference-targets', value = value_hide_reference, style = style_hide_reference),
                        html.Div(
                            [   
                                html.P('Generating download link, Please wait...', id = 'download-link-sumbyguide'), 
                                dcc.Interval(interval = 5*1000, id = 'interval-sumbyguide')
                            ]
                        )
            ]
        )
    )
    if genome_type == 'ref':
        cols = [{"name": i, "id": i, 'type':t, 'hideable':True} for i,t in zip(COL_REF, COL_REF_TYPE)]    
        file_to_grep = '.Annotation.targets.txt'#'.top_1.txt'
    else:
        cols = [{"name": i, "id": i, 'type':t, 'hideable':True} for i,t in zip(COL_BOTH, COL_BOTH_TYPE)]
        file_to_grep = '.samples.annotation.txt'
    
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    guide_grep_result = job_directory + job_id + '.' + bulge_t + '.' + bulge_s + '.' + mms + '.' + guide + '.txt'
    put_header = 'head -1 ' + job_directory + job_id + file_to_grep + ' > ' + guide_grep_result + ' ; '
    final_list.append(
        html.Div(job_id + '.' + bulge_t + '.' + bulge_s + '.' + mms + '.' + guide,style = {'display':'none'}, id = 'div-info-sumbyguide-targets')
    )
    # print('qui guide before grep')
    # print('esiste guide?', str(os.path.exists(guide_grep_result)))
    if not os.path.exists(guide_grep_result):    #Example    job_id.X.0.4.guide.txt #NOTE HEADER NON SALVATO
        subprocess.call([put_header + 'LC_ALL=C fgrep ' + guide + ' ' + job_directory + job_id + file_to_grep + ' | LC_ALL=C fgrep ' + bulge_t + ' | awk \'$8==' + mms + ' && $9==' + bulge_s + '\'> ' + guide_grep_result], shell = True)
        subprocess.Popen(['zip ' + guide_grep_result.replace('.txt','.zip') + ' ' + guide_grep_result], shell = True)
    global_store_subset(job_id, bulge_t, bulge_s, mms,guide)
    
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
                style_data_conditional = [
                    # {
                    #     'if': {
                    #             'filter_query': '{Variant Unique} eq y',
                    #             #'filter_query': '{Direction} eq +', 
                    #             #'column_id' :'Bulge Type'
                    #         },
                    #         #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                    #         'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                    #     },
                    {
                        'if': {
                                'filter_query': '{Variant Unique} eq F',
                                #'filter_query': '{Direction} eq +', 
                                #'column_id' :'Bulge Type'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(0, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        },

                ]            
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

#Update primary table of 'Show targets' of Summary by Guide
@app.callback(
    Output('table-subset-target', 'data'),
    [Input('table-subset-target', "page_current"),
     Input('table-subset-target', "page_size"),
     Input('table-subset-target', "sort_by"),
     Input('table-subset-target', 'filter_query'),
     Input('hide-reference-targets', 'value')],
     [State('url', 'search'),
     State('url', 'hash')]
)
def update_table_subset(page_current, page_size, sort_by, filter, hide_reference, search, hash_guide):
    '''
    La funzione ritorna uno split dei risultati in base ad un filtering o a un sort da parte dell'utente. Inoltre aggiorna i risultati
    visualizzati quando il bottone next page / prev page è cliccato. (Codice preso dalla pagina dash datatable sul sorting con python)
    Inoltre carica i file targets, o scores se presente, e lo trasforma in un dataframe, cambiando il nome delle colonne per farle corrispondere
    all'id delle colonne della tabella nella pagina.
    Se non ci sono targets ritorna un avviso di errore
    '''
    job_id = search.split('=')[-1]
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
    
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
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
    if genome_type == 'ref':
        dff.rename(columns = COL_REF_RENAME, inplace = True)
    else:
        dff.rename(columns = COL_BOTH_RENAME , inplace = True)

    if 'hide-ref' in hide_reference or genome_type == 'var':
        dff.drop( df[(df['Samples'] == 'n')].index, inplace = True)
    
    try:    #For VAR and BOTH
        del dff['Variant Unique']
    except: #For REF
        pass

    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)
        if col_name == 'Samples Summary':
            col_name = 'Samples'
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
            ['Samples' if col['column_id'] == 'Samples Summary' else col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )
   
    cells_style = [
                        
                        # {
                        # 'if': {
                        #         'filter_query': '{Variant Unique} eq y',
                        #         #'filter_query': '{Direction} eq +', 
                        #         #'column_id' :'Bulge Type'
                        #     },
                        #     #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                        #     'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        # },
                        {
                            'if': {
                                    'filter_query': '{Cluster Position} eq "' + guide + '"', 
                                    #'column_id' :'{#Bulge type}',
                                    #'column_id' :'{Total}'
                                },
                                #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                                'background-color':'rgba(0, 0, 255,0.15)'#'rgb(255, 102, 102)'
                                
                        },
                        
                        # {
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
                        #             'filter_query': '{Variant Unique} eq n',           
                        #             'column_id' :'Bulge Type'
                        #         },
                        #         'border-left': '5px solid rgba(26, 26, 255, 0.9)',

                        # }
                        
                ]
    
    #Calculate sample count
    
    data_to_send=dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')
    if genome_type != 'ref':
        dict_sample_to_pop, dict_pop_to_superpop = associateSample.loadSampleAssociation(job_directory + 'sampleID.txt')[:2]
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
    return data_to_send#, cells_style + style_data_table

#Create second table for subset targets page, and show corresponding samples    -> CHANGED, now show IUPAC scomposition
@app.callback(
    [Output('div-second-table-subset-targets', 'children'),
    Output('table-subset-target', 'style_data_conditional')],
    [Input('table-subset-target', 'active_cell')],
    [State('table-subset-target', 'data'),
    State('table-subset-target', 'columns'),
    State('url', 'search'),
    State('table-subset-target', 'style_data_conditional'),
    State('table-subset-target', 'selected_cells')]
)
def loadFullSubsetTable(active_cel, data, cols, search, style_data, sel_cell):
    #NOTE tabella secondaria della scomposizione ora non serve, non cancello il codice ma uso PreventUpdate per non azionare la funzione
    if False:
        raise PreventUpdate
    if active_cel is  None:
        raise PreventUpdate
    fl = []
    job_id = search.split('=')[-1]
    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
    
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'

    if genome_type == 'ref':
        raise PreventUpdate
    #fl.append(html.Br())
    fl.append(html.Hr())
    #Table for IUPAC scomposition
    #fl.append(html.Br())
    fl.append('List of all the configurations for the selected target.')
    fl.append(html.Br())
    cols.append({"name": 'Samples', "id": 'Samples', 'type':'text', 'hideable':True})  

       
    fl.append(
        html.Div(
            dash_table.DataTable(
                id='second-table-subset-targets', 
                columns=cols, 
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
                filter_query='',
                style_table={
                    'max-height': '600px'
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'Samples'},
                        'textAlign': 'left'
                    }
                ],
                css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],
                style_data_conditional = [
                        # {
                        # 'if': {
                        #         'filter_query': '{Variant Unique} eq y',
                        #     },
                        #     #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                        #     'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        # },
                        {
                        'if': {
                                'filter_query': '{Variant Unique} eq F',
                                #'filter_query': '{Direction} eq +', 
                                #'column_id' :'Bulge Type'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(0, 0, 0,0.15)'#'rgb(255, 102, 102)'
                        }
                ]         
            )
        )
    )

    pos_cluster = data[int(sel_cell[0]['row'])]['Cluster Position']
    chrom = data[int(sel_cell[0]['row'])]['Chromosome']
    cells_style = [
                       style_data[0],
                        {
                            'if': {
                                    'filter_query': '{Cluster Position} eq "' + str(pos_cluster) + '"',
                                    ##'filter_query': '{Chromosome} eq "' + str(chrom) + '"',
                                    #'column_id' :'{#Bulge type}',
                                    #'column_id' :'{Total}'
                                },
                                #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                                'background-color':'rgba(0, 0, 255,0.15)'#'rgb(255, 102, 102)'
                                
                        }
                        
                        # {
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
                        #             'filter_query': '{Variant Unique} eq n',           
                        #             'column_id' :'Bulge Type'
                        #         },
                        #         'border-left': '5px solid rgba(26, 26, 255, 0.9)',

                        # }
                        
                ]
    return  fl, cells_style

#Filter etc for second tabe
@app.callback(
    [Output('second-table-subset-targets', 'data'),                         #Table showing iupac scomposition
    Output('second-table-subset-targets', 'style_data_conditional')],
    [Input('second-table-subset-targets', "page_current"),
     Input('second-table-subset-targets', "page_size"),
     Input('second-table-subset-targets', "sort_by"),
     Input('second-table-subset-targets', 'filter_query')],
     [State('url', 'search'),
     State('url', 'hash'),
     State('table-subset-target', 'active_cell'),
    State('table-subset-target', 'data')]
)
def update_table_subsetSecondTable(page_current, page_size, sort_by, filter, search, hash_guide, active_cel, data):
    #NOTE tabella secondaria della scomposizione ora non serve, non cancello il codice ma uso PreventUpdate per non azionare la funzione
    if False:
        raise PreventUpdate
    if active_cel is None:
        raise PreventUpdate
    job_id = search.split('=')[-1]
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]

    guide = hash_guide[1:hash_guide.find('new')]
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
    if search is None:
        raise PreventUpdate

    if genome_type == 'ref':
        raise PreventUpdate    

    filtering_expressions = filter.split(' && ')
    bulge_t =  data[active_cel['row']]['Bulge Type']
    bulge_s = str(data[active_cel['row']]['Bulge Size'])
    mms = str(data[active_cel['row']]['Mismatches'])
    chrom = str(data[active_cel['row']]['Chromosome'])
    pos = str(data[active_cel['row']]['Cluster Position'])
    # annotation_type = str(data[active_cel['row']]['Annotation Type'])

    scomposition_file = job_directory + job_id + '.' + bulge_t + '.' + bulge_s + '.' + mms + '.' + guide + '.' + chrom + '.' + pos + '.scomposition.txt'
    file_to_grep = '.samples.annotation.txt'

    if not os.path.exists(scomposition_file):    #Example    job_id.X.0.4.GUIDE.chrom.position.scomposition.txt
        # subprocess.call(['LC_ALL=C fgrep ' + guide + ' ' + current_working_directory + 'Results/'+ job_id + '/' + job_id + file_to_grep + ' |  awk \'$6==' + pos + ' && $4==\"' + chrom + '\" && $8==' + mms + ' && $9==' + bulge_s +'\' > ' + scomposition_file], shell = True)
        subprocess.call(['LC_ALL=C fgrep ' + guide + ' ' + current_working_directory + 'Results/'+ job_id + '/' + job_id + file_to_grep + ' |  awk \'$6==' + pos + ' && $4==\"' + chrom + '\" && $9==' + bulge_s + ' && $13!=\"n\"' +'\' > ' + scomposition_file], shell = True)
    
    if os.path.getsize(scomposition_file) > 0:          #Check if result grep has at least 1 result
        df = pd.read_csv(scomposition_file, header = None, sep = '\t')
        # df['Annotation Type'] = annotation_type
    else:
        raise PreventUpdate
     
    df.rename(columns = COL_BOTH_RENAME , inplace = True)
    df.drop(df[(~( df['Cluster Position'] == int(data[active_cel['row']]['Cluster Position']))) | (~( df['Chromosome'] == data[active_cel['row']]['Chromosome']))].index, inplace = True)
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
            ['Samples' if col['column_id'] == 'Samples Summary' else col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )
   

    cells_style = [
                        # {
                        # 'if': {
                        #         'filter_query': '{Variant Unique} eq y',
                        #         #'filter_query': '{Direction} eq +', 
                        #         #'column_id' :'Bulge Type'
                        #     },
                        #     #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                        #     'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        # },
                        {
                        'if': {
                                'filter_query': '{Variant Unique} eq F',
                                #'filter_query': '{Direction} eq +', 
                                #'column_id' :'Bulge Type'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(0, 0, 0,0.15)'#'rgb(255, 102, 102)'
                        }
                        # {
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
                        #             'filter_query': '{Variant Unique} eq n',           
                        #             'column_id' :'Bulge Type'
                        #         },
                        #         'border-left': '5px solid rgba(26, 26, 255, 0.9)',

                        # }
                        
                ]
    
    #Calculate sample count
    
    data_to_send=dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')
    if genome_type != 'ref':
        dict_sample_to_pop, dict_pop_to_superpop = associateSample.loadSampleAssociation(job_directory + 'sampleID.txt')[:2]
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

@cache.memoize()
def global_store_general(path_file_to_load):
    '''
    Caching dei file targets per una miglior performance di visualizzazione
    '''
    if 'scomposition' in path_file_to_load:
        rows_to_skip = 0
    else:
        rows_to_skip = 0        #Skip header
    if path_file_to_load is None:
        return ''
    if os.path.getsize(path_file_to_load) > 0: 
        df = pd.read_csv( path_file_to_load , sep = '\t', header = None, skiprows = rows_to_skip)
    else:
        df = None
    #df.rename(columns = {"#Bulge type":'Bulge Type', "#Bulge_type":'Bulge Type', 'Bulge_Size':'Bulge Size'}, inplace = True)
    return df

#Return the targets found for the selected sample
def samplePage(job_id, hash):
    guide = hash[:hash.find('-Sample-')]
    sample = hash[hash.rfind('-') + 1:]
    if (not isdir(current_working_directory + 'Results/' + job_id)):
        return html.Div(dbc.Alert("The selected result does not exist", color = "danger"))

    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
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
    final_list.append(
        html.P(
            [
                'List of Targets found for the selected sample.', #'The rows highlighted in red indicates that the target was found only in the genome with variants.',
                html.Div(
                    [   
                        html.P('Generating download link, Please wait...', id = 'download-link-sumbysample'), 
                        dcc.Interval(interval = 5*1000, id = 'interval-sumbysample')
                    ]

                )
            ]
        )
    )
        
    file_to_grep = '.samples.annotation.txt'
    sample_grep_result = current_working_directory + 'Results/'+ job_id + '/' + job_id + '.' + sample + '.' + guide + '.txt'
    put_header = 'head -1 ' + current_working_directory + 'Results/' + job_id + '/' + job_id + file_to_grep + ' > ' + sample_grep_result + ' ; '
    final_list.append(
        html.Div(job_id + '.' + sample + '.' + guide,style = {'display':'none'}, id = 'div-info-sumbysample-targets')
    )
    # print('qui sample before grep')
    # print('esiste sample?', str(os.path.exists(sample_grep_result)))

    if not os.path.exists(sample_grep_result):    #Example    job_id.HG001.guide.txt #NOTE HEADER NON SALVATO
        subprocess.call([put_header + 'LC_ALL=C fgrep ' + guide + ' ' + current_working_directory + 'Results/'+ job_id + '/' + job_id + file_to_grep + ' | LC_ALL=C fgrep ' + sample + ' > ' + sample_grep_result], shell = True)
        subprocess.Popen(['zip ' + sample_grep_result.replace('.txt','.zip') + ' ' + sample_grep_result],shell = True)
    
    cols = [{"name": i, "id": i, 'type':t, 'hideable':True} for i,t in zip(COL_BOTH, COL_BOTH_TYPE)]
    
    final_list.append(          
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
                    # {
                    #     'if': {
                    #             'filter_query': '{Variant Unique} eq y', 
                    #             #'column_id' :'{#Bulge type}',
                    #             #'column_id' :'{Total}'
                    #         },
                    #         #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                    #         'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                    #     },
                    {
                        'if': {
                                'filter_query': '{Variant Unique} eq F',
                                #'filter_query': '{Direction} eq +', 
                                #'column_id' :'Bulge Type'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(0, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
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
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    hash = hash.split('#')[1]
    guide = hash[:hash.find('-Sample-')]
    sample = hash[hash.rfind('-') + 1:]
    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
    
    filtering_expressions = filter.split(' && ')
    dff = global_store_general(current_working_directory + 'Results/'+ job_id + '/' + job_id + '.' + sample + '.' + guide + '.txt')
    if dff is None:
        raise PreventUpdate
    
    dff.rename(columns = COL_BOTH_RENAME , inplace = True)
    del dff['Correct Guide']         #NOTE Drop the Correct Guide column
    del dff['Variant Unique']
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
            ['Samples' if col['column_id'] == 'Samples Summary' else col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )

    #Calculate sample count
    dict_sample_to_pop, dict_pop_to_superpop = associateSample.loadSampleAssociation(job_directory + 'sampleID.txt')[:2]
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
    if (not isdir(current_working_directory + 'Results/' + job_id)):
        return html.Div(dbc.Alert("The selected result does not exist", color = "danger"))
    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    style_hide_reference = {'display':'none'}
    value_hide_reference = []
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
        style_hide_reference = {}
        value_hide_reference = ['hide-ref', 'hide-cluster']
    final_list = []
    final_list.append(
        html.H3('Selected Position: ' + chromosome + ' - ' + position)
    )
    
    
    if genome_type == 'ref':
        cols = [{"name": i, "id": i, 'type':t, 'hideable':True} for i,t in zip(COL_REF, COL_REF_TYPE)]
        file_to_grep = '.targets.cluster.txt'       
    else:
        cols = [{"name": i, "id": i, 'type':t, 'hideable':True} for i,t in zip(COL_BOTH, COL_BOTH_TYPE)]
        file_to_grep = '.total.cluster.txt'
    # print('qui cluster before grep')
    
    cluster_grep_result = current_working_directory + 'Results/'+ job_id + '/' + job_id + '.' + chromosome + '_' + position + '.' + guide +'.txt'
    put_header = 'head -1 ' + current_working_directory + 'Results/' + job_id + '/' + job_id + file_to_grep + ' > ' + cluster_grep_result + ' ; '
    # print('esiste cluster?' , str(os.path.exists(cluster_grep_result)) )
    if not os.path.exists(cluster_grep_result):    #Example    job_id.chr3_100.guide.txt
        #Grep annotation for ref
        if genome_type == 'ref':#NOTE HEADER NON SALVATO
            get_annotation = subprocess.Popen(['LC_ALL=C fgrep ' + guide + ' ' + current_working_directory + 'Results/'+ job_id + '/' + job_id + '.Annotation.targets.txt' + ' |  awk \'$6==' + position + ' && $4==\"' + chromosome + '\"\''], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = get_annotation.communicate()
            annotation_type = out.decode('UTF-8').strip().split('\t')[-1]
            subprocess.call([put_header + 'LC_ALL=C fgrep ' + guide + ' ' + current_working_directory + 'Results/'+ job_id + '/' + job_id + file_to_grep + ' | awk \'$6==' + position + ' && $4==\"' + chromosome + '\" {print $0\"\\t' + annotation_type + '\"}\' > ' + cluster_grep_result], shell = True)
        else:  
            # print('qui cluster in grep')     #NOTE HEADER NON SALVATO       
            subprocess.call([put_header + 'LC_ALL=C fgrep ' + guide + ' ' + current_working_directory + 'Results/'+ job_id + '/' + job_id + file_to_grep + ' | awk \'$6==' + position + ' && $4==\"' + chromosome + '\"\' > ' + cluster_grep_result], shell = True)  #NOTE top1 will have sample and annotation, other targets will have '.'-> 18/03 all samples and annotation are already writter for all targets
        subprocess.Popen(['zip ' + cluster_grep_result.replace('.txt','.zip') + ' ' + cluster_grep_result], shell = True)
    final_list.append(
        html.Div(job_id + '.' + chromosome + '_' + position + '.' + guide ,style = {'display':'none'}, id = 'div-info-sumbyposition-targets')
    ) 

    scomposition_file = current_working_directory + 'Results/'+ job_id + '/' + job_id + '.' + chromosome + '_' + position + '.' + guide +'.scomposition.txt'
    file_to_grep = '.samples.annotation.txt'

    iupac_scomposition_visibility = {'display':'none'}
    if genome_type != 'ref':                   
        iupac_scomposition_visibility = {}
        if not os.path.exists(scomposition_file):    #Example    job_id.chr_pos.guide.scomposition.txt
            subprocess.call(['LC_ALL=C fgrep ' + guide + ' ' + current_working_directory + 'Results/'+ job_id + '/' + job_id + file_to_grep + ' |  awk \'$6==' + position + ' && $4==\"' + chromosome + '\" && $13!=\"n\"\' > ' + scomposition_file], shell = True)

    final_list.append(html.P(
        [
            html.P('List of all the configurations for the target in the selected position.', style = iupac_scomposition_visibility),
            dcc.Checklist(
                options = [{'label': 'Hide Reference Targets', 'value': 'hide-ref'}, {'label': 'Show only TOP1 Target', 'value': 'hide-cluster'}], 
                id='hide-reference-targets', value = value_hide_reference, style = style_hide_reference
            ),
            html.Div(
                [   
                    html.P('Generating download link, Please wait...', id = 'download-link-sumbyposition'), 
                    dcc.Interval(interval = 5*1000, id = 'interval-sumbyposition')
                ]

            )
        ]
    )
    )
    
    cols_for_scomposition = cols.copy()
    cols_for_scomposition.append({"name": 'Samples', "id": 'Samples', 'type':'text', 'hideable':True})
    final_list.append(
        html.Div(
            dash_table.DataTable(
                id = 'table-scomposition-cluster',          #TABLE that represent scomposition of iupac of selected target, take rows from top_1.samples.txt
                columns=cols_for_scomposition, 
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
                    # {
                    #     'if': {
                    #             'filter_query': '{Variant Unique} eq y', 
                    #             #'column_id' :'{#Bulge type}',
                    #             #'column_id' :'{Total}'
                    #         },
                    #         #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                    #         'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                    #     },
                    {
                        'if': {
                                'filter_query': '{Variant Unique} eq F',
                                #'filter_query': '{Direction} eq +', 
                                #'column_id' :'Bulge Type'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(0, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        }
                ],
                css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],
                
            ),
            style = iupac_scomposition_visibility
        )
    )

    final_list.append(html.Hr())

    #Cluster Table
    final_list.append(
        'List of Targets found for the selected position. Other possible configurations of the target are listed in the table above, along with the corresponding samples list.', # The rows highlighted in red indicates that the target was found only in the genome with variants.',
    )
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
                    'max-height': '600px'
                    #'overflowY': 'scroll',
                },
                style_data_conditional=[
                    # {
                    #     'if': {
                    #             'filter_query': '{Variant Unique} eq y', 
                    #             #'column_id' :'{#Bulge type}',
                    #             #'column_id' :'{Total}'
                    #         },
                    #         #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                    #         'background-color':'rgba(255, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                    #     },
                    {
                        'if': {
                                'filter_query': '{Variant Unique} eq F',
                                #'filter_query': '{Direction} eq +', 
                                #'column_id' :'Bulge Type'
                            },
                            #'border-left': '5px solid rgba(255, 26, 26, 0.9)', 
                            'background-color':'rgba(0, 0, 0,0.15)'#'rgb(255, 102, 102)'
                            
                        }
                ],
                css= [{ 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;' }, { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'background-color: rgba(0, 0, 255,0.15) !important;'}],
                
            ),
            id = 'div-result-table',
        )
    )
    # final_list.append(html.Div('', id ='target-to-highlight'))
    return html.Div(final_list, style = {'margin':'1%'})

# #Save the first scomposition target from the second table, in order to highlight it in the first table
# @app.callback(
#     Output('target-to-highlight','children'),
#     [Input('table-scomposition-cluster', 'data')],
#     [State('target-to-highlight','children')]
# )
# def saveFirstScomposedTarget(data_scomp, current_target):
#     if current_target != '' or current_target is None:
#         raise PreventUpdate
#     if data_scomp is None or not data_scomp:
#         raise PreventUpdate
#     return data_scomp[0]['DNA']

# #update the Color of the top1 scomposed target in the first table
# @app.callback(
#     Output('table-position-target', 'style_data_conditional'),
#     [Input('target-to-highlight', 'children')]
# )
# def highlightSummaryTarget(to_highlight):
#     if to_highlight is None or to_highlight == '':
#         raise PreventUpdate
#     return [{'if': {'filter_query': '{DNA} eq ' + to_highlight}, 'font-weight':'bold'}]

#Filter/sort cluster
#Filter and sorting sample targets
@app.callback(
    Output('table-position-target', 'data'),
    [Input('table-position-target', "page_current"),
     Input('table-position-target', "page_size"),
     Input('table-position-target', 'sort_by'),
     Input('table-position-target', 'filter_query'),
     Input('hide-reference-targets', 'value')],
    [State('url', 'search'),
     State('url', 'hash')]    
)
def update_table_cluster(page_current, page_size, sort_by, filter, hide_reference, search, hash):
    job_id = search.split('=')[-1]
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    hash = hash.split('#')[1]
    guide = hash[:hash.find('-Pos-')]
    chr_pos = hash[hash.find('-Pos-') + 5:]
    chromosome = chr_pos.split('-')[0]
    position = chr_pos.split('-')[1]
    
    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'
    
    filtering_expressions = filter.split(' && ')
    dff = global_store_general(current_working_directory + 'Results/' + job_id + '/' + job_id + '.' + chromosome + '_' + position + '.' + guide +  '.txt')
    if dff is None:
        raise PreventUpdate

    if genome_type == 'ref':
        dff.rename(columns = COL_REF_RENAME, inplace = True)
    else:                           
        dff.rename(columns =COL_BOTH_RENAME , inplace = True)

    if genome_type != 'ref':
        # add_samples = [dff['Samples'][0]] * dff.shape[0]
        # check_minmms = dff['Min Mismatches']
        # if dff['Variant Unique'][0] != 'y' and dff['PAM Creation'][0] == 'n':
        #     for pos_minmms, minmms in enumerate(check_minmms):
        #         if minmms == '-':
        #             add_samples[pos_minmms] = 'n'
        # dff['Samples'] = add_samples
        del dff['Variant Unique']
        # dff.drop(dff.head(1).index, inplace=True)       #Remove first target, that is the top1 with no iupac (lowest mm of scomposed target) and is 
                                                    #needed only for summary by guide, not the show target part
                                                    #NOTE 18/03 removed all the iupac char, the first line is needed to be shown
    # dff['Annotation Type'] = list(dff['Annotation Type'])[0]
    del dff['Correct Guide']
    
    if 'hide-ref' in hide_reference or genome_type == 'var':
        dff.drop( dff[(dff['Samples'] == 'n')].index, inplace = True)

    if 'hide-cluster' in hide_reference:
        dff = dff.head(1)

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
            ['Samples' if col['column_id'] == 'Samples Summary' else col['column_id'] for col in sort_by],
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
    if genome_type != 'ref':
        dict_sample_to_pop, dict_pop_to_superpop = associateSample.loadSampleAssociation(job_directory + 'sampleID.txt')[:2]
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


#Filter/sort IUPAC decomposition table for cluster page
@app.callback(
    Output('table-scomposition-cluster','data'),
    [Input('table-scomposition-cluster', "page_current"),
     Input('table-scomposition-cluster', "page_size"),
     Input('table-scomposition-cluster', 'sort_by'),
     Input('table-scomposition-cluster', 'filter_query')],
    [State('url', 'search'),
     State('url', 'hash')]
)
def update_iupac_scomposition_table_cluster(page_current, page_size, sort_by, filter, search, hash):
    job_id = search.split('=')[-1]
    job_directory = current_working_directory + 'Results/' + job_id + '/'
    hash = hash.split('#')[1]
    guide = hash[:hash.find('-Pos-')]
    chr_pos = hash[hash.find('-Pos-') + 5:]
    chromosome = chr_pos.split('-')[0]
    position = chr_pos.split('-')[1]
    
    with open(current_working_directory + 'Results/' + job_id + '/Params.txt') as p:
        all_params = p.read()
        genome_type_f = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
        ref_comp = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
        
    genome_type = 'ref'
    if '+' in genome_type_f:
        genome_type = 'var'
    if 'True' in ref_comp:
        genome_type = 'both'

    if genome_type == 'ref':       
        raise PreventUpdate
    
    filtering_expressions = filter.split(' && ')
    dff = global_store_general(current_working_directory + 'Results/'+ job_id + '/' + job_id + '.' + chromosome + '_' + position + '.' + guide +'.scomposition.txt')
    if dff is None:
        raise PreventUpdate
    
    # #Grep annotation
    # file_to_grep = '.Annotation.targets.txt'
    # get_annotation = subprocess.Popen(['LC_ALL=C fgrep ' + guide + ' ' + current_working_directory + 'Results/'+ job_id + '/' + job_id + file_to_grep + ' |  awk \'$6==' + position + ' && $4==\"' + chromosome + '\"\''], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # out, err = get_annotation.communicate()
    # annotation_type = out.decode('UTF-8').strip().split('\t')[-1]
    
    # if genome_type == 'var':           
    #     dff.rename(columns = {0:'Bulge Type', 1:'crRNA', 2:'DNA', 3:'Chromosome', 4:'Position', 5:'Cluster Position', 6:'Direction',
    #     7:'Mismatches', 8:'Bulge Size', 9:'Total', 10:'Min Mismatches', 11:'Max Mismatches', 12:'Samples', 13:'Correct Guide', 14:'Annotation Type',15:'Top Subcluster'}, inplace = True)
    # else:
    dff.rename(columns = COL_BOTH_RENAME , inplace = True)
    # dff.drop(dff.columns[[-1,]], axis=1, inplace=True)         #NOTE Drop the Correct Guide column
    del dff['Correct Guide']
    #dff['Annotation Type'] = annotation_type
    del dff['Variant Unique']
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
            ['Samples' if col['column_id'] == 'Samples Summary' else col['column_id'] for col in sort_by],
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
    if genome_type != 'ref':
        dict_sample_to_pop, dict_pop_to_superpop = associateSample.loadSampleAssociation(job_directory + 'sampleID.txt')[:2]
        for row in data_to_send:
            summarized_sample_cell = dict()
            for s in row['Samples'].split(','):
                if s == 'n':
                    break     #If a target have n, it means it's REF, because either all have samples or the single target is REF
                try:
                    summarized_sample_cell[dict_pop_to_superpop[dict_sample_to_pop[s]]] += 1
                except:
                    summarized_sample_cell[dict_pop_to_superpop[dict_sample_to_pop[s]]] = 1
            if summarized_sample_cell:
                row['Samples Summary'] = ', '.join([str(summarized_sample_cell[sp]) + ' ' + sp for sp in summarized_sample_cell])
            else:
                row['Samples Summary'] = 'n'
    return data_to_send

#Generate download link sumbyguide
@app.callback(
    [Output('download-link-sumbyguide', 'children'),
    Output('interval-sumbyguide', 'disabled')],
    [Input('interval-sumbyguide','n_intervals')],
    [State('div-info-sumbyguide-targets','children'),
    State('url', 'search')]
)
def downloadLinkGuide(n, file_to_load, search): #file to load = job_id.RNA.1.0.guide
    if n is None:
        raise PreventUpdate
    job_id = search.split('=')[-1]
    file_to_load = file_to_load + '.zip'
    if os.path.exists(current_working_directory + 'Results/' + job_id + '/' + file_to_load):
        return html.A('Download zip', href=URL+'/data/' + job_id + '/' + file_to_load, target = '_blank' ), True
    
    return 'Generating download link, Please wait...', False

# Generate download link sumbysample
@app.callback(
    [Output('download-link-sumbysample', 'children'),
    Output('interval-sumbysample', 'disabled')],
    [Input('interval-sumbysample','n_intervals')],
    [State('div-info-sumbysample-targets','children'),
    State('url', 'search')]
)
def downloadLinkSample(n, file_to_load, search): #file to load = job_id.HG001.guide
    if n is None:
        raise PreventUpdate
    job_id = search.split('=')[-1]
    file_to_load = file_to_load + '.zip'
    if os.path.exists(current_working_directory + 'Results/' + job_id + '/' + file_to_load):
        return html.A('Download zip', href=URL+'/data/' + job_id + '/' + file_to_load, target = '_blank' ), True
    
    return 'Generating download link, Please wait...', False

#Generate download link sumbyposition
@app.callback(
    [Output('download-link-sumbyposition', 'children'),
    Output('interval-sumbyposition', 'disabled')],
    [Input('interval-sumbyposition','n_intervals')],
    [State('div-info-sumbyposition-targets','children'),
    State('url', 'search')]
)
def downloadLinkPosition(n, file_to_load, search): #file to load = 
    if n is None:
        raise PreventUpdate
    job_id = search.split('=')[-1]
    file_to_load = file_to_load + '.zip'
    if os.path.exists(current_working_directory + 'Results/' + job_id + '/' + file_to_load):
        return html.A('Download zip', href=URL+'/data/' + job_id + '/' + file_to_load, target = '_blank' ), True
    
    return 'Generating download link, Please wait...', False

############################ Genome Database Page Callbacks ##########################

@app.callback(
    Output('genomes-table', 'data'),
    [Input('genomes-table', "page_current"),
     Input('genomes-table', "page_size"),
     Input('genomes-table', 'sort_by'),
     Input('genomes-table', 'filter_query')])
def updateGenomePageTable(page_current, page_size, sort_by, filter):
    filtering_expressions = filter.split(' && ')
    dff = get_genomes.get_genomes(current_working_directory)
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

    page = page_current
    size = page_size
    return dff.iloc[page * size: (page + 1) * size].to_dict('records')


############################ History Page ##########################

def get_results():
    '''
    Get a dataframe of the Results directory
    '''
    results_dirs = [join(current_working_directory + '/Results/', f) for f in listdir(current_working_directory + '/Results/') if isdir(join(current_working_directory + '/Results/', f)) and isfile(current_working_directory + '/Results/' + f + '/Params.txt')]
    results_dirs.sort(key = os.path.getctime)   #Sorted older first
    results_dirs = [os.path.basename(f) for f in results_dirs]
    col = ['Job ID', 'Genome', 'PAM', 'Mismatches', 'DNA Bulges', 'RNA Bulges', 'Gecko Comparison', 'Reference Comparison', 'Date', 'Load']
    a = pd.DataFrame(columns = col)
    for job in results_dirs:
        if os.path.exists(current_working_directory + '/Results/' + job + '/Params.txt'):
            with open(current_working_directory  + '/Results/' + job + '/Params.txt') as p:
                all_params = p.read()
                mms = (next(s for s in all_params.split('\n') if 'Mismatches' in s)).split('\t')[-1]
                genome_selected = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
                genome_selected = genome_selected.replace('_',' ')
                if os.path.exists(current_working_directory + '/Results/' + job + '/log.txt'):
                    with open(current_working_directory  + '/Results/' + job + '/log.txt') as lo:
                        all_log = lo.read()
                    job_start = (next(s for s in all_log.split('\n') if 'Job\tStart' in s)).split('\t')[-1]
                    try:
                        job_end = (next(s for s in all_log.split('\n') if 'Job\tDone' in s)).split('\t')[-1]
                    except:
                        link_load = URL + '/load?job=' + job
                    else:
                        link_load = URL + '/result?job=' + job
                else:
                    job_start = 'n/a'
                    link_load = URL + '/load?job=' + job
                dna = (next(s for s in all_params.split('\n') if 'DNA' in s)).split('\t')[-1]
                rna = (next(s for s in all_params.split('\n') if 'RNA' in s)).split('\t')[-1]
                pam = (next(s for s in all_params.split('\n') if 'Pam' in s)).split('\t')[-1]
                gecko = (next(s for s in all_params.split('\n') if 'Gecko' in s)).split('\t')[-1]
                if gecko == 'True':
                    gecko = 'Yes'
                else:
                    gecko = 'No'
                comparison = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
                if comparison == 'True':
                    comparison = 'Yes'
                else:
                    comparison = 'No'
                if os.path.exists(current_working_directory + '/Results/' + job + '/guides.txt'):
                    with open(current_working_directory  + '/Results/' + job + '/guides.txt') as g:
                        n_guides = str(len(g.read().strip().split('\n')))
                else:
                    n_guides ='n/a'
                
                a = a.append({'Job ID':job, 'Genome':genome_selected, 'Mismatches':mms, 'DNA Bulges':dna,
                'RNA Bulges':rna, 'PAM':pam,'Gecko Comparison':gecko,'Reference Comparison':comparison, 'Date':job_start, 'Load': link_load, 'Delete':''}, ignore_index = True)
    a = a.sort_values(['Mismatches','DNA Bulges','RNA Bulges'],ascending = [True, True, True])
    return a

def generate_table_results(dataframe, page, max_rows = 10):
    '''
    Generate table for History page
    '''
    fl = []
    rows_remaining = len(dataframe) - (page - 1) * max_rows
    header = html.Thead(
            html.Tr([html.Th(col,style = {'vertical-align':'middle', 'text-align':'center'}) if col != 'Load' and col != 'Delete' else html.Th('',style = {'vertical-align':'middle', 'text-align':'center'})  for col in dataframe.columns])
        )
    body_history = []
    add_button = 0
    for i in range(min(rows_remaining, max_rows)):
        add_button += 1
        row_hist = []
        for col in dataframe.columns:
            if col == 'Load':
                row_hist.append(
                        html.Td(html.A('Load', target = '_blank', href = dataframe.iloc[i + (page - 1)*max_rows][col]), style = {'vertical-align':'middle', 'text-align':'center'})
                )
            elif col == 'Delete':
                row_hist.append(
                    html.Td(html.Button('Delete', id = 'button-delete-history-'+str(i), **{'data-jobid':dataframe.iloc[i + (page - 1)*max_rows]['Job ID']}),style = {'vertical-align':'middle', 'text-align':'center'})
                )
            else:
                row_hist.append(
                        html.Td(dataframe.iloc[i + (page - 1)*max_rows][col], style = {'vertical-align':'middle', 'text-align':'center'})
                    )
        body_history.append(html.Tr(row_hist))
    fl.append(
        html.Table([
            header,
            html.Tbody(body_history)
        ], style = {'display':'inline-block'},)
    )
    
    for i in range(add_button, 10): #Add hidden buttons for callback removeJobId compatibility
        fl.append(html.Button(
            str(i), id = 'button-delete-history-'+str(i),**{'data-jobid':'None'}, style = {'display':'none'}
            ))
    return fl


def historyPage():
    '''
    Create the History page
    '''
    results = get_results()
    final_list = []

    final_list.append(
        html.Div(
            [
                html.H3('Results History'),
                html.P('List of available results. Click on the \'Load\' link to open the corresponding result in a new page.')
            ]
        )
    )
    final_list.append(
            html.Div
                (
                    [
                        dbc.Row(
                            [
                                dbc.Col(html.Div(dcc.Dropdown(options = availableGenomes(), id = 'dropdown-genomes-history', placeholder = 'Select a Genome'))),
                                dbc.Col(html.Div(dcc.Dropdown(options = availablePAM(), id = 'dropdown-pam-history', placeholder = 'Select a PAM'))),
                                # dbc.Col(html.Div(dcc.Dropdown(options = av_mismatches, id = 'dropdown-mms-history', placeholder = 'Select a Mismatch value' ))),
                                # dbc.Col(html.Div(dcc.Dropdown(options = av_bulges, id = 'dropdown-dna-history', placeholder = 'Select a DNA Bulge value' ))),
                                # dbc.Col(html.Div(dcc.Dropdown(options = av_bulges, id = 'dropdown-rna-history', placeholder = 'Select a RNA Bulge value' ))),


                                dbc.Col(html.Div(html.Button('Filter', id = 'button-filter-history')))
                            ]
                        ),
                    ],
                )
        )
    final_list.append(html.Div('None,None',id = 'div-history-filter-query', style = {'display':'none'}))

    final_list.append(
            html.Div(
                generate_table_results(results,1),
                id = 'div-history-table',
                style = {'text-align': 'center'}
            ),
    )
    final_list.append(
        html.Div(id = 'div-remove-jobid', style = {'display':'none'})
    )
    final_list.append(
        html.Div(
            [
                html.Br(),
                html.Button('Prev', id = 'prev-page-history'),
                html.Button('Next', id = 'next-page-history')
            ],
            style = {'text-align': 'center'}
        )
    )
    max_page = len(results.index)
    max_page = math.floor(max_page / 10) + 1
    final_list.append(html.Div('1/' + str(max_page), id= 'div-current-page-history'))
    page = html.Div(final_list, style = {'margin':'1%'})
    return page

#Callback to update the hidden div filter of history page
@app.callback(
    Output('div-history-filter-query', 'children'),
    [Input('button-filter-history', 'n_clicks')],
    [State('dropdown-genomes-history', 'value'),
    State('dropdown-pam-history', 'value')]
)
def updateHistoryFilter(n, genome, pam):
    if n is None:
        raise PreventUpdate
    return str(genome) + ',' + str(pam)


def supportFilterHistory(result_df, genome_f, pam_f):
    if genome_f is not None:
        result_df.drop(result_df[(result_df['Genome'] != genome_f)].index, inplace = True)
    if pam_f is not None:
        keep_values = []
        for index, row in result_df.iterrows():
            if row.PAM not in pam_f:
                keep_values.append(index)
        result_df.drop(labels= keep_values, inplace = True)

    max_page = len(result_df.index)
    max_page = math.floor(max_page / 10) + 1
    return result_df, max_page

#Remove Results and Apply Filtering
@app.callback(
    [Output('div-history-table', 'children'),
    Output('div-current-page-history', 'children')],
    [Input('button-delete-history-0', 'n_clicks_timestamp'),
    Input('button-delete-history-1', 'n_clicks_timestamp'),
    Input('button-delete-history-2', 'n_clicks_timestamp'),
    Input('button-delete-history-3', 'n_clicks_timestamp'),
    Input('button-delete-history-4', 'n_clicks_timestamp'),
    Input('button-delete-history-5', 'n_clicks_timestamp'),
    Input('button-delete-history-6', 'n_clicks_timestamp'),
    Input('button-delete-history-7', 'n_clicks_timestamp'),
    Input('button-delete-history-8', 'n_clicks_timestamp'),
    Input('button-delete-history-9', 'n_clicks_timestamp'),
    Input('prev-page-history', 'n_clicks_timestamp'),
    Input('next-page-history', 'n_clicks_timestamp'),
    Input('div-history-filter-query', 'children')],
    [State('button-delete-history-0', 'data-jobid'),
    State('button-delete-history-1', 'data-jobid'),
    State('button-delete-history-2', 'data-jobid'),
    State('button-delete-history-3', 'data-jobid'),
    State('button-delete-history-4', 'data-jobid'),
    State('button-delete-history-5', 'data-jobid'),
    State('button-delete-history-6', 'data-jobid'),
    State('button-delete-history-7', 'data-jobid'),
    State('button-delete-history-8', 'data-jobid'),
    State('button-delete-history-9', 'data-jobid'),
    State('button-filter-history', 'n_clicks_timestamp'),
    State('url', 'search'),
    State('div-current-page-history', 'children')
    ]
)
def removeJobIDandFilter(n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, nPrev, nNext, filter_q, jID0, jID1, jID2, jID3, jID4, jID5, jID6, jID7, jID8, jID9, n, search, current_page):
    #Get last pressed button
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
    if not nPrev:
        nPrev = 0
    if not nNext:
        nNext = 0
    if not n:
        n = 0
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
    btn_group.append(nPrev)
    btn_group.append(nNext)
    btn_group.append(n)
    
    genome_filter = filter_q.split(',')[0]
    pam_filter = filter_q.split(',')[1]
    if genome_filter == 'None':
        genome_filter = None
    if pam_filter == 'None':
        pam_filter = None
    current_page = current_page.split('/')[0]
    current_page = int(current_page)
    results = get_results()
    selectedID = ''

    if max(btn_group) == 0:
        selectedID = ''
    elif max(btn_group) == n0:
        selectedID = jID0
    elif max(btn_group) == n1:
        selectedID = jID1
    elif max(btn_group) == n2:
        selectedID = jID2
    elif max(btn_group) == n3:
        selectedID = jID3
    elif max(btn_group) == n4:
        selectedID = jID4
    elif max(btn_group) == n5:
        selectedID = jID5
    elif max(btn_group) == n6:
        selectedID = jID6
    elif max(btn_group) == n7:
        selectedID = jID7
    elif max(btn_group) == n8:
        selectedID = jID8
    elif max(btn_group) == n9:
        selectedID = jID9
    elif max(btn_group) == n:    #Filter Button selected, return the first page of the filtered table
        results, max_page = supportFilterHistory(results, genome_filter, pam_filter)
        return generate_table_results(results,1), '1/' + str(max_page)
    elif max(btn_group) == nNext:   #Next Button of the table
        current_page = current_page + 1
        results, max_page = supportFilterHistory(results, genome_filter, pam_filter)
        if ((current_page - 1) * 10) > len(results): 
            current_page = current_page -1
            if current_page < 1:
                current_page = 1
        return generate_table_results(results,current_page), str(current_page) + '/' + str(max_page)
    elif max(btn_group) == nPrev:   #Go to previous page
        current_page = current_page - 1
        if current_page < 1:
            current_page = 1
        results, max_page = supportFilterHistory(results, genome_filter, pam_filter)
        return generate_table_results(results,current_page), str(current_page) + '/' + str(max_page)

    if selectedID == '':
        raise PreventUpdate
    result_removed = Gmsg.deleteResultConfirm(selectedID)
    if result_removed:      #If the result was removed, update the table
        results, max_page = supportFilterHistory(get_results(), genome_filter, pam_filter)
        return generate_table_results(results,1), '1/' + str(max_page)
    else:
        raise PreventUpdate
    results, max_page = supportFilterHistory(get_results(), genome_filter, pam_filter)
    return generate_table_results(results,1), '1/' + str(max_page)


############################ GUI CALLBACKS #########################
#Add a new genome
@app.callback(
    Output("genome-job","value"),        
    [Input("add-genome","n_clicks")],  
)
def add_genome(nAdd):
    """
    Bottone per avviare la GUI in Tkinter per l'aggiunta di genomi offline
    """
    from GUI import ChooseFiles as cf
    if nAdd is None:
        raise PreventUpdate
    cf.startChooseFiles(current_working_directory,  app_location + 'GUI/' )
    return ''

#Update an existing dictionary    
@app.callback(
    Output("dict-job","value"),        
    [Input("update-dict","n_clicks")],  
)
def update_dict(nUpd):
    """
    Bottone per avviare la GUI in Tkinter per l'aggiornamento di dizionari
    """
    from GUI import UpdateDict as ud
    if nUpd is None:
        raise PreventUpdate
    ud.startUpdateDict(current_working_directory)
    return ''


#Open filedialog for choosing new annotation file 
@app.callback(
    [Output('label-new-annotation-selected', 'children'),
    Output('tooltip-label-new-annotation-selected', 'children')],
    [Input('button-choose-new-annotation', 'n_clicks')]
)
def fileDialogUpdateAnnotation(n):
    selected_file = openDialog(n, 'F')
    return 'Selected: ' + os.path.basename(selected_file), 'Full Path: ' + selected_file


#Change annotation of selected Genome row
@app.callback(
    Output('ann-job', 'children'),
    [Input('change-ann','n_clicks')],
    [ State('genomes-table', 'derived_virtual_data'),
     State('genomes-table', 'selected_rows'),
     State('tooltip-label-new-annotation-selected', 'children'),
     State('radioitems-new-annotation', 'value')]
    )
def change_annotation(nChg, rows, selected_row, selected_new_ann, selected_type):
    if nChg is None:
        raise PreventUpdate
    if len(selected_row) == 0:
        return dbc.Alert("Warning! Please select a Genome!", is_open=True, duration=5000, color = 'warning' )
    selected_new_ann = selected_new_ann.split('Full Path: ')[-1]
    if not isfile(selected_new_ann):
        return dbc.Alert("Error! The selected file does not exist!", is_open=True, duration=7000, color = 'danger' )
    if selected_type is None:
        return dbc.Alert("Warning! Please select an option (Overwrite or Extend)!", is_open=True, duration=7000, color = 'warning' )
    row = pd.DataFrame(rows).iloc[selected_row,:] 
    annotationFile = row["Annotation File"].iloc[0]

    if selected_type == 'replace':
        subprocess.run(['cp', selected_new_ann ,current_working_directory + 'annotations/' + annotationFile])
    else:
        with open (current_working_directory + 'annotations/' + annotationFile, 'a') as oldAnn:
            with open (selected_new_ann, 'r') as newAnn:
                for line in newAnn:
                    oldAnn.write("\n"+line.strip())
                    
    
    # from GUI import annotations as ann
    # ann.startChangeAnn(current_working_directory+"/annotations/"+str(annotationFile))
    
    #Return an alert if the job is completed
    return dbc.Alert(
            "Completed! The annotation file is updated!",
            id="alert-auto",
            is_open=True,
            duration=5000,
        )

if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run_server(host='0.0.0.0', debug=True, port=8050)
    #app.run_server(host='0.0.0.0',  port=8080) #NOTE to not reload the page when creating new images in graphical report
    cache.clear()       #delete cache when server is closed

    #BUG nel filtering se ho, in min mismatch etc, la stringa '-', che non è considerata numero
    #NOTE: l'ordinamento su Samples Summary o su Samples è fatto su stringhe, e non su numero di samples (potrebbe essere più utile)
    #BUG see https://github.com/plotly/dash/issues/1049; Location component is called twice, meaning that two grep can occure at once.
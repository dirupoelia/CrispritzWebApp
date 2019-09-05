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
        return html.Div([
            html.H3('Tab content 1'),
            dcc.Graph(
                id='graph-1-tabs',
                figure={
                    'data': [{
                        'x': [1, 2, 3],
                        'y': [3, 1, 2],
                        'type': 'bar'
                    }]
                }
            )
        ])
    elif tab == 'index-genome':
        final_list = []
        final_list.append(html.P('Tool to find the candidate targets in a genome starting from a PAM. The ouput is a set of files, containing all the sequences of candidate targets extracted from the genome.'))
        
        #Genome name
        final_list.extend([html.Label('Insert the name for the  output Genome Index'), dcc.Input(id = 'name-genome', placeholder='Example: hg19_ref', type='text')])

        #Dropdown available genomes
        onlydir = [f for f in listdir('Genomes') if isdir(join('Genomes', f))]
        gen_dir = []
        for dir in onlydir:
            gen_dir.append({'label': dir, 'value' : dir})
        final_list.append(html.P(["Select an available Genome ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your directory containing the fasta file(s) into the Genomes directory"))]))
        final_list.append(html.Div(dcc.Dropdown(options = gen_dir, clearable = False, id = "available-genomes"), id = 'div-available-genomes'))

        #Dropdown available PAM
        onlyfile = [f for f in listdir('pam') if isfile(join('pam', f))]
        pam_file = []
        for pam_name in onlyfile:
            pam_file.append({'label': pam_name, 'value' : pam_name})
        final_list.append(html.P(["Select an available PAM ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your PAM text file into the pam directory"))]))
        final_list.append(html.Div(dcc.Dropdown(options = pam_file, clearable = False, id = "available-pams"), id = 'div-available-pams'))
        #TODO se lascio il rosso nel div, se metto un elemento rimane il rosso, sistemare o lasciare così
        #Number of max bulges
        final_list.extend([html.Label('Insert # of max allowed bulges'), dcc.Input(id = 'max-bulges', placeholder='Example: 2', type='number', min = 0)])
        final_list.append(html.P())

        #Submit job
        final_list.append(html.Button('Submit', id='submit-index-genome'))
        final_list.append(html.Div(id = "executing-index-genome"))
        return final_list
    
    elif tab == 'search':
        final_list = []
        final_list.append(html.P('Tool to perform off-target search on a genome (with or without variants) or genome index (with or without variants). The ouput is a set of files, one is a list of all targets and off-targets found, the others are profile files containing detailed information for each guide , like bp/mismatches and on/off-targets count.'))

        #Boolean switch for Index search
        final_list.append(html.Div(daq.BooleanSwitch(on = False, label = "Use Index Search", labelPosition = "top", id = 'index-search')))

        #Dropdown available genomes
        onlydir = [f for f in listdir('Genomes') if isdir(join('Genomes', f))]
        gen_dir = []
        for dir in onlydir:
            gen_dir.append({'label': dir, 'value' : dir})
        final_list.append(html.P(["Select an available Genome ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your directory containing the fasta file(s) into the Genomes directory"))]))
        final_list.append(dcc.Dropdown(options = gen_dir, clearable = False, id = "available-genomes-search"))

        #Dropdown available PAM
        onlyfile = [f for f in listdir('pam') if isfile(join('pam', f))]
        pam_file = []
        for pam_name in onlyfile:
            pam_file.append({'label': pam_name, 'value' : pam_name})
        final_list.append(html.P(["Select an available PAM ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your PAM text file into the pam directory"))]))
        final_list.append(html.Div(dcc.Dropdown(options = pam_file, clearable = False, id = "available-pams-search"), style = {'border': '3px solid red'}))

        #Dropdown available guide file
        onlyfile = [f for f in listdir('guides') if isfile(join('guides', f))]
        guide_file = []
        for guide_name in onlyfile:
            guide_file.append({'label': guide_name, 'value' : guide_name})
        final_list.append(html.P(["Select an available Guide file ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your Guide text file into the guides directory"))]))
        final_list.append(html.Div(dcc.Dropdown(options = guide_file, clearable = False, id = "available-guides-search")))


        #Genome name
        final_list.extend([html.Label('Insert the name for the  output result files'), dcc.Input(id = 'name-result-file', placeholder='Example: emx1.hg19', type='text')])

        #Number of Mimatches and DNA/RNA bulges
        final_list.append(
            html.Div(
                [html.Div(
                    [html.Label('Insert # of mismatches'),
                    dcc.Input(id = 'max-mms', placeholder='Example: 2', type='number', min = 0)]
                ), 
                html.Div(
                    [html.Label('Insert # of DNA bulges'),
                    dcc.Input(id = 'max-dna', placeholder='Example: 2', type='number', min = 0, disabled = True)]
                ),
                html.Div(
                    [html.Label('Insert # of RNA bulges'),
                    dcc.Input(id = 'max-rna', placeholder='Example: 2', type='number', min = 0, disabled = True)]
                )],
                id = "container-m-d-r",
                className = "flex-container-mdr-search",
                style = {'width' : '50%'}
            )
        )

        #Set Type of result
        final_list.extend(
            [html.Label('Select type of result:'),
            dcc.Checklist(
                options = [
                    {'label' : 'Off-targets list', 'value': 'r'},
                    {'label' : 'Profile', 'value': 'p'}
                ],
                value = ['r'],
                id = 'result-checklist'
            )
            ]
        )

        #Boolean switch for Score calculation
        final_list.append(
            html.Div(
                [daq.BooleanSwitch(on = False, label = "Calculate Scores", labelPosition = "top", id = 'score-switch', style = {'align-items':'start'}),          #TODO sistemare posizione del bottone
                dcc.Dropdown(options = gen_dir, clearable = False, id = "scores-available-genomes-search", style = {'width':'50%'})
                ],
                id = 'container-scores',
                className = "flex-container-score",
                style = {'width' : '50%'}
            )
        )
        #TODO add number thread selector
        
        final_list.append(html.Br())

        #Submit job
        final_list.append(html.Button('Submit', id='submit-search-genome'))
        final_list.append(html.Div(id = "executing-search-genome"))

        #TODO quando il search finisce, i risultati sono salvati in una cartella Results col nome in input
        return final_list
    elif tab == 'annotate-results':
        final_list = []
        final_list.append(html.P('Tool to annotate results found during search with functional annotations (promoter, chromatin accessibility, insulator, etc). The output is a set of files, one is the list of on/off-targets with the annotation type, the others are files containing counts for each guide, the counts are the total on/off-targets found with the specific mismatch threshold and the specific annotation.'))
        
        #Dropdown available guide file
        onlyfile = [f for f in listdir('guides') if isfile(join('guides', f))]
        guide_file = []
        for guide_name in onlyfile:
            guide_file.append({'label': guide_name, 'value' : guide_name})
        final_list.append(html.P(["Select an available Guide file ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your Guide text file into the guides directory"))]))
        final_list.append(html.Div(dcc.Dropdown(options = guide_file, clearable = False, id = "available-guides-annotation"), id = 'div-available-guides-annotation'))

        #Dropdown available result file
        onlydir = [f for f in listdir('Results') if isdir(join('Results', f))]
        result_file = []
        for result_name in onlydir:
            result_file.append({'label': result_name, 'value' : result_name})
        final_list.append(html.P(["Select an available result file ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your directory containing the result file into the Results directory"))]))
        final_list.append(html.Div(dcc.Dropdown(options = result_file, clearable = False, id = "available-results-annotation"), id = 'div-available-results-annotation')) #Note that we need the .targets.txt file inside the selected directory

        #Genome name
        final_list.extend([html.Label('Insert the name for the  output annotated result file'), dcc.Input(id = 'name-result-file-annotated', placeholder='Example: emx1.hg19.annotated', type='text')])
        
        #Upload text file with path
        final_list.append(
            html.Div(
                [html.P('Select file containing path for annotation'),
                dcc.Upload(html.Button('Upload File', id = 'button-upload-path-annotation'), id = 'upload-path-annotation'),
                html.P('', id = 'name-upload-file-annotation')]
            )  
        )
        
        #Submit job
        final_list.append(html.Button('Submit', id='submit-annotate-result'))
        final_list.append(html.Div(id = "executing-annotate-result"))

        return final_list
    elif tab == 'generate-report':
        final_list = []
        final_list.append(html.P('Tool to generate a graphical report with annotated and overall mismatch and bulge profile for a given guide. The output is a graphical representation of the input guide behaviour.'))
        
        #Guide Sequence
        final_list.extend([html.Label('Insert the Guide sequence'), dcc.Input(id = 'guide-sequence-report', placeholder='Example: GAGTCCGAGCAGAAGAAGAANNN', type='text')])
        
        #Number of mismatches
        final_list.append(dcc.Input(id = 'max-mms-report', placeholder='Example: 2', type='number', min = 0))

        #Dropdown available result file
        onlydir = [f for f in listdir('Results') if isdir(join('Results', f))]
        result_file = []
        for result_name in onlydir:
            result_file.append({'label': result_name, 'value' : result_name})
        final_list.append(html.P(["Select an available result file ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your directory containing the result file into the Results directory"))]))
        final_list.append(html.Div(dcc.Dropdown(options = result_file, clearable = False, id = "available-results-report"), id = 'div-available-results-report')) #Note that we need the .targets.txt file inside the selected directory
        #From the dropdown, we could select and check if all files are available: profile, ext_profile, introns, exons etc...

        #Gecko comparison
        final_list.append(daq.BooleanSwitch(on = False, label = "Activate the gecko dataset comparison", labelPosition = "top", id = 'gecko-comparison-report')) #TODO sistemare posizione del bottone

        #Submit job
        final_list.append(html.Button('Submit', id='submit-generate-report'))
        final_list.append(html.Div(id = "executing-generate-report"))

        return final_list
    elif tab == 'view-report':
        final_list = []

        #Images from the report #TODO modify the 3 call for .savefig to also create png images in radar_chart.py and radar_chart_docker.py
        onlydir = [f for f in listdir('Results') if isdir(join('Results', f))]
        result_file = []
        for result_name in onlydir:
            result_file.append({'label': result_name, 'value' : result_name})
        final_list.append(html.P(["Select an available result file ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your directory containing the result file into the Results directory"))]))
        final_list.append(html.Div(
            dcc.Dropdown(options = result_file, clearable = False, id = "available-results-view", style={'position':'relative', 'zIndex':'999', 'widht':'50%'}),     #position and zindex is for avoid being under column fixed
            id = 'div-available-results-view')
        )
        final_list.append(html.Br())

        #Table for targets and score#TODO check if user has created only targets or also scores
        
        col_list = ['BulgeType', 'crRNA', 'DNA', 'Chromosome', 'Position', 'Direction', 'Mismatches', 'BulgeSize', 'CFD', 'Doench2016']
        col_type = ['text','text','text','text','numeric','text','numeric', 'numeric', 'numeric', 'numeric', 'numeric']
        cols = [{"name": i, "id": i, 'type':t} for i,t in zip(col_list, col_type)]
        final_list.append(dash_table.DataTable(
            id='result-table', 
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
            filter_query=''
            )
        )
        
        # hidden signal value
        final_list.append(html.Div(id='signal', style={'display': 'none'}))
        
        final_list.append(html.Div([
                html.Img(id = 'selected-img', width="65%", height="65%"),
                html.Div([html.Button('Submit-test', id = 'test-button'), html.P(id = 'filename-show')], id = 'container-button-filename-show', className = 'flex-container-button-filename-show')
            ],
            id = 'container-img-button-show',
            className = "flex-container-img-button-show"
            )
        )
        #final_list.append(html.Br())
        #final_list.append(html.Button('Submit-test', id = 'test-button'))
        

        final_list.append(html.Div(id='intermediate-value', style={'display': 'none'})) #Hidden div to save data for img show (contains list of all images available in a result directory)
        return final_list
    
###################################################### CALLBACKS ######################################################

#############################
# Callbacks for Add variant #
#############################

##########################
# Callbacks for Indexing #
##########################

#Execute Indexing of a genome
@app.callback([Output("executing-index-genome", "children"),
            Output('name-genome', 'required'),
            Output('max-bulges', 'required'),
            Output('div-available-genomes', 'style'),
            Output('div-available-pams', 'style')],
            [Input('submit-index-genome', 'n_clicks')],
            [State('max-bulges', 'value'),
            State('name-genome', 'value'),
            State('available-genomes', 'value'),
            State('available-pams', 'value')])
def executeIndex(n_clicks, max_bulges, name, gen, pam):
    if n_clicks is None:
        return '', False, False, None, None
    drop_red = {'border': '3px solid red'}
    #Check if all elements are valid for input
    gen_update = None
    pam_update = None
    drop_update = False             #Create red border only if one of the drop is None or ''
    if gen is None or gen is '':
        gen_update = drop_red
        drop_update = True      
    if pam is None or pam is '':
        pam_update = drop_red
        drop_update = True
    if name is None or name is '' or max_bulges is None or drop_update:        #max bulges is none when not set or is not a number
        return '', True, True, gen_update, pam_update
         
    
    subprocess.call(["ls", "-l"])
    subprocess.call(["sleep", "5s"])            #TODO find better positioning of Loading and loading gif
    return '', False, False, None, None

########################
# Callbacks for search #
########################

#Switch available fields from nonIndex to Index search
@app.callback([Output('max-dna', 'disabled'),
            Output('max-rna', 'disabled'),
            Output('available-genomes-search', 'options')],
            [Input('index-search', 'on')]
            )
def switchSearch(on):
    if on:
        onlydir = [f for f in listdir('genome_library') if isdir(join('genome_library', f))]    #select Indexed genomes
        gen_dir = []
        for dir in onlydir:
            gen_dir.append({'label': dir, 'value' : dir})

        return False, False, gen_dir
    
    onlydir = [f for f in listdir('Genomes') if isdir(join('Genomes', f))]
    gen_dir = []
    for dir in onlydir:
        gen_dir.append({'label': dir, 'value' : dir})
    return True, True, gen_dir

#Switch directory availability for Score 
@app.callback(Output('scores-available-genomes-search', 'disabled'),
            [Input('score-switch', 'on')]
            )
def switchScore(on):
    if on: 
        return False
    return True

#Execute Search
@app.callback([Output('executing-search-genome', 'children'),
            Output('name-result-file', 'required'),
            Output('max-mms', 'required'),
            Output('max-dna', 'required'),
            Output('max-rna', 'required')],
            [Input('submit-search-genome', 'n_clicks')],
            [State('index-search', 'on'),
            State('available-genomes-search', 'value'),
            State('available-pams-search', 'value'),
            State('available-guides-search', 'value'),
            State('name-result-file', 'value'),
            State('max-mms', 'value'),
            State('max-dna', 'value'),
            State('max-rna', 'value'),
            State('result-checklist', 'value'),
            State('score-switch', 'on'),
            State('scores-available-genomes-search', 'value')]
            )
def executeSearch(n_clicks, index, genome, pam, guide, res_name, mm, dna, rna, res_type, score, genome_score):
    if n_clicks is None:
        raise PreventUpdate
    
    
    #Check if elements are valid
    if genome is None or genome is '' or pam is None or pam is '' or guide is None or guide is '':
        raise PreventUpdate        #TODO find better way to signal to provide a value from both dropdown list
    if res_name is None or res_name is '' or mm is None or (index and (dna is None or rna is None)):
        return '', True, True, True, True
    if not res_type:
        raise PreventUpdate         #TODO find better way to signal, maybe modify execute search genome?
    if score and (genome_score is None or genome_score is ''):
        return 'Error, no directory for scores selected', True, True, True, True   #TODO found a way

    if index:
        subprocess.call(["sleep", "5s"])
        return '', False, False, False, False
    
    subprocess.call(["sleep", "5s"])
    return '', False, False, False, False

##########################
# Callbacks for Annotate #
##########################

#Show the uploaded filename
@app.callback(Output('name-upload-file-annotation', 'children'),
            [Input('upload-path-annotation', 'filename')]
            )
def showFileName(name):
    if name is None:
        return ''
    return 'Uploaded ' + name

#Read the uploaded file and converts into bit
def parse_contents(contents):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    return decoded

#Execute Annotation
@app.callback([Output('executing-annotate-result', 'children'),
            Output('div-available-guides-annotation', 'style'),
            Output('div-available-results-annotation', 'style'),
            Output('name-result-file-annotated', 'required')],
            [Input('submit-annotate-result', 'n_clicks')],
            [State('available-guides-annotation', 'value'),
            State('available-results-annotation', 'value'),
            State('name-result-file-annotated', 'value'),
            State('upload-path-annotation', 'contents')]
            )
def executeAnnotation(n_clicks, guide, result_target, result_name, file_content):
    if n_clicks is None:
        raise PreventUpdate
    
    #Check if elements are valid
    drop_red = {'border': '3px solid red'}
    guide_update = None
    res_update = None
    drop_update = False
    if guide is None or guide is '':
        guide_update = drop_red
        drop_update = True      
    if result_target is None or result_target is '':
        res_update = drop_red
        drop_update = True
    #TODO insert same thing for button and update the outputs
    
    if result_name is None or result_name is '' or file_content is None or (drop_update):
        return '', guide_update, res_update, True
    
    paths = parse_contents(file_content).decode('utf-8')
    file_tmp = open('test.txt', 'w')  #TODO choose better name for when multiple users
    file_tmp.write(paths)       #use file_tmp as input for the bash call

    #Note that we need the targets.txt file inside the result_target directory
    subprocess.call(["sleep", "5s"])
    return '', None, None, False

#################################
# Callbacks for Generate Report #
#################################

#TODO creare funzione che quando scelgo il Result controllo subito che cisiano tutti i file e nel caso li faccio vedere?

#Execute Generate Report
@app.callback([Output('executing-generate-report', 'value'),
            Output('guide-sequence-report', 'required'),
            Output('max-mms-report', 'required'),
            Output('available-results-report', 'style')],
            [Input('submit-generate-report', 'n_clicks')],
            [State('guide-sequence-report', 'value'),
            State('max-mms-report', 'value'),
            State('available-results-report', 'value')]
)
def executeReport(n_clicks, sequence, mms, result_file):
    if n_clicks is None:
        raise PreventUpdate
    #TODO continuare la funzione
    raise PreventUpdate

#############################
# Callbacks for Show Report #
#############################

#Perform expensive loading of a dataframe and save result into 'global store'
#Cache are in the Cache directory
@cache.memoize()
def global_store(value):
    
    target = [f for f in listdir('Results/' + value) if isfile(join('Results/'+value, f)) and f.endswith('scores.txt') ]
    if not target:
        target = [f for f in listdir('Results/' + value) if isfile(join('Results/'+value, f)) and f.endswith('targets.txt') ]
    
    df = pd.read_csv('Results/' +value + '/' + target[0], sep = '\t')
    df.rename(columns = {"#Bulge type":'BulgeType', '#Bulge_type':'BulgeType','Bulge Size': 'BulgeSize', 'Bulge_Size': 'BulgeSize', 'Doench 2016':'Doench2016','Doench_2016':'Doench2016'}, inplace = True)
    return df

#Signal the loading is done and reset page_current and sorting_filter
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

#Given the selected result, save the list of available images in that directory
@app.callback(
    [Output('intermediate-value', 'children'),
    Output('test-button', 'n_clicks')],
    [Input('available-results-view', 'value')]
)
def loadImgList(value):
    if value is None or value is '':
        raise PreventUpdate
    
    onlyimg = [f for f in listdir('Results/' + value) if isfile(join('Results/' + value, f)) and f.endswith('.png')]
    json_str = json.dumps(onlyimg) 
    return json_str, 0                  #Returning the n_clicks is needed to 'trick' the system to press the Next button, thus loading an image

#When result is chosen, or when Next button is pressed, load the img list and go to next image
@app.callback(
    [Output('selected-img','src'),
    Output('filename-show', 'children')],
    [Input('intermediate-value', 'children'),
    Input('test-button', 'n_clicks')],
    [State('available-results-view', 'value')]
)
def showImg(json_data, n_clicks, value):
    if json_data is None or json_data is '' or n_clicks is None:
        raise PreventUpdate

    img_list = json.loads(json_data)

    img_pos = 0
    if n_clicks > 0 :
        img_pos = n_clicks%len(img_list)
    image_filename = 'Results/' + value + '/' + img_list[img_pos]
    encoded_image = base64.b64encode(open(image_filename, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded_image.decode()), 'Selected image: ' + image_filename.split('/')[-1] 

if __name__ == '__main__':
    app.run_server(debug=True)
    cache.clear()       #delete cache when server is closed
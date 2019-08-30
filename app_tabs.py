import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.exceptions import PreventUpdate
from os import listdir #for getting directories
from os.path import isfile, isdir,join #for getting directories
import subprocess

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True       #necessary if update element in a callback generated in another callback
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

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
    ]),
    html.Div(id='tab-content')
])


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
        final_list.append(dcc.Dropdown(options = gen_dir, clearable = False, id = "available-genomes"))

        #Dropdown available PAM
        onlyfile = [f for f in listdir('pam') if isfile(join('pam', f))]
        pam_file = []
        for pam_name in onlyfile:
            pam_file.append({'label': pam_name, 'value' : pam_name})
        final_list.append(html.P(["Select an available PAM ", html.Sup(html.Abbr("\u003F", title="To add or remove elements from this list, simply move (remove) your PAM text file into the pam directory"))]))
        final_list.append(dcc.Dropdown(options = pam_file, clearable = False, id = "available-pams"))

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
        final_list.append(daq.BooleanSwitch(on = False, label = "use Index Search", labelPosition = "top", id = 'index-search')) #TODO sistemare posizione del bottone

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
        final_list.append(dcc.Dropdown(options = pam_file, clearable = False, id = "available-pams-search"))

        #Dropdown/File select guide file
        #TODO  do

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
                className = "flex-container"
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
                [daq.BooleanSwitch(on = False, label = "calculate Scores", labelPosition = "top", id = 'score-switch'),          #TODO sistemare posizione del bottone
                dcc.Dropdown(options = gen_dir, clearable = False, id = "scores-available-genomes-search")
                ],
                id = 'container-scores',
                className = "flex-container"
            )
        )

        #Submit job
        final_list.append(html.Button('Submit', id='submit-search-genome'))
        final_list.append(html.Div(id = "executing-search-genome"))
        return final_list
    elif tab == 'annotate-results':
        return 'annotate'
    elif tab == 'generate-report':
        return 'gen rep'

##########################
# Callbacks for Indexing #
##########################

#Execute Indexing of a genome
@app.callback([Output("executing-index-genome", "children"),
            Output('name-genome', 'required'),
            Output('max-bulges', 'required')],
            [Input('submit-index-genome', 'n_clicks')],
            [State('max-bulges', 'value'),
            State('name-genome', 'value'),
            State('available-genomes', 'value'),
            State('available-pams', 'value')])
def executeIndex(n_clicks, max_bulges, name, gen, pam):
    if n_clicks is None:
        return '', False, False
    
    #Check if all elements are valid for input
    if name is None or name is '' or max_bulges is None:        #max bulges is none when not set or is not a number
        return '', True, True
    if gen is None or gen is '':
        return PreventUpdate        #TODO find better way to signal to provide a value from both dropdown list
    if pam is None or pam is '':
        return PreventUpdate        #TODO find better way to signal to provide a value from both dropdown list
    
    subprocess.call(["ls", "-l"])
    subprocess.call(["sleep", "5s"])            #TODO find better positioning of Loading and loading gif
    return '', False, False

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
            #State( guide file),
            State('name-result-file', 'value'),
            State('max-mms', 'value'),
            State('max-dna', 'value'),
            State('max-rna', 'value'),
            State('result-checklist', 'value'),
            State('score-switch', 'on'),
            State('scores-available-genomes-search', 'value')]
            )
def executeSearch(n_clicks, index, genome, pam, res_name, mm, dna, rna, res_type, score, genome_score):
    if n_clicks is None:
        raise PreventUpdate
    
    if index:           #Search with index parameters
        raise PreventUpdate
    else:               #Search without index parameters
        #Check if elements are valid
        if genome is None or genome is '' or pam is None or pam is '':
            raise PreventUpdate        #TODO find better way to signal to provide a value from both dropdown list
        if res_name is None or res_name is '' or mm is None:
            return '', True, True, True, True
        if not res_type:
            raise PreventUpdate         #TODO find better way to signal, maybe modify execute search genome?
        if score and (genome_score is None or genome_score is ''):
            return 'Error, no directory for scores selected', True, True, True, True   #TODO found a way

        subprocess.call(["sleep", "5s"])
        return '', False, False, False, False
if __name__ == '__main__':
    app.run_server(debug=True)
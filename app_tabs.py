import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
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

        #Genome name
        final_list.append(html.P('Tool to find the candidate targets in a genome starting from a PAM. The ouput is a set of files, containing all the sequences of candidate targets extracted from the genome.'))
        final_list.extend([html.Label('Insert the name for the Genome'), dcc.Input(id = 'name-genome', placeholder='Example: hg19_ref', type='text')])

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



        final_list.extend([html.Label('Insert # of max allowed bulges'), dcc.Input(id = 'max-bulges', placeholder='Example: 2', type='number', min = 0)])
        final_list.append(html.P())
        final_list.append(html.Button('Submit', id='submit-index-genome'))
        final_list.append(html.Div(id = "executing-index-genome"))
        return final_list
    elif tab == 'search':
        return 'search'
    elif tab == 'annotate-results':
        return 'annotate'
    elif tab == 'generate-report':
        return 'gen rep'

#Eseguo il programma
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
    subprocess.call(["sleep", "5s"])
    return '', False, False


if __name__ == '__main__':
    app.run_server(debug=True)
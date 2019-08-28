import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import subprocess

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True       #necessary if update element in a callback generated in another callback
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
        final_list.extend([html.Label('Insert the name for the Genome'), dcc.Input(id = 'name-genome', placeholder='Example: hg19_ref', type='text')])
        final_list.extend([html.Label('Insert # of max allowed bulges'), dcc.Input(id = 'max-bulges', placeholder='Example: 2', type='number', min = 0)])
        final_list.append(html.P())
        final_list.append(html.Button('Submit', id='submit-index-genome'))
        final_list.append(html.Div(id = "executing-index-genome"))
        final_list.append(html.Div(id = "executing2-index-genome"))

        return final_list
    elif tab == 'search':
        return 'search'
    elif tab == 'annotate-results':
        return 'annotate'
    elif tab == 'generate-report':
        return 'gen rep'

#Eseguo il programma
@app.callback(Output('executing-index-genome', 'children'),
            [Input('submit-index-genome', 'n_clicks')],
            [State('max-bulges', 'value')])
def executeIndex(n_clicks, max_bulges):
    if n_clicks is None:
        return ''
    subprocess.call(["sleep", "10s"])
    return max_bulges

#Creo overlay
@app.callback(Output('executing2-index-genome', 'children'),
            [Input('submit-index-genome', 'n_clicks')],
            [State('max-bulges', 'value')])
def executeOverlayIndex(n_clicks, max_bulges):
    #subprocess.call(["sleep", "10s"])
    if max_bulges is None:
        return 'none'
    return max_bulges+10


if __name__ == '__main__':
    app.run_server(debug=True)
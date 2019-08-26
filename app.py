import dash
import dash_core_components as dcc
import dash_html_components as html

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='CRISPRitz Web Application'),

    html.Div(children='''
        Description of CRISPRitz.


        Select one from:
    '''),
    html.Div([
        html.Button('Enrich Genome', id='enrich'),
        html.Div(id='output-container-button',
                children='Enter a value and press submit')
    ]),
    html.Div([
        html.Button('Generate Tree', id='gen_tree'),
        
    ]),
   
])


@app.callback(
    dash.dependencies.Output('output-container-button', 'children'),
    [dash.dependencies.Input('enrich', 'n_clicks')],
def update_output(n_clicks):
    return 'The button has been clicked {} times'.format(
        n_clicks
    )


if __name__ == '__main__':
    app.run_server(debug=True)
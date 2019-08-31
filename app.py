import dash
import dash_core_components as dcc
import dash_html_components as html

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='CRISPRitz Web Application'),

    html.Div(children='''
        CRISPRitz is a software package containing 5 different tools dedicated to perform predictive analysis and result assessement on CRISPR/Cas experiments. 
    '''),
    html.Div([
        html.Button('Enrich Genome', id='enrich', style={"background-color":"orange"}, title = "test title"),
        html.Div(id='output-container-button',
                children='Enter a value and press submit')
    ]),
    html.Table([
        html.Tr([html.Td(['Input']), html.Td(['Tool']), html.Td(['Output'])]),
        html.Tr([
            html.Td([html.P('Reference Genome'),html.P('Variants')]), 
            html.Td([html.Button('Add-variants', id='add-var', style={"background-color":"orange", "color":"white"})]), 
            html.Td(['Reference genome with variants'])
            ]),
        html.Tr([
            html.Td([html.P('Reference Genome'), html.P('or Reference Genome with Variants'),html.P('PAM')]),
            html.Td([html.Button('Index-genome', id='index-genome', style={"background-color":"grey", "color":"white"})]),
            html.Td(['Reference Genome Index'])
        ]),
        html.Tr([
            html.Td([html.P('Reference Genome Index'), html.P('or reference Genome'), html.P('or Reference Genome with Variants'), html.P('PAM'),
                html.P('sgRNA sequence(s)'), html.P('# Mismatches'), html.P('# DNA/RNA bulges')]),
            html.Td([html.Button('Search', id='Search', style={"background-color":"#ffcc00", "color":"white"})]),
            html.Td([html.P('List of targets and off-targets with genomic coordinates'), html.P('Overall mismatch and bulge profile')])
        ]),
        html.Tr([
            html.Td([html.P('sgRNA sequence(s)'), html.P('List of targets and off-targets with genomic coordinates')]),
            html.Td([html.Button('Annotate-results', id='annotate-results', style={"background-color":"blue", "color":"white"})]),
            html.Td([html.P('Count in each functional annotation'), html.P('Annotated List of targets and off-targets with genomic coordinates')])
        ]),
        html.Tr([
            html.Td([html.P('sgRNA sequence'), html.P('# Mismatches'), html.P('Overall mismatch and bulge profile'), html.P('Count in each functional annotation'), html.P('Summary counts [optional, 2 required]')]),
            html.Td([html.Button('Generate-report', id='generate-report', style={"background-color":"green", "color":"white"})]),
            html.Td([html.P('Detailed graphical report for each sgRNA'), html.P('Barplot with percentage increasing  from Variant/Reference Genome')])
        ])

    ], style = {"margin-left":"auto", "margin-right":"auto"})
   
])

#test git
@app.callback(
    dash.dependencies.Output('output-container-button', 'children'),
    [dash.dependencies.Input('enrich', 'n_clicks')])
def update_output(n_clicks ):
    if n_clicks is None:
        return 'Enter value'
    return 'The button has been clicked {} times'.format(
        n_clicks
    )


if __name__ == '__main__':
    app.run_server(debug=True)
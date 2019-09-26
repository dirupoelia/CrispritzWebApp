# import dash
# import dash_html_components as html
# import flask

# app = flask.Flask(__name__)
# dash_app = dash.Dash(__name__, server = app, url_base_pathname = '/')

# dash_app.css.append_css({"external_url" : "https://codepen.io/chriddyp/pen/bWLwgP.css"})

# colors = {
#     'background' : '#111111',
#     'text' : '#7FDBFF'
# }


# dash_app.layout = html.Div(
#     [
#         html.Div(
#             [
#                 html.H1(
#                     "My Dashboard",
#                     style={
#                         'text-align':'center',
#                     }
#                 ),
#             ],
#         )
#     ],
# )


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', debug=True, port=80)

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
server = Flask(__name__)
server.secret_key ='test'
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Input(id='my-id', value='initial value', type='text'),
    html.Div(id='my-div')
])


@app.callback(
    Output(component_id='my-div', component_property='children'),
    [Input(component_id='my-id', component_property='value')]
)
def update_output_div(input_value):
    return 'You\'ve entered "{}"'.format(input_value)


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=80)
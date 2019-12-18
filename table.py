import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dash_table.DataTable(
        data= [ {'OS':'Linux', 'V': 'vvvvv', 'Ch': 'chromeVersion' , 'S':'safariVersion', 'ME':'n/a' ,'F':'FirefoxVersion','O':'OperaVersion'},
                {'OS':'MacOS', 'V': 'Mojave', 'Ch': ' 79.0' , 'S':'13.0.4' , 'ME':'n/a' , 'F':'71.0' , 'O':'65.0'},
                {'OS':'Windows', 'V': 'vvvvv', 'Ch': 'chromeVersion' , 'S':'safariVersion' ,'ME':'MicrosoftEdgeVersion','F':'FirefoxVersion','O':'OperaVersion'}],

        columns=[{'id': 'OS', 'name': 'Operative System'}, {'id': 'V', 'name': 'Version'}, {'id': 'Ch', 'name': 'Chrome'},
                 {'id': 'S', 'name': 'Safari'}, {'id': 'ME', 'name': 'Microsoft Edge'}, {'id': 'F', 'name': 'Firefox'},
                 {'id': 'O', 'name': 'Opera'}],

        style_cell={
        'textAlign':'center',
        'width':'20'
    },

        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
    }
)
],   style = {'display': 'inline-block', 'width': '48%'})

if __name__ == '__main__':
    app.run_server(debug=True)

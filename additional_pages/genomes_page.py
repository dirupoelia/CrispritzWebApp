#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 17:05:06 2020

@author: francesco
"""

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import base64                               #for decoding upload content
import io                                   #for decoding upload content
import sys, os
#print(os.path.abspath(os.path.join('..', '../CrispritzWebApp-OFFLINE/GUI')))
#sys.path.append(os.path.abspath(os.path.join('..', '../CrispritzWebApp-OFFLINE/GUI')))

"""
html.Div([html.H3("Search bar"),
                      dcc.Dropdown(id='search-genomes-dropdown',
                                   options=[{"label":"Reference Genome", "value":"Reference Genome"},
                                            {"label":"Name Enriched","value":"Name Enriched"}, 
                                            {"label":"PAM","value":"PAM"}, 
                                            {"label":"Annotation","value":"Annotation"}, 
                                            {"label":"Sample List","value":"Sample List"},
                                            {"label":"# Bulges","value":"# Bulges"}],
                                   value = "Reference Genome",
                                   clearable=False
                                )
                ], style={'width': '40%', 'display': 'inline-block', 'vertical-align': 'left'}
                ),
            html.Div([html.H3(" "),
                      html.Button("Search",id="search-genomes-button")
                      ], style={'width': '10%', 'display': 'inline-block', 'vertical-align': 'middle'}
                 )
"""



def genomesPage(pathDir):
    from .get_genomes import get_genomes
    genomes = get_genomes(pathDir)
    final_list = []
    final_list.append(
        html.Div([  html.H4("Search bar"),
                    html.Div([dcc.Dropdown(id='search-genomes-dropdown',
                                 options=[{"label":"Reference Genome", "value":"Reference Genome"},
                                          {"label":"Name Enriched","value":"Name Enriched"}, 
                                          {"label":"PAM","value":"PAM"}, 
                                          {"label":"Annotation","value":"Annotation"}, 
                                          {"label":"Sample List","value":"Sample List"},
                                          {"label":"# Bulges","value":"# Bulges"}],
                                 value = "Reference Genome",
                                 clearable=False,
                                 style={'display':'inline-block', "width":"400px"}
                                 ),
                                dcc.Input(id="search-genomes-input"),
                                html.Button("Search",id="search-genomes-button"),
                                html.Button("Reset",id="search-genomes-reset")
                            ], style={"columnCount":4}
                         )
            ], style = {'display':'none'}
        )
    )
    final_list.append(
        html.Div([
            html.H3('Genomes'),
            html.P('List of available Reference and Enriched Genomes. For each Genome, the available indexed PAM is shown, along with the maximum searchable number of bulges (PAM and #Bulges columns). The annotation and samples ID files are also shown.'),
            # html.P('Select a row, and click on the \"Change Annotations\" button to update or replace the annotation file for the desired Genome.'),
            dash_table.DataTable(
                id = "genomes-table",
                columns = [{"name": i, "id": i} for i in genomes.columns],
                data=genomes.to_dict('records'),
                row_selectable="single",
                selected_rows=[],
                page_current= 0,
                page_size= 10,
                page_action='custom',

                filter_action='custom',
                filter_query='',

                sort_action='custom',
                sort_mode='multi',
                sort_by=[]
                )
            ])
        )
    final_list.append(
        html.Div([
            html.Br(),
            html.H4('Change annotations'),
            html.P('Select a row on the above table, provide a new Annotation file and update or replace the Annotation file for the desired Genome.')
        ])
        )

    final_list.append(
        html.Div(
            html.Div(
                [
                    html.Div(
                        dbc.Row([
                            dbc.Col(
                                [
                                    html.Button('Choose a new Annotation File', id = 'button-choose-new-annotation'),
                                    
                                    html.P('Selected: None', id = 'label-new-annotation-selected'),
                                    dbc.Tooltip('Full Path: None', placement = 'bottom-start', target = 'label-new-annotation-selected',id = 'tooltip-label-new-annotation-selected' )
                                    
                                ]
                            ),
                            dbc.Col(
                                # html.P('Selected: None', id = 'label-new-annotation-selected')
                                dcc.RadioItems(
                                options=[
                                    {'label': ' Overwrite previous file', 'value': 'replace'},
                                    {'label': ' Extend previous file', 'value': 'update'}
                                ],
                                id='radioitems-new-annotation'
                            )  
                            )
                        ]),
                        style = {'width':'50%'}
                    ),
                    html.Br(),
                    dbc.Row([
                        dbc.Col(
                            # dcc.RadioItems(
                            #     options=[
                            #         {'label': ' Overwrite previous file', 'value': 'replace'},
                            #         {'label': ' Extend previous file', 'value': 'update'}
                            #     ],
                            # )  
                        )
                    ]),
                    # html.Br()
                ],
                # style = {'display':'inline-block'}
            ), 
            # style = {'text-align':'center'}
        )
    )
    # final_list.append(
    #     html.Div([
    #             html.Div([
    #                 html.Button("Change annotations", id = 'change-ann'), 
    #                 html.Br(),
    #                 html.Div( id = 'ann-job')
    #             ])
    #         ])
    #     )
    final_list.append(
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(html.Button("Change annotations", id = 'change-ann')),
                        dbc.Col(html.Div( id = 'ann-job'))
                    ]
                )
            ],
            style = {'width':'50%'}
        )
    )

    page = html.Div(final_list, style = {'margin':'1%'})
    return page
    

if __name__ == '__main__':
    #app.run_server(debug=True)
    sys.path.append(os.path.abspath(os.path.join('..', '../CrispritzWebApp-OFFLINE/')))

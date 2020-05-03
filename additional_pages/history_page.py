#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 18:59:01 2020

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
from os import listdir
from os.path import isfile, isdir,join      #for getting directories
import pandas as pd

def get_results():
    current_working_directory = os.getcwd() + '/'       #Get directory where 'Results' is located
    results_dirs = [f for f in listdir(current_working_directory + '/Results/') if isdir(join(current_working_directory + '/Results/', f)) and isfile(current_working_directory + '/Results/' + f + '/Params.txt')]
    col = 'Job\tGenSe\tGenId\tMM\tDNA\tRNA\tPAM\tGuide\tGecko\tComp'.split('\t')
    a = pd.DataFrame(columns = col)
    for job in results_dirs:
        if os.path.exists(current_working_directory + '/Results/' + job + '/Params.txt'):
            with open(current_working_directory  + '/Results/' + job + '/Params.txt') as p:
                all_params = p.read()
                mms = (next(s for s in all_params.split('\n') if 'Mismatches' in s)).split('\t')[-1]
                genome_selected = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
                with open(current_working_directory  + '/Results/' + job + '/log.txt') as lo:
                    all_log = lo.read()
                job_start = (next(s for s in all_log.split('\n') if 'Job\tStart' in s)).split('\t')[-1]
                if '+' in genome_selected:
                    genome_selected = genome_selected.split('+')[0] + '+'
                dna = (next(s for s in all_params.split('\n') if 'DNA' in s)).split('\t')[-1]
                rna = (next(s for s in all_params.split('\n') if 'RNA' in s)).split('\t')[-1]
                genome_idx = (next(s for s in all_params.split('\n') if 'Genome_idx' in s)).split('\t')[-1]
                if genome_idx != 'None':
                    genome_idx = 'X'
                pam = (next(s for s in all_params.split('\n') if 'Pam' in s)).split('\t')[-1]
                gecko = (next(s for s in all_params.split('\n') if 'Gecko' in s)).split('\t')[-1]
                comparison = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
                if os.path.exists(current_working_directory + '/Results/' + job + '/guides.txt'):
                    with open(current_working_directory  + '/Results/' + job + '/guides.txt') as g:
                        n_guides = str(len(g.read().strip().split('\n')))
                else:
                    n_guides ='n/a'
                a = a.append({'Job':job, 'GenSe':genome_selected, 'GenId':genome_idx, 'MM':mms, 'DNA':dna,
                'RNA':rna, 'PAM':pam,'Guide':n_guides,'Gecko':gecko,'Comp':comparison, 'Start':job_start}, ignore_index = True)
    a = a.sort_values(['MM','DNA','RNA'],ascending = [True, True, True])
    return a

def historyPage():
    current_working_directory = os.getcwd() + '/'       #Get directory where 'Results' is located
    results_dirs = [f for f in listdir(current_working_directory + '/Results/') if isdir(join(current_working_directory + '/Results/', f)) and isfile(current_working_directory + '/Results/' + f + '/Params.txt')]
    results = get_results()
    final_list = []

    final_list.append(
        html.Div(
            [
                html.H3('Available Analysis'),
                html.P('List of available analysis, select a row to load the results.')
            ]
        )
    )

    final_list.append(
        html.Div([
            dash_table.DataTable(
                id = "results-table",
                columns = [{"name": i, "id": i} for i in results.columns],
                data=results.to_dict('records')
                )
            ])
        )
    page = html.Div(final_list, style = {'margin':'1%'})
    return page

@app.callback(
    Output('results-table', 'style_data_conditional'),
    [Input('results-table', 'selected_cells')],
    [State('results-table', 'data')]
) 
def highlightRow(sel_cel, all_guides):
    if sel_cel is None or not sel_cel or not all_guides:
        raise PreventUpdate
    job_name = all_guides[int(sel_cel[0]['row'])]['Job']
    return [
        {
            'if': {
                    'filter_query': '{Job} eq "' + job_name + '"'
                },
                'background-color':'rgba(0, 0, 255,0.15)'
                
            }
    ]

if __name__ == '__main__':
    #app.run_server(debug=True)
    print(historyPage())

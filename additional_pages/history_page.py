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
sys.path.append(os.path.abspath(os.path.join('..', '../CrispritzWebApp-master/')))
import get_results as gt


def historyPage():
    
    results = gt.get_results()
    final_list = []
    final_list.append(
        html.Div([
            html.H3('Results'),
            dash_table.DataTable(
                id = "results-table",
                columns = [{"name": i, "id": i} for i in results.columns],
                data=results.to_dict('records')
                )
            ])
        )
    page = html.Div(final_list, style = {'margin':'1%'})
    return page
    

if __name__ == '__main__':
    #app.run_server(debug=True)
    print(historyPage())

#Perform expensive loading of a dataframe and save result into 'global store'
#Cache are in the Cache directory
@cache.memoize()
def global_store(value):
    
    if value is None:
        return ''
    target = [f for f in listdir('Results/' + value) if isfile(join('Results/'+value, f)) and f.endswith('scores.txt') ]
    if not target:
        target = [f for f in listdir('Results/' + value) if isfile(join('Results/'+value, f)) and f.endswith('targets.txt') ]
    
    df = pd.read_csv('Results/' +value + '/' + target[0], sep = '\t')
    df.rename(columns = {"#Bulge type":'BulgeType', '#Bulge_type':'BulgeType','Bulge Size': 'BulgeSize', 'Bulge_Size': 'BulgeSize', 'Doench 2016':'Doench2016','Doench_2016':'Doench2016'}, inplace = True)
    return df

#Callback to populate the tab, note that it's called when the result_page is loaded (dash implementation), so we do not use raise update to block this first callback
@app.callback(
    [Output('signal','children'),
    Output('result-table','page_current'),
    Output('result-table', "sort_by"), 
    Output('result-table','filter_query')],
    [Input('url', 'pathname')],
    [State('url', 'search')]
)
def populateTable(pathname, search):
    if pathname != '/result':
        raise PreventUpdate

    job_id = search.split('=')[-1]
    job_directory = 'Results/' + job_id + '/'
    if(not isdir(job_directory)):
        return 'not_exists', 0, [], ''
    global_store(job_id)
    return job_id, 0, [], ''

#Send the data when next or prev button is clicked on the result table
@app.callback(
    [Output('result-table', 'data'),
    Output('mms-dropdown','options'),
    Output('warning-div', 'children'),
    Output('general-profile-table', 'columns'),
    Output('general-profile-table', 'data')],
    [Input('signal', 'children'),
     Input('result-table', "page_current"),
     Input('result-table', "page_size"),
     Input('result-table', "sort_by"),
     Input('result-table', 'filter_query'),
     Input('general-profile-table','selected_cells')],
     [State('general-profile-table', 'data'),
     State('url', 'search')]
)
def update_table(value, page_current,page_size, sort_by, filter, sel_cel, all_guides, search):
    #print('signal_children', value)
    print('sel_cel', sel_cel)
    if value is None:
        raise PreventUpdate
    if value == 'not_exists':
        return [], [] , dbc.Alert("The selected result does not exist", color = "danger"), [], []

    #Load mismatches
    with open('Results/' + value + '/Params.txt') as p:
       mms = (next(s for s in p.read().split('\n') if 'Mismatches' in s)).split('\t')[-1]

    mms = int(mms[0])
    mms_values = [{'label':i, 'value':i} for i in range(mms + 1) ]      
    
    col_profile_general = ['Total On-Targets', 'Total Off-Targets']
    for i in range(mms):
        col_profile_general.append(str(i+1) + ' Mismatches')
    col_type = ['numeric' for i in col_profile_general]
        
    filtering_expressions = filter.split(' && ')
    if sel_cel:
        guide = all_guides[int(sel_cel[0]['row'])]['Guide']
        filtering_expressions = ['{crRNA} = ' + guide]      #TODO currently only this filter will be applied when a guide is selected
        df = global_store(value)
        dff = df
        for filter_part in filtering_expressions:
            col_name, operator, filter_value = split_filter_part(filter_part)

            if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
                # these operators match pandas series operator method names
                dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
            elif operator == 'contains':
                dff = dff.loc[dff[col_name].str.contains(filter_value)]
            elif operator == 'datestartswith':
                # this is a simplification of the front-end filtering logic,
                # only works with complete fields in standard format
                dff = dff.loc[dff[col_name].str.startswith(filter_value)]

        if len(sort_by):
            dff = dff.sort_values(
                [col['column_id'] for col in sort_by],
                ascending=[
                    col['direction'] == 'asc'
                    for col in sort_by
                ],
                inplace=False
            )

    #Check if results are not 0
    warning_no_res = ''
    if not sel_cel:
        dff = pd.DataFrame()    #TODO test
    job_id = search.split('=')[-1]
    job_directory = 'Results/' + job_id + '/'
    with open(job_directory + job_id + '.targets.txt') as t:
        no_result = False
        t.readline()
        last_line = t.readline()
        if (last_line is '' or last_line is '\n'):
            no_result = True

    if (no_result):
        warning_no_res = dbc.Alert("No results were found with the given parameters", color = "warning")
    
    #Load profile
    try:
        profile = pd.read_csv('Results/' + value + '/' + value + '.profile_complete.xls')   #NOTE profile_complete has ',' as separator 
    except:
        profile = pd.read_csv('Results/' + value + '/' + value + '.profile.xls', sep = '\t')    #NOTE profile has \t as separator or ','
        if len(profile.columns) == 1:
            profile = pd.read_csv('Results/' + value + '/' + value + '.profile.xls')
    
    columns_profile_table = [{'name':'Guide', 'id' : 'Guide', 'type':'text'}, {'name':'Total On-Targets', 'id' : 'Total On-Targets', 'type':'numeric'}, {'name':'Total Off-targets', 'id' : 'Total Off-Targets', 'type':'numeric'}]
    keep_column = ['GUIDE', 'ONT', 'OFFT']
    for i in range (mms):
        print(i+1)
        columns_profile_table.append({'name': str(i+1) + ' Mismatches', 'id':str(i+1) + ' Mismatches', 'type':'numeric'})
        keep_column.append(str(i+1) + 'MM')

   
    profile = profile[keep_column]
    rename_columns = {'GUIDE':'Guide',"ONT":'Total On-Targets', 'OFFT':'Total Off-Targets'}
    for i in range(mms):
        rename_columns[str(i+1) + 'MM'] = str(i+1) + ' Mismatches'

    profile.rename(columns = rename_columns, inplace = True)    #Now profile is Guide, Total On-targets, ...
     
    return dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records'), mms_values, warning_no_res, columns_profile_table, profile.to_dict('records')

#For filtering
def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


#Read the uploaded file and converts into bit
def parse_contents(contents):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    return decoded

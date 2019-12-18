
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

def helpPage():
    final_list = []
    final_list.append(
        html.Div([
            html.H3('About'),
            html.P([
        'CRISPRme  performs  predictive analysis and result assessment on population and individual specific CRISPR/Cas experiments.' +  
        ' CRISPRme enumerates on- and off-target accounting simultaneously for  substitutions, DNA/RNA bulges and common genetic variants from the 1000 genomes project.'
        ]),
        html.P(['Open this ', html.A('example',href = 'http://crispritz.di.univr.it/result?job=QVFHZMMBRA', target = '_blank') ,' to navigate the results we show in this page'])
    
    ])
        
    )

    final_list.append(html.H3('Main Page'))
   
    final_list.append(
        html.Div([
        html.P(
            ['In the main page of CRISPRme, users can select a wide range of options to personalize their searches. The input phase is divided into three main steps:',
            html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/main_page.png', 'rb').read()).decode()), width="100%", height="auto")]
        ),
        html.Ul(
            [
                html.Li(
                    [
                        'STEP 1: Genome and PAM selection',
                        html.Ul(
                            [
                                html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/helpPage/genome.png', 'rb').read()).decode()), width='30%' ),
                                html.Li('Genome: here you can select a genome from the ones present, some genomes have also the variant version enriched (indicated with a \'+\' symbol) with genetic variant from the 1000genome project'),
                                html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/helpPage/pam.png', 'rb').read()).decode()), width='30%' ),
                                html.Li('PAM: here you can select a Protospacer Adjacent Motif for a specific Cas protein.'),
                            ], style = {'padding': '15px'}
                        )
                    ]
                ),
                html.Li(
                    [
                        'STEP 2: Guide insertion and threshold configuration',
                        html.Ul(
                            [
                                html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/helpPage/guides.PNG', 'rb').read()).decode()), width='40%' ),
                                html.Li('Guides: a list of crRNAs sequences, consisting in 1 or more sequences (max 1000 sequences) to search on the genome'),
                                html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/helpPage/sequence.PNG', 'rb').read()).decode()), width='40%' ),
                                html.Li('Sequence: one or more genetic sequences (max 1000 characters), each sequence MUST BE separated with the header \'>name\'. The sequence can be also submitted with a ' + 
                                'chromosome range, also provided with an header. The region will be extracted from the Genome selected in STEP 1'),
                                html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/helpPage/crRNA.PNG', 'rb').read()).decode()), width='20%' ),
                                html.Li('Allowed mismatches: number of tolerated mismatches in a target'),
                                html.Li('Bulge DNA size: size of bubbles tolerated on the DNA sequence (can be consecutive(AA--AA) or interleaved(AA-A-AA)).'),
                                html.Li('Bulge RNA size: size of bubbles tolerated on the RNA sequence (can be consecutive(AA--AA) or interleaved(AA-A-AA))'),
                                # html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/helpPage/crRNA.PNG', 'rb').read()).decode()), width='20%' ),
                                html.Li('crRNA length: available only when a genetic sequence is given as input, represents the length of the guides (without PAM) that you want to extract from the sequence.')
                            ], style = {'padding': '15px'}
                        )
                    ]
                ),
                html.Li(
                    [
                        'STEP 3 (Advanced options): Select various comparisons',
                        html.Ul(
                            [
                                html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/helpPage/advOpt.PNG', 'rb').read()).decode()), width='40%' ),
                                html.Li('Compare your results with the GeCKO v2 library: selected by default, compares the results of your guides with the results obtained in a previous search with guides from the well-known GeCKO library.'),
                                html.Li('Compare your results with the corresponding reference genome: selected by default when an enriched genome is chosen, compares the results with the respective reference genome to evaluate differences when variant are added.'),
                                html.Li('Notify me by email: if selected, let you insert an email to receive a notification when your job is terminated.'),
                            ], style = {'padding': '15px'}
                        )
                    ]
                )
            ] , style = {'padding': '15px'}
        )
        ])
    )

    final_list.append(
        html.P(
            ['After selecting the desired inputs, click on the Submit button to start the search']
        )
    )

    final_list.append(
        html.Div(
            [
                dbc.Alert(
                    [
                        'WARNING: If some inputs are missing, a warning popup will be displayed', html.P(),
                        html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/helpPage/warning.png', 'rb').read()).decode()), width='100%' ),
                    ],color = 'warning', fade = False, style = {'width':'70%'}
                )
            ]
        )
    )

    final_list.append(
        html.P(
            [
                'After the submission, the status of the search will be displayed in a new page',
                html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/waitPage/loadPage.png', 'rb').read()).decode()), width='100%' ),
                'When the job is complete, the result link will appear at the end of the status report',
                html.P(html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/waitPage/jobDone.png', 'rb').read()).decode()), width='20%' ))
            ]
        )
    )

    final_list.append(html.H3('Result Page'))
    final_list.append(
        html.P(
            [
                'At the top of the page, you find a table with the list of sgRNAs used during the search phase. This table summarizes the results obtained for each input guide.',
                html.P(html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/resultPage/resultsSummary.PNG', 'rb').read()).decode()), width='100%' )),
                html.Ul(
                    [
                        html.Li('CFD: Off-Target Cutting Frequency Determination Score, calculates how much is the affinity of the guides with the off-targets, basically tells you the likelihood of the guide to perform cut in off-target regions.'),
                        html.Li('Doench 2016: On-Target Efficacy Scoring (Azimuth 2.0), it’s a trained machine learning model that gives you the likelihood of on-target activity for the selected guide.'),
                        html.Li('Total On-Targets: shows how many possible On-Targets the guide can have.'),
                        html.Li('Total Off-Targets: shows how many possible Off-Targets the guide can have.'),
                        html.Li('Targets for 0-n mismatches: shows how many possible Off-Targets the guide can have, but grouped by mismatch count.'),
                    ], style = {'padding': '15px'}
                ),
                'In the middle of the page there are four tabs:',
                html.Ul(
                    [
                        html.Li([html.Span('Summary by Guide: ', style = {'color':'red'}) ,'This table collects all the possible On-/Off- Targets grouped by mismatch/bulge couples.']),
                        html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/resultPage/summaryByGuide.PNG', 'rb').read()).decode()), width='100%' ),
                        html.Ul(
                            [
                                html.Li('Bulge Type: type of bulge of the targets, can be X (no bulge), DNA or RNA'),
                                html.Li('Bulge Size: size of the bulge present in the targets'),
                                html.Li('Mismatches: number of mismatches present in the targets'),
                                html.Li('Number of Targets: number of non-unique (also found in reference genome) targets found in that combination mismatch/bulge'),
                                html.Li('Target Created by SNPs: number of unique targets (found only in variant genome) found in that combination mismatch/bulge'),
                                html.Li('PAM Disruption: number of possible disrupted PAMs due to variants addition'),
                                html.Li('PAM Creation: number of possible created PAMs due to variants addition'),
                                html.Li('Show Targets: open a new page to display all the targets of the row of interest')
                            ]
                        ),
                        html.Li([html.Span('Summary by Sample: ', style = {'color':'red'}),'This table collects all the possible On-/Off- Targets grouped by sample name.']),
                        html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/resultPage/summaryBySamples.PNG', 'rb').read()).decode()), width='100%' ),
                        html.Ul(
                            [
                                html.Li('Population: population which the sample belong to'),
                                html.Li('Super Population: continent which the sample belong to'),
                                html.Li('Targets in Sample: number of unique targets (found only in variant genome) generated by that sample'),
                                html.Li('Total Targets in Population: number of unique targets (found only in variant genome) generated by all the sample of the population'),
                                html.Li('Total Targets in Super Population: number of unique targets (found only in variant genome) generated by all the populations'),
                                html.Li('PAM Disruption: number of possible disrupted PAMs due to variants addition'),
                                html.Li('PAM Creation: number of possible created PAMs due to variants addition'),
                                html.Li('Show Targets: open a new page to display all the targets of the row of interest')
                            ]
                        ),
                        html.Li([html.Span('Summary by Position: ', style = {'color':'red'}),'This table collects all the possible On-/Off- Targets grouped by position in the genome (composed by chromosome and relative position)']),
                        html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/resultPage/summaryByPosition.PNG', 'rb').read()).decode()), width='100%' ),
                        html.Ul(
                            [
                                html.Li('Position: chromosome relative position of the first letter of the guide'),
                                html.Li('Best Target: best target found in that position'),
                                html.Li('Min Mismatch: minimum number of mismatches present in the targets in that position'),
                                html.Li('Min Bulge: minimum number of bulges present in the targets in that position'),
                                html.Li('Bulge: number of bulges present in the targets in that position'),
                                html.Li('Targets in Cluster by Mismatch Value: Matrix showing the distribution of the targets grouped by mismatch/bulge count'),
                            ]

                        ),
                        html.Li([html.Span('Graphical Report: ', style = {'color':'red'}),'This page shows graphics about a specific guide, including genomic annotation and motif logos. The main feature introduced is the possibility to visualize graphical reports at individual level.']),
                        html.Img(src = 'data:image/png;base64,{}'.format(base64.b64encode(open('assets/resultPage/summaryByGraphicaGecko.png', 'rb').read()).decode()), width='100%' ),
                        html.Ul(
                            [
                                html.Li('Select a Mismatch Value: generate graphics with the specified mismatch value'),
                                html.Li('Select Individual Data: generate individual data, by selecting Super Population, Population and Sample')
                            ]
                        )
                    ], style = {'padding': '15px'}
                )

            ]
        )
    )

    final_list
    page = html.Div(final_list, style = {'margin':'1%'})
    return page
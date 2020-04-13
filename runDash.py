
import os,json, locale, requests
import dash, dash_table, dash_auth
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from os import listdir
import plotly.figure_factory as ff
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from datetime import date,datetime,timedelta,time

try:

    with open('./configuration/credentials.txt') as json_file:
        creds = json.load(json_file)
except:
    import createjsons
    with open('./configuration/credentials.txt') as json_file:
        creds = json.load(json_file)

USERNAMES = {creds.get('Username for Dash'): creds.get('Password for Dash')}

locale = locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')


 

def refresh_data():
    global data
    from getdata import jsonallcards, jsonallepics, jsonimportantcards,jsoncategories, alldates, jsonepics, jsoncards, jsonmeta, jsonnietingepland, jsonstatuses, jsonuren
    data = {'allcards': jsonallcards, 'allepics': jsonallepics, 'belangrijkekaarten': jsonimportantcards, 'categories': jsoncategories, 'dates': alldates, 'epics': jsonepics, 'kaarten': jsoncards, 'meta': jsonmeta, 'nietingepland': jsonnietingepland, 'statuses': jsonstatuses, 'uren': jsonuren}
    data['refreshed'] = {'daterefreshed': datetime.strftime(datetime.now(),'%A %-d %B, %H:%M'), 'dateofdata': datetime.now()}
    create_graphdata()

def create_graphdata():
    global graphdata
    graphdata = {}
    datesofcards = []
    for i,j in data['kaarten'].items():
        datesofcards.append(datetime.strptime(j['created'][6:], '%Y-%m-%d, %H:%M:%S'))
    graphdata['meta'] = {'eerstedatum': min(datesofcards).date(),'huidigedatum': datetime.now().date()}
    planneddates = {'startingdates': [], 'endingdates': []}
    for i,j in data['kaarten'].items():
        try:
            planneddates['startingdates'].append(datetime.strptime(j['Begindatum'][6:], '%Y-%m-%d, %H:%M:%S'))
        except:
            pass 
        try:
            planneddates['endingdates'].append(datetime.strptime(j['Einddatum'][6:], '%Y-%m-%d, %H:%M:%S'))
        except:
            pass 
    graphdata['meta']['firstdateplanned'] = min(planneddates['startingdates']).date()
    graphdata['meta']['lastdateplanned'] = max(planneddates['endingdates']).date()

    layoutforstackedbars = go.Layout(barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    barsfornietingepland = []
    for i,j in data['nietingepland']['data'].items():
            barsfornietingepland.append(dict(x=data['nietingepland']['labels'],
                        y=data['nietingepland']['data'].get(i),
                        name=i,
                        type='bar',
                        opacity='0.6'
                        ))
                        
    optionsstatusesurenpermaand=[] 
    for name in data['statuses']:
        optionsstatusesurenpermaand.append({'label':name, 'value':name})   
    doingdatatable = []
    for i,j in data['kaarten'].items():
            try:
                start = datetime.strptime(j['Begindatum'][6:16], '%Y-%m-%d').date()
            except:
                start = None
            try:
                stop = datetime.strptime(j['Einddatum'][6:16], '%Y-%m-%d').date()
            except:
                stop = None
            
            doingdatatable.append({'Kaart': j['name'],
                              'Begindatum': start,
                              'Einddatum': stop,
                              'Epic': j['epic'],
                              'URL': j['shortUrl'],
                              'Categorie': j['Category'],
                              'Hoofdverantwoordelijke': j['Hoofdverantwoordelijke'],
                              'Cognosrapport': j['Cognosrapport'],
                              'Geplande uren': j['Geplande uren'],
                              'Status': j['status'],
                              'Lijst': j['list'],
                              'Gearchiveerd': j['closed']
                             })
    
    graphdata['emptygraph'] = {'data': [go.Pie()],'layout': go.Layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')}
    graphdata['doingdatatable'] = doingdatatable
    graphdata['nietingepland']= {'data': barsfornietingepland, 'layout': layoutforstackedbars}
    graphdata['optionsstatusesurenpermaand'] = optionsstatusesurenpermaand
    

refresh_data()

## Set update interval to refresh data of the dashboard and create a function to update every x seconds
UPDADE_INTERVAL = 5

def get_new_data_every(period=UPDADE_INTERVAL):
    """Update the data every 'period' seconds"""

    while True:
        refresh_data()
        time.sleep(period)

## Create a function that contains the layout
def make_layout():
    refresh_data()
    return html.Div(className='First Div',children=[
        
        html.Div(
            className='Second Div?', 
            children=[
                html.Div(className='Banner',
                    children = [
                        html.Div(
                            className='Banner text', 
                            children=[
                                html.H1('Werkvoorraad'),
                                ],
                            style = {'display': 'inline-block',
                                    'width': '80%'
                            },
                        ), #/banner text
                        html.Div(
                            className='logo', 
                            children=[
                                html.Img(src=app.get_asset_url('logonop.png'), style={'width': '150px','margin-right': '0px'})
                                ],
                            style = {'display': 'inline-block',
                                    'margin-right': '1px'                            
                            }
                        ), #/logo                    
                    ],
                ), #/ banner
                
                
                ],
            style={'font-style': 'italic',
                'font-weight': 'bold',
                'border': '10px', 
                'box-shadow': '8px 8px 8px grey',
                'background': 'rgb(149,193,31)',
                'background': 'linear-gradient(133deg, rgba(62,182,235,1) 0%, rgba(243,253,255,1) 76%, rgba(243,253,255,0) 100%)',
                'margin-top': '1%', 
                'margin-bottom': '1%', 
                'margin-right': '1%', 
                'margin-left': '1%',
                'border-radius': '10px',
                'text-align': 'center'
            }
            ), #/ second div?

        html.Div(
            className='Refreshbutton', 
            children=[
                html.Button(data['refreshed']['daterefreshed'], id='my-button'),

                ],
                style={'margin-bottom': '1%'}
                ), #/ Refreshbutton
        dcc.Tabs(
            className='Tabs', 
            children=[
                dcc.Tab(
                    label='Epics', 
                    children=[
                        html.Div(
                            className='row',
                            children=[
                                html.Div(
                                    className='three columns',
                                    children=[
                                        html.H4('Epics'),
                                        dcc.Markdown('''**Definitie:** Een overstijgend samenhangend geheel van projecten wat als geheel waarde oplevert voor de organisatie.'''),
                                        html.Div([
                                            dash_table.DataTable(
                                                id='duetable',
                                                columns = [{'name': 'Epic', 'id': 'Epic'},{'name': 'Uren','id': 'Uren'}],
                                                data= [{'Epic': j['name'], 'Uren': j['Geplande uren']} for j in data['belangrijkekaarten']['epics'].values()],
                                                style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                                                style_cell = {'backgroundColor': 'grey', 'color': 'white','text-align': 'left'}
                                            )],
                                        style={'margin-bottom': '15px',
                                        'margin-top': '1%', 
                                        'margin-left': '1%',
                                        'margin-right': '1%',
                                        }
                                        ), #/ 
                                    ],
                                    style={'width': '23%', 
                                    'display': 'inline-block', 
                                    'background-color': 'rgba(0,0,0,0)', 
                                    'margin-top': '1%', 
                                    'margin-bottom': '1%', 
                                    'margin-left': '1%',
                                    'margin-right': '1%',
                                    'border-radius': '10px',
                                    'text-align': 'center',
                                    },
                                ), #/ three columns
                        html.Div(
                            className='three columns',
                            children=[
                                html.H4('Geschatte uren'),
                                dcc.Markdown('Gebruik de Dropdown hieronder om de grafiek aan te passen.'),
                                html.Div([
                                    dcc.Dropdown(
                                        id='dropdownepics',
                                        options=[{'label':name, 'value':name} for name in data['epics'].keys()],
                                        multi=True, 
                                        value = [next(iter(data['epics']))]
                                        )
                                    ],
                                    style={'margin-left': '1%',
                                        'margin-right': '1%',
                                        }
                                    ), #/dropdownepics                                    
                                html.Div([
                                    dcc.Graph(id='donutepichours')
                                    ],
                                    style={'margin-bottom': '15px',
                                        'margin-top': '1%', 
                                        'margin-left': '1%',
                                        'margin-right': '1%',
                                        }        
                                    ), #/donutepichours                                       
                            ],    
                                
                            style={'width': '73%', 
                                'display': 'inline-block', 
                                'background-color': 'rgba(62,182,235,0.1)', 
                                'margin-top': '1%', 
                                'margin-bottom': '1%', 
                                'margin-left': '1%',
                                'margin-right': '1%',
                                'text-align': 'center',
                                'border-radius': '10px'
                                },
                            ), #/three columns2
                    ],
                    style={'box-shadow': '8px 8px 8px grey',
                        'background-image': """url('./assets/left.png')""",
                        'background-repeat': 'no-repeat',
                        'background-position': '0px 0px',
                        'margin-top': '1%', 
                        'margin-bottom': '1%', 
                        'margin-right': '1%', 
                        'margin-left': '1%',
                        'border-radius': '10px'
                        }
                    ), #/row

## second div in Epics tab (uren per maand)
                    html.Div([
                        html.Div(
                            className='urenpermaand', 
                            children=[
                                html.H4('Uren per maand'),
                                html.Div(
                                    className='filters', 
                                    children=[
                                        dcc.Markdown('''**Uitleg:** Kies hieronder de epic(s) en de status(sen) die je wil zien. Rechts kun je de verschillende onderdelen aan of uit zetten.'''),
                                        html.Div(
                                            className='dropdownepicsdiv', 
                                            children=[
                                                html.Div([
                                                    dcc.Markdown('**Epic:**'),
                                                ],
                                                style={'display': 'inline-block',
                                                    'margin-left': '1%', 
                                                    'width': '10%'
                                                    }
                                                ), #/dropdownepicsdiv
                                            html.Div([
                                                dcc.Dropdown(
                                                    id='dropdownepicsfortimeline',
                                                    options=[{'label':name, 'value':name} for name in data['epics'].keys()],
                                                    multi=True,
                                                    value = [next(iter(data['epics']))]
                                                ),                               
                                                ],
                                                style={'display': 'inline-block', 
                                                    'margin-right': '1%', 
                                                    'width': '88%'
                                                    }
                                                ),
                                            ],
                                            style={'display': 'inline-block', 
                                                'width': '100%'
                                                }
                                        ),
                                        html.Div(
                                            className='dropdownstatusdiv', 
                                            children=[
                                                html.Div([
                                                    dcc.Markdown('**Status:**'),
                                                ],
                                                style={'display': 'inline-block',
                                                    'margin-left': '1%', 
                                                    'width': '10%'
                                                    }
                                                ), #/dropdownstatusdiv
                                                html.Div([
                                                    dcc.Dropdown(
                                                        id='dropdownstatusfortimeline',
                                                        options=graphdata['optionsstatusesurenpermaand'],
                                                        multi=True,
                                                        searchable=False,
                                                        value = ["Not Started", "Blocked", "Doing", "Done"]
                                                    ),                               
                                                ],
                                                style={'display': 'inline-block', 
                                                    'margin-right': '1%', 
                                                    'width': '88%'
                                                    }
                                                ),
                                            ],
                                            style={'display': 
                                                'inline-block', 
                                                'width': '100%'
                                                }
                                        ),

                                    ],
                                    style={'margin-left': '1%',
                                    }
                                ), #/filters
                            dcc.Graph(id='epicstimeline')
                            ],
                            style={
                                'background-color': 'rgba(62,182,235,0.1)', 
                                'margin-top': '1%', 
                                'margin-bottom': '1%', 
                                'margin-left': '1%',
                                'margin-right': '1%',
                                'border-radius': '10px'                   
                                }          
                        ) #/urenpermaand                
                    ],
                    style={                
                        'box-shadow': '8px 8px 8px grey',
                        'background-image': """url('./assets/left.png')""",
                        'background-repeat': 'no-repeat',
                        'background-position': '0px 0px',
                        'margin-top': '1%', 
                        'margin-bottom': '1%', 
                        'margin-left': '1%',
                        'margin-right': '1%',
                        'text-align': 'center',
                        'border-radius': '10px'                   
                        }
                    ), #/second div in epics tab                

## Third Div in epics tab (GANTT)                
                html.Div([
                    html.Div([
                        html.H4('Gantt chart per epic'),
                        
                        dcc.Markdown('''Onderstaand is een Gantt chart te zien van alle kaarten die aan de gekozen epic(s) gekoppeld zijn. Gebruik de Dropdown hieronder om de epics te kiezen.'''),
                        html.Div([
                            dcc.Dropdown(
                                id='dropdownepicsforgantt',
                                options=[{'label':name, 'value':name} for name in data['epics'].keys()],
                                multi=True,
                                value = [next(iter(data['epics']))]
                            ),
                            ],
                            style={'margin-left': '1%',
                                'margin-right': '1%',
                                'margin-bottom': '1%',
                                }
                        ),
                        dcc.Graph(id='epicgantt'),                    
                        ],
                        style={
                            'background-color': 'rgba(62,182,235,0.1)', 
                            'margin-top': '1%', 
                            'margin-bottom': '1%', 
                            'margin-left': '1%',
                            'margin-right': '1%',
                            'border-radius': '10px'                   
                            }                    
                        ) #/dropdowns for gantt
                    ],
                    style={ 
                        'box-shadow': '8px 8px 8px grey',
                        'background-image': """url('./assets/left.png')""",
                        'background-repeat': 'no-repeat',
                        'background-position': '0px 0px',
                        'margin-top': '1%', 
                        'margin-bottom': '1%', 
                        'margin-left': '1%',
                        'margin-right': '1%',
                        'text-align': 'center',
                        'border-radius': '10px'                   
                        }
                    ),   
### TEST         
                html.Div([
                    html.Div([
                        html.H4('Gantt chart op totaalniveau'),
                        dcc.Markdown('''Onderstaand is een Gantt chart te zien van de gekozen epic(s). Gebruik de Dropdown hieronder om de epics te kiezen.'''),
                        html.Div([
                            dcc.Dropdown(
                                id='dropdownepicsforgantttotal',
                                options=[{'label':name, 'value':name} for name in data['epics'].keys()],
                                multi=True,
                                value = [name for name in data['epics'].keys()]
                            ),
                            ],
                            style={'margin-left': '1%',
                                'margin-right': '1%',
                                'margin-bottom': '1%',
                                }
                        ),
                        dcc.Graph(id='gantttotal'),                    
                        ],
                        style={
                            'background-color': 'rgba(62,182,235,0.1)', 
                            'margin-top': '1%', 
                            'margin-bottom': '1%', 
                            'margin-left': '1%',
                            'margin-right': '1%',
                            'border-radius': '10px'                   
                            }                    
                        ) #/dropdowns for gantt
                    ],
                    style={ 
                        'box-shadow': '8px 8px 8px grey',
                        'background-image': """url('./assets/left.png')""",
                        'background-repeat': 'no-repeat',
                        'background-position': '0px 0px',
                        'margin-top': '1%', 
                        'margin-bottom': '1%', 
                        'margin-left': '1%',
                        'margin-right': '1%',
                        'text-align': 'center',
                        'border-radius': '10px'                   
                        }
                    ), 
## end of test

                ],
                style={'border-style': 'solid',
                    'border-width': '2px',
                    'background': 'rgb(255,255,255)',
                    'background': 'radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(162,162,162,1) 100%, rgba(255,255,255,1) 100%)',
                    'margin-top': '5px', 
                    'margin-bottom': '5px', 
                    'margin-right': '5px', 
                    'margin-left': '5px',
                    'border-radius': '6px'
                    }
            ),#/tab epics
            


            dcc.Tab(label='Urenverdeling',children=[
                html.Div([                   
                    html.Div([html.Div([                        
                        html.H4('Uren per categorie'),
                        dcc.Markdown('Gebruik de Dropdown hieronder om de grafiek aan te passen.'),
                        dcc.Dropdown(
                            id='dropdownhourscat',
                            options=[{'label': 'Per dag', 'value': 'Datum'}, {'label': 'Per maand', 'value': 'periode'}],                            
                            value = 'periode'
                            ),
                        ],
                        style={'margin-left': '1%',
                                'margin-right': '1%',
                                'margin-top': '1%',
                                'margin-bottom': '1%'
                            }                        
                        ),
                        dcc.Graph(id='graph_cat')
                        ],
                        style={
                            'background-color': 'rgba(62,182,235,0.1)', 
                            'margin-top': '1%', 
                            'margin-bottom': '1%', 
                            'margin-left': '1%',
                            'margin-right': '1%',
                            'text-align': 'center',
                            'border-radius': '10px'                   
                            }                        
                    )
                ],
                style={                        
                    'box-shadow': '8px 8px 8px grey',
                    'background-image': """url('./assets/left.png')""",
                    'background-repeat': 'no-repeat',
                    'background-position': '0px 0px',
                    'margin-top': '1%', 
                    'margin-bottom': '1%', 
                    'margin-left': '1%',
                    'margin-right': '1%',
                    'text-align': 'center',
                    'border-radius': '10px'                   
                    }
                ), #/ first div tab Urenverdeling
                html.Div([
                    html.Div([
                        html.Div([                        
                            html.H4('(nog) niet ingeplande uren'),
                            ],
                            style={'margin-left': '1%',
                                'margin-right': '1%',
                                'margin-top': '1%',
                                'margin-bottom': '1%'
                                }
                            ),                        
                        dcc.Graph(
                            id='graph_nietingepland',
                            figure={'data': graphdata['nietingepland']['data'], 'layout': graphdata['nietingepland']['layout']}
                            )
                        ],
                        style={
                            'background-color': 'rgba(62,182,235,0.1)', 
                            'margin-top': '1%', 
                            'margin-bottom': '1%', 
                            'margin-left': '1%',
                            'margin-right': '1%',
                            'text-align': 'center',
                            'border-radius': '10px'                   
                            }
                        )
                    ],
                    style={                        
                        'box-shadow': '8px 8px 8px grey',
                        'background-image': """url('./assets/left.png')""",
                        'background-repeat': 'no-repeat',
                        'background-position': '0px 0px',
                        'margin-top': '1%', 
                        'margin-bottom': '1%', 
                        'margin-left': '1%',
                        'margin-right': '1%',
                        'text-align': 'center',
                        'border-radius': '10px'                   
                        }            
                    ), #/second div tab urenverdeling
            ],
            style={'border-style': 'solid',
                'border-width': '2px',
                'background': 'rgb(255,255,255)',
                'background': 'radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(162,162,162,1) 100%, rgba(255,255,255,1) 100%)',
                'margin-top': '5px', 
                'margin-bottom': '5px', 
                'margin-right': '5px', 
                'margin-left': '5px',
                'border-radius': '6px'
                }
            ), #/ tab urenverdeling
                

            
                dcc.Tab(label='Tabelgegevens',children=[
                    html.Div([
                        html.Div([
                            html.H4('Alle kaarten'),
                            dcc.Markdown('Gebruik de knop \'Toggle Columns\' om velden zichtbaar te maken. Vervolgens kun je sorteren en filteren in de tabel.'),
                            dcc.Markdown('Klik op Export om een dump van alle kaarten te downloaden.'),
                            dash_table.DataTable(
                            id='exportallcards',
                            columns = [{'name': 'Kaart', 'id': 'Kaart','hideable': True},
                                       {'name': 'Begindatum','id':'Begindatum','hideable': True},
                                       {'name': 'Einddatum','id':'Einddatum','hideable': True},
                                       {'name': 'Epic','id':'Epic','hideable': True},
                                       {'name': 'URL', 'id': 'URL','hideable': True},
                                       {'name': 'Categorie', 'id': 'Categorie', 'hideable': True},
                                       {'name': 'Hoofdverantwoordelijke', 'id': 'Hoofdverantwoordelijke', 'hideable': True},
                                       {'name': 'Cognosrapport', 'id': 'Cognosrapport', 'hideable': True},
                                       {'name': 'Geplande uren', 'id': 'Geplande uren', 'hideable': True},
                                       {'name': 'Status', 'id': 'Status', 'hideable': True},
                                       {'name': 'Lijst', 'id': 'Lijst', 'hideable': True},
                                       {'name': 'Gearchiveerd', 'id': 'Gearchiveerd', 'hideable': True}
                                      ],
                            hidden_columns=['Kaart', 'Begindatum', 'Einddatum', 'Epic', 'URL', 'Categorie', 'Hoofdverantwoordelijke', 'Cognosrapport', 'Geplande uren','Status','Lijst','Gearchiveerd'],
                            export_format='xlsx',
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",                            
                            export_headers='display',
                            export_columns='all',
                            data= graphdata['doingdatatable'],
                            style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                            style_cell = {'backgroundColor': 'grey', 'color': 'white','text-align': 'left'}
                            ),
                        ],
                        style={
                            'background-color': 'rgba(62,182,235,0.1)', 
                            'margin-top': '5%', 
                            'margin-bottom': '5%', 
                            'margin-left': '1%',
                            'margin-right': '1%',
                            'text-align': 'center',
                            'border-radius': '10px'                   
                            }
                        
                        ),
                            
                    ],
                    style={                        
                        'box-shadow': '8px 8px 8px grey',
                        'background-image': """url('./assets/left.png')""",
                        'background-repeat': 'no-repeat',
                        'background-position': '0px 0px',
                        'margin-top': '5%', 
                        'margin-bottom': '5%', 
                        'margin-left': '1%',
                        'margin-right': '1%',
                        'text-align': 'center',
                        'border-radius': '10px'                   
                        } 
                    ),
                    html.Div([
                        html.Div([
                            html.H4('Kaarten per status'),
                            dcc.Markdown('Maak een keuze in de dropdown (gearchiveerde kaarten kunnen niet worden gekozen)'),
                            dcc.Markdown('Klik daarna op Export om een dump van deze kaarten te downloaden.'),
                            dcc.Dropdown(
                                id='dropdownexportstatus',
                                options=graphdata['optionsstatusesurenpermaand'],
                                multi=True,
                                searchable=False,
                                value = ["Not Started", "Blocked", "Doing", "Done"]
                            ),
                            html.Div([
                                dash_table.DataTable(
                                id='exportcardsperstatus',
                                columns = [{'name': 'Kaart', 'id': 'Kaart','hideable': True},
                                           {'name': 'Begindatum','id':'Begindatum','hideable': True},
                                           {'name': 'Einddatum','id':'Einddatum','hideable': True},
                                           {'name': 'Epic','id':'Epic','hideable': True},
                                           {'name': 'URL', 'id': 'URL','hideable': True},
                                           {'name': 'Categorie', 'id': 'Categorie', 'hideable': True},
                                           {'name': 'Hoofdverantwoordelijke', 'id': 'Hoofdverantwoordelijke', 'hideable': True},
                                           {'name': 'Cognosrapport', 'id': 'Cognosrapport', 'hideable': True},
                                           {'name': 'Geplande uren', 'id': 'Geplande uren', 'hideable': True},
                                           {'name': 'Status', 'id': 'Status', 'hideable': True},
                                           {'name': 'Lijst', 'id': 'Lijst', 'hideable': True},
                                           {'name': 'Gearchiveerd', 'id': 'Gearchiveerd', 'hideable': True}
                                          ],
                                hidden_columns=['Categorie', 'Cognosrapport', 'Lijst','Gearchiveerd'],
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                export_format='xlsx',
                                export_headers='display',
                                export_columns='all',
                                style_header={'backgroundColor': 'rgba(62,182,235,0.6)','color': 'black', 'fontWeight': 'bold', 'fontFamily': 'Arial'},
                                style_cell = {'backgroundColor': 'rgba(62,182,235,0.2)', 'color': 'black','text-align': 'left', 'fontFamily': 'Arial'}
                                ),
                            ],
                            style={

                                'margin-top': '5%', 
                                'margin-bottom': '5%', 
                                'margin-left': '1%',
                                'margin-right': '1%',
                                'text-align': 'center',
                                'border-radius': '10px'                                     
                                }
                            
                            )
                        ],
                        style={
                            'background-color': 'rgba(62,182,235,0.1)', 
                            'margin-top': '5%', 
                            'margin-bottom': '5%', 
                            'margin-left': '1%',
                            'margin-right': '1%',
                            'text-align': 'center',
                            'border-radius': '10px'                   
                            }
                        
                        ),
                            
                    ],
                    style={                        
                        'box-shadow': '8px 8px 8px grey',
                        'background-image': """url('./assets/left.png')""",
                        'background-repeat': 'no-repeat',
                        'background-position': '0px 0px',
                        'margin-top': '5%', 
                        'margin-bottom': '5%', 
                        'margin-left': '1%',
                        'margin-right': '1%',
                        'text-align': 'center',
                        'border-radius': '10px'                   
                        } 
                    ),                
                
                    ],
                
                    style={'border-style': 'solid',
                    'border-width': '2px',
                    'background': 'rgb(255,255,255)',
                    'background': 'radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(162,162,162,1) 100%, rgba(255,255,255,1) 100%)',
                    'margin-top': '5px', 
                    'margin-bottom': '5px', 
                    'margin-right': '5px', 
                    'margin-left': '5px',
                    'border-radius': '6px'
                    }                
                    )
            
            
            ])#/dcctabs
    ],

    
    
    
    
    
    )#/maindiv


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_scripts = ['https://cdn.plot.ly/plotly-locale-nl-latest.js']

app = dash.Dash(external_stylesheets=external_stylesheets,external_scripts=external_scripts)
# app.scripts.append_script({"external_url": "https://cdn.plot.ly/plotly-locale-nl-latest.js"})

auth = dash_auth.BasicAuth(app,USERNAMES)


app.layout = make_layout





executor = ThreadPoolExecutor(max_workers=1)
executor.submit(get_new_data_every)


@app.callback(Output('exportcardsperstatus','data'),
    [Input('dropdownexportstatus','value')])
def exportstatus(somevalue):
    refresh_data()
    return [item for item in graphdata['doingdatatable'] if item['Status'] in somevalue]



@app.callback(Output('my-button','children'), [Input('my-button', 'n_clicks')])
def on_click(n_clicks):
    if n_clicks != None:
        refresh_data()

    return data['refreshed']['daterefreshed']





@app.callback(dash.dependencies.Output('donutepichours','figure'),
    [dash.dependencies.Input('dropdownepics','value')])




def update_fig(input_value):
    refresh_data
    tmp = []
    fig = go.Pie(labels= [j['name'] for j in data['kaarten'].values() if j['epic'] in input_value ],
                  values = [j['Geplande uren'] if j['Geplande uren'] is not None else 0 for j in data['kaarten'].values() if j['epic'] in input_value  ],
                  hole=.5,
                  title= 'Totaal: '+ str(sum(int(i) for i in [j['Geplande uren'] if j['Geplande uren'] is not None else 0 for j in data['kaarten'].values() if j['epic'] in input_value  ])),
                  textinfo='value'
                  )    
    tmp.append(fig)
    

    layout = go.Layout(paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_range=[graphdata['meta']['firstdateplanned'], graphdata['meta']['lastdateplanned']]
                    )

    
    return {
        'data': tmp,
        'layout': layout
    }
 

@app.callback(Output('epicgantt','figure'),
    [Input('dropdownepicsforgantt','value')])

def update_gantt(someinput):
    if someinput != []:
        ganttdata= []
        for i,j in data['kaarten'].items():
            if j['epic'] in someinput:
                if j['status'] in data['statuses']:
                    try:
                        ganttdata.append(dict(Task=j['name'], Start=j['Begindatum'][6:16], Finish=j['Einddatum'][6:16], Resource=j['status']))
                    except:
                        pass
        title = 'Epic: '
        
        for i in someinput: 
            if i != someinput[-1]:
                title += i + ', '
            else:
                title += i
        fig = ff.create_gantt(ganttdata, index_col='Resource', show_colorbar=True, showgrid_x=True, 
            showgrid_y=True,
            title=title)
        fig['layout'].update(paper_bgcolor='rgba(0,0,0,0)', 
                            plot_bgcolor='rgba(0,0,0,0)',)
        return fig
    else:
        return graphdata['emptygraph']


@app.callback(Output('gantttotal','figure'),
    [Input('dropdownepicsforgantttotal','value')])

def update_gantt_total(someinput):
    if someinput != []:
        ganttdata= []
        total_hours=0
        for i,j in data['allepics'].items():
            if j['name'] in someinput:
                try:
                    total_hours += j['Geplande uren']
                except:
                    pass 
        
        for i,j in data['allepics'].items():
            if j['name'] in someinput:
                    try:
                        ganttdata.append(dict(Task=j['name'], Start=j['Begindatum'][6:16], Finish=j['Einddatum'][6:16], Resource=j['Categorie'] ))
                    except:
                        pass
        title = 'Totaalniveau'
    
                
        fig = ff.create_gantt(ganttdata, showgrid_x=True, index_col='Resource', show_colorbar=True,
            showgrid_y=True,
            title=title)
        fig['layout'].update(paper_bgcolor='rgba(0,0,0,0)', 
                            plot_bgcolor='rgba(0,0,0,0)',)
        return fig
    else:
        return graphdata['emptygraph']

        
@app.callback(Output('epicstimeline','figure'),
    [Input('dropdownepicsfortimeline','value'),
    Input('dropdownstatusfortimeline','value')])
    
    
def update_timeline(v1,v2):
    refresh_data
    traces = []


    layout = go.Layout(showlegend=True, 
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis={'title': 'Datum', 'gridcolor': 'gray'},
                        yaxis={'title': 'Ingeplande uren', 'gridcolor': 'gray'})

    for i,j in data['allcards'].items():
   
        if j['epic'] in v1 and j['status'] in v2:
            traces.append(dict(x=data['dates']['all']['Months'],
                y = j['periode'],
                name=i,
                line = {'shape': 'spline', 'smoothing': 0.5},
                mode='lines',
                stackgroup='one',
            ))


    return {
        'data': traces,
        'layout': layout}
        
@app.callback(Output('graph_cat','figure'),
    [Input('dropdownhourscat','value')])
    
def update_hourscat(whatever):
    refresh_data
    traces = []
    layout = go.Layout(paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis={'title': 'Datum', 'gridcolor': 'gray'},
                        yaxis={'title': 'Ingeplande uren', 'gridcolor': 'gray'})
    if whatever == 'periode':
        categorieen = []
        for i,j in data['categories'].items():
            categorieen.append(i)
    
        categorieen.reverse()
        for i in categorieen:
            traces.append(dict(x=data['dates']['all']['Months'],
                y = data['categories'][i]['periode'],
                name = i,
                line = {'shape': 'spline', 'smoothing': 1},
                mode = 'lines',
                stackgroup = 'one'
            
            ))

        traces.append(dict(name='Beschikbare uren',
            mode = 'lines',
            x = data['dates']['all']['Months'],
            y = data['uren']['totaal']['periode'],
            size=10,
            line = {'shape': 'spline', 'smoothing': 0.5},
            
        ))
    if whatever == 'Datum':
        for i,j in data['categories'].items():
            traces.append(dict(x=data['dates']['all']['datum'],
                y = j['Datum'],
                name = i,
                line = {'shape': 'spline', 'smoothing': 1},
                mode = 'lines',
                stackgroup = 'one'
            ))

    return {
         'data': traces,
         'layout': layout}
        



if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0', port=8051)











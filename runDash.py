import pandas as pd
import os,json, locale
import dash, dash_table, dash_auth
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from os import listdir
import plotly.figure_factory as ff
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from datetime import date,datetime,timedelta

with open('./configuration/credentials.txt') as json_file:
    creds = json.load(json_file)

USERNAMES = {creds.get('Username for Dash'): creds.get('Password for Dash')}

locale = locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')


def refresh_data():
    with open('./data/date.txt', 'r') as f2:
        dateofdata = f2.read()

    daterefreshed = datetime.strftime(datetime.strptime(dateofdata,'%Y-%m-%d, %H:%M:%S'),'%A %-d %B, %H:%M')
    if datetime.strptime(dateofdata,'%Y-%m-%d, %H:%M:%S') < datetime.now() - timedelta(hours=1):
        import createjsons
    global data
    data = {}
    def loadjson(file):
        with open('./data/'+file) as json_file:
            return json.load(json_file)
    for i in listdir('./data'):
        if i[-5:]== '.json':
            name = i[:-5]
            values = loadjson(i)
            data[name] = values
    data['refreshed'] = {'daterefreshed': daterefreshed, 'dateofdata': dateofdata}
    create_graphdata()

def create_graphdata():
    global graphdata
    graphdata = {}
    datesofcards = []
    for i,j in data['kaarten'].items():
        datesofcards.append(datetime.strptime(j['created'][6:], '%Y-%m-%d, %H:%M:%S'))
    graphdata['meta'] = {'eerstedatum': min(datesofcards).date(),'huidigedatum': datetime.now().date()}
    layoutforlistsgraph = go.Layout(paper_bgcolor='rgba(0,0,0,0)', 
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    autosize=True,
                                    xaxis_range=[graphdata['meta']['eerstedatum'],graphdata['meta']['huidigedatum']],
                                    xaxis={'title': 'Datum', 'gridcolor': 'gray'},
                                    yaxis={'title': 'Aantal kaarten', 'gridcolor': 'gray'})
    tracesforlistsgraph = []
    for i,j in data['lists'].items():
        tracesforlistsgraph.append(dict(x=data['dates']['history']['datum'],
                                        y=j['Datum'],
                                        name=i,
                                        mode='lines',
                                        line = {'shape': 'spline', 'smoothing': 0.5},
                                        stackgroup='one'))

    layoutforstackedbars = go.Layout(barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    barsfornietingepland = []
    for i,j in data['nietingepland']['data'].items():
            barsfornietingepland.append(dict(x=data['nietingepland']['labels'],
                        y=data['nietingepland']['data'].get(i),
                        name=i,
                        type='bar'
                        ))
                        
    optionsstatusesurenpermaand=[] 
    for name in data['statuses']:
        optionsstatusesurenpermaand.append({'label':name, 'value':name})   
    
    testdf = [dict(Task="Job A", Start='2009-01-01', Finish='2009-02-28'),
        dict(Task="Job B", Start='2009-03-05', Finish='2009-04-15'),
        dict(Task="Job C", Start='2009-02-20', Finish='2009-05-30')]
    
    graphdata['testfig'] = ff.create_gantt(testdf)
    
    
    graphdata['listgraph'] = {'traces': tracesforlistsgraph, 'layout': layoutforlistsgraph}
    graphdata['nietingepland']= {'data': barsfornietingepland, 'layout': layoutforstackedbars}
    graphdata['optionsstatusesurenpermaand'] = optionsstatusesurenpermaand
                                          
    



UPDADE_INTERVAL = 5

def get_new_data_every(period=UPDADE_INTERVAL):
    """Update the data every 'period' seconds"""

    while True:
        refresh_data()
        time.sleep(period)


refresh_data()


def make_layout():
    refresh_data()
    
    return html.Div([
        
        html.Div([
            html.Div(
            className='row',
            children = [
                html.Div(
                    className='tekst', children=[
                        html.H1('Werkvoorraad'),

                        ],
                        style = {'display': 'inline-block',
                            'width': '80%'
                        }
                        ,

                    ),
                html.Div(
                    className='logo', children=[
                        html.Img(src=app.get_asset_url('logonop.png'), style={'width': '150px','margin-right': '0px'})
                    
                    
                    
                    
                    ],
                    style = {'display': 'inline-block',

                    'margin-right': '1px'
                        
                        
                    }
                
                
                ),
                
                
                
                ],
                

                
                

            )
            
            
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
            'text-align': 'center'}
            ),
        
        
        
        html.Div([
            html.Button('Click Me', id='my-button'),
            dcc.Markdown('''**Tijdstip van refresh: **''' + data['refreshed']['daterefreshed'])

            ]),
        dcc.Tabs([
            dcc.Tab(label='Epics', children=[
                
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
                                    ),
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
                                ),
                        
                        
                        
                        html.Div(
                            className='five columns',
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
                                    'margin-right': '1%',}),#/dropdownepics
                                    
                                html.Div([
                                    dcc.Graph(id='donutepichours')
                                    
                                    
                                    ],
                                    style={'margin-bottom': '15px',
                                    'margin-top': '1%', 
                                    'margin-left': '1%',
                                    'margin-right': '1%',
                                    }
        
                                    ),#/donutepichours   
                                    
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
                            ),#upperdiv
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
                  
                    ),
            html.Div([

                html.Div([
                    html.H4('Uren per maand'),
                    dcc.Markdown('Gebruik de Dropdown hieronder om de epics te kiezen.'),
                    html.Div([
                        dcc.Dropdown(
                            id='dropdownepicsfortimeline',
                            options=[{'label':name, 'value':name} for name in data['epics'].keys()],
                            multi=True,
                            value = [next(iter(data['epics']))]
                                ),
                        dcc.Markdown('Kies hieronder de statussen om te laten zien.'),
                        dcc.Dropdown(
                            id='dropdownstatusfortimeline',
                            options=graphdata['optionsstatusesurenpermaand'],
                            multi=True,
                            searchable=False,
                            value = ["Not Started", "Blocked", "Doing", "Done"]
                            )
                        ],
                        style={'margin-left': '1%',
                                'margin-right': '1%',}
                        
                        ),
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
                    
                    )
                
                ],
                style={ 'width': '100%',
                'display': 'inline-block', 
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
                
                ## testdf
                
            html.Div([

                html.Div([
                    html.H4('Test GANTT chart'),
                    dcc.Markdown('Gebruik de Dropdown hieronder om de epics te kiezen.'),
                    html.Div([
                        dcc.Dropdown(
                            id='dropdownepicsforgantt',
                            options=[{'label':name, 'value':name} for name in data['epics'].keys()],
                            multi=True,
                            value = [next(iter(data['epics']))]
                                ),

                        ],
                        style={'margin-left': '1%',
                                'margin-right': '1%',}
                        
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
                    
                    )
                
                ],
                style={ 'width': '100%',
                'display': 'inline-block', 
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
            
            dcc.Tab(label='Trellogebruik', children=[
                html.Div([

                    
                    html.Div([
                        
                        html.H3('Aantal kaarten per lijst'),
                        dcc.Markdown('''**Uitleg**'''),
                        dcc.Markdown('''Deze grafiek geeft aan hoeveel kaarten er per lijst wanneer op Trello stonden. Rechts staan de lijsten uit Trello. Door op deze lijsten te klikken, kunnen ze aan of uit gezet worden.'''),
                        dcc.Markdown('''**Let op: ** Dit is een weergave van **alle** lijsten! Ook de kaarten die klaar zijn!'''),

                        dcc.Graph(id='graph_lists',figure={'data': graphdata['listgraph']['traces'],
                                                    'layout': graphdata['listgraph']['layout']})
                        
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
            ),#/tab allekaarten
            
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
                                
                        ),
                html.Div([

                    
                    html.Div([html.Div([
                        
                        html.H4('(nog) niet ingeplande uren'),
                        

                        ],
                        style={'margin-left': '1%',
                                'margin-right': '1%',
                                'margin-top': '1%',
                                'margin-bottom': '1%'
                            
                        }
                        
                        ),                        


                        dcc.Graph(id='graph_nietingepland',figure={'data': graphdata['nietingepland']['data'], 'layout': graphdata['nietingepland']['layout']})
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
                    ),
                
                
                
                
                
                #/ children urenverdeling
                
                
                
                
                #/ tab urenverdeling
            
            
            
            
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

@app.callback(Output('my-button','children'), [Input('my-button', 'n_clicks')])
def on_click(n_clicks):
    if n_clicks != None:
        import createjsons
        refresh_data()
        make_layout()
        return 'Data refreshen'
        
    else:
        return 'Data refreshen'




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
    
    # layout = {'title': 'Kaarten'}
    layout = go.Layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    
    return {
        'data': tmp,
        'layout': layout
    }
 

@app.callback(Output('epicgantt','figure'),
    [Input('dropdownepicsforgantt','value')])

def update_gantt(someinput):

    ganttdata= []
    for i,j in data['kaarten'].items():
        if j['epic'] in someinput:
            if j['status'] in data['statuses']:
                try:
                    ganttdata.append(dict(Task=j['name'], Start=j['Begindatum'][6:16], Finish=j['Einddatum'][6:16], Resource=j['status']))
                except:
                    pass
    return ff.create_gantt(ganttdata, index_col='Resource', show_colorbar=True, showgrid_x=True, showgrid_y=True)



        
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

        traces.append(dict(name='Geplande uren',
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
    app.run_server(debug=True,host='0.0.0.0')









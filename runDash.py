import os, json, locale, requests, dash, dash_table, copy, time, flask, base64
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
from os import listdir
import plotly.figure_factory as ff
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dash.dependencies import Input, Output
from datetime import date,datetime,timedelta,time
from dateutil.relativedelta import relativedelta
 
#--! Check if app is deployed
try:
    with open('./configuration/credentials.txt') as json_file:
        credentials = json.load(json_file)
    with open('./configuration/configuration.txt') as json_file:
        config = json.load(json_file)
except:
    raise Exception('Draai eerst deploy.py!')
    
#--! Set locale
locale = locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')

#--! Set all global variables
globals = {'config': config, 'credentials': credentials, 'styles': {}}
board_url = 'https://api.trello.com/1/members/me/boards?fields=name&key='+credentials.get('API key')+ "&token="+credentials.get('API token')
boards = json.loads(json.dumps(requests.get(board_url).json()))
globals['boards'] = boards
globals['styles']['maindivs'] = {'box-shadow': '8px 8px 8px grey',
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
globals['styles']['tabs'] = {'border-style': 'solid',
                            'border-width': '2px',
                            'background': 'rgb(255,255,255)',
                            'background': 'radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(162,162,162,1) 100%, rgba(255,255,255,1) 100%)',
                            'margin-top': '5px', 
                            'margin-bottom': '5px', 
                            'margin-right': '5px', 
                            'margin-left': '5px',
                            'border-radius': '6px'
                            }
globals['styles']['divgraphs'] = {'background-color': 'rgba(62,182,235,0.1)',
                                'margin-top': '1%', 
                                'margin-bottom': '2%', 
                                'margin-left': '1%',
                                'margin-right': '1%',
                                'text-align': 'center',
                                'border-radius': '10px'                   
                                }
globals['styles']['dropdowns'] = {'margin-left': '1%', 'margin-right': '2%'}

globals['graphlayouts']= {'bars': go.Layout(barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode='closest')}

#--! Create function to refresh data

def get_data(value):
    # set data variable to global to use in other functions
    global data
    global config
    with open('./configuration/configuration.txt') as json_file:
        configfile = json.load(json_file)
    config = configfile.get(value)
    # set all url variables
    keys = "key="+credentials.get('API key')+"&token="+credentials.get('API token')
    trello_base_url = "https://api.trello.com/1/"
    board_url = trello_base_url+"boards/"+ value    
    #board_url = trello_base_url+"boards/"+ config.get('Board ID')
    url_cards = board_url+"?cards=all&card_pluginData=true&card_attachments=true&card_customFieldItems=true&filter=all&"+keys
    url_lists = board_url+"/lists?filter=all&"+keys
    url_customfields = board_url+"/customFields?"+keys
    url_labels = board_url+"/labels?"+keys
    url_members = board_url+"/members?"+keys
    
    # get JSON
    board = json.loads(json.dumps(requests.get(url_cards).json()))
    lists = json.loads(json.dumps(requests.get(url_lists).json()))
    customfields = json.loads(json.dumps(requests.get(url_customfields).json()))
    labels = json.loads(json.dumps(requests.get(url_labels).json()))
    members = json.loads(json.dumps(requests.get(url_members).json()))
    cards = board['cards']
    
    # create function to convert Trello date to datetime
    def dateCalc(date):
        try:
            newdate = datetime.strptime(date[0:19],'%Y-%m-%dT%H:%M:%S')
            return newdate
        except:
            return None
    
    # create dict for custom fields
    customfields_dict = {'date': {},'list': {}, 'text': {}, 'number': {}, 'checkbox': {}}
    for i in customfields:
        customfields_dict[i['type']] = {}
    for i in customfields:
        customfields_dict[i['type']][i['id']] = {}
    for i in customfields:
        if i['type'] == 'list':
            customfields_dict[i['type']][i['id']]['name'] = i['name']
            customfields_dict['list'][i['id']]['options'] = {}
            for j in i['options']:
                customfields_dict['list'][i['id']]['options'][j['id']] = j['value'].get('text')
        else:
            customfields_dict[i['type']][i['id']]['name'] = i['name']
    
    # collect all chosen lists
    chosenlists = []
    for i in config.get('Not Started'):
        chosenlists.append(i)
    chosenlists.extend(config.get('Blocked'))
    chosenlists.extend(config.get('Doing'))
    chosenlists.extend(config.get('Done'))
    for i in config.get('Epics'):
        chosenlists.append(i)
    for i in config.get('Always continuing'):
        chosenlists.append(i)
    for i in config.get('List with Epics Done'):
        chosenlists.append(i)
    
    # create function to convert cardid to datetime
    def idtodate(cardid):
        hex = cardid[0:8]
        timestamp = int(hex,16)
        timedate = datetime.fromtimestamp(timestamp)
        return timedate  

    # create function to get the epic id from the attachment-urls
    def get_epicid(url):
        try:
            if 'epicId=' in url:
                start = url.find('epicId=')+7
                end = url.find('&attachmentId=')
                return url[start:end]
            else:
                pass
        except:
            pass

    # create dict for cards
    kaarten = {i['id']: {'Naam': i['name'],
                         'KaartID': i['id'],
                         'ListID': i['idList'],
                         'customfields': i['customFieldItems'],
                         'Aangemaakt': idtodate(i['id']),
                         'labels': [label['name'] for label in i['labels'] if i['labels'] != []],
                         'members': [member['fullName'] for member in members if member['id'] in i['idMembers']],
                         'Sjabloon': i['isTemplate'],
                         'Vervaldatum': dateCalc(i['due']),
                         'Gearchiveerd': i['closed'],
                         'epicid': [get_epicid(j['url']) for j in i['attachments']],
                         'Epic': None,
                         'shortUrl': i['shortUrl']
                        } for i in cards}
                        
    # remove all attachments except epic-attachments, plus add all members in one string field
    for i,j in kaarten.items():
        while None in j['epicid']:
            j['epicid'].remove(None)
        if j['members'] != []:
            j['Leden'] = ''
            for k in j['members']:
                if j['Leden'] == '':
                    j['Leden'] += k
                else:
                    j['Leden'] += ', '+ k        
        else:
            j['Leden'] = None
        del j['members']

    # add the custom fields to cards-dict
    if customfields_dict != {}:
        for i,j in customfields_dict.items():
            for k,l in j.items():
                for m,n in kaarten.items():
                    n[l['name']] = None
        for i,j in kaarten.items():
            for k in j['customfields']:
                if k['idCustomField'] in customfields_dict['list'].keys():
                    j[customfields_dict['list'][k['idCustomField']].get('name')] = customfields_dict['list'][k['idCustomField']]['options'].get(k['idValue'])
                elif k['idCustomField'] in customfields_dict['checkbox'].keys():
                    if k['value']['checked'] == 'true':
                        j[customfields_dict['checkbox'][k['idCustomField']].get('name')] = True
                    else:
                        j[customfields_dict['checkbox'][k['idCustomField']].get('name')] = False
                elif k['idCustomField'] in customfields_dict['date'].keys():
                    j[customfields_dict['date'][k['idCustomField']].get('name')] =  dateCalc(k['value'].get('date')) 
                else:
                    for key in k['value']:
                        j[customfields_dict[key][k['idCustomField']].get('name')] = k['value'].get(key)
    
    # add epicname
    epicIdNameCategory = []
    for i,j in kaarten.items():
        epicIdNameCategory.append((i,j['Naam'],j[config.get('Custom Field for Categories')]))                    
    for i,j in kaarten.items():
        if j['epicid'] == []:
            j['Epic'] = 'Geen epic'
            j['Categorie'] = None
        else:
            for k in epicIdNameCategory:
                if k[0] == j['epicid'][0]:
                    j['Epic'] = k[1]
                    j['Categorie'] = k[2]
        del j['epicid']

    # add listname and status
    for i,j in kaarten.items():
        for k in lists:
            if j['ListID'] == k['id']: j['Lijst'] = k['name']
        if j['Lijst'] in config.get('Not Started'):
            j['Status'] = 'Niet gestart'
        elif j['Lijst'] in config.get('Doing'):
            j['Status'] = 'Doing'
        elif j['Lijst'] in config.get('Blocked'):
            j['Status'] = 'Blocked'
        elif j['Lijst'] in config.get('Done'):
            j['Status'] = 'Done'
        elif j['Lijst'] in config.get('Always continuing'):
            j['Status'] = 'Doorlopend'
        elif j['Lijst'] in config.get('Epics'):
            j['Status'] = 'Epics Doing'
        elif j['Lijst'] in config.get('List with Epics Done'):
            j['Status'] = 'Epics Done'
        else:
            j['Status'] = 'Archived'
        del j['customfields']
        del j['ListID']
    for i,j in kaarten.items():
        if j['Gearchiveerd'] == True and j['Status'] != 'Done':
            j['Status'] = 'Archived'

    # collect all lists with cards to delete
    liststodelete = []
    for i in lists:
        if i['name'] not in chosenlists:
            liststodelete.append(i['name'])

    # collect all cards to delete
    cardstodelete = []
    for i,j in kaarten.items():
        if j['Sjabloon'] == True:
            cardstodelete.append(i)
        elif j['Lijst'] in liststodelete:
            cardstodelete.append(i)
    
    # create hours-dict for available hours
    hours = {}
    for i,j in kaarten.items():
        if j['Lijst'] == config.get('List for hours'):
            hours[j['Naam']] = {config['Custom Field for Starting date']: j[config['Custom Field for Starting date']], config['Custom Field for Ending date']: j[config['Custom Field for Ending date']], config['Custom Field with hours']: j[config['Custom Field with hours']]}

    # delete previously collected cards
    for i in cardstodelete:
        if i in kaarten:
            del kaarten[i]

    # create list with all dates (6 months history, 1yr in advance)
    tmpdatesdict = {}
    now = datetime.now().date()
    numdays = 365
    numdayshistory = 183

    for x in range (0, numdays):
        tmpdatesdict[str(now + timedelta(days = x))] = {}
    for x in range (0,numdayshistory):
        tmpdatesdict[str(now - timedelta(days = x))] = {}

    dates = []
    for i in sorted(tmpdatesdict):
        dates.append(i)        
    
    # create some global arrays for later use
    arrays = {'epics': list(dict.fromkeys([card['Epic'] for card in kaarten.values()])), 
              'xaxis_months': list(dict.fromkeys([i[0:4]+"-"+i[5:7]+"-01" for i in dates])), 
              'perioden': list(dict.fromkeys([i[0:4]+i[5:7] for i in dates])),
              'statuses': list(dict.fromkeys([card['Status'] for card in kaarten.values()])), 
              config.get('Custom Field for Categories'): list(dict.fromkeys([card[config.get('Custom Field for Categories')] for card in kaarten.values()])),
              config.get('Custom Field for Person'): list(dict.fromkeys([card[config.get('Custom Field for Person')] if card[config.get('Custom Field for Person')] != None else 'Geen ' + config.get('Custom Field for Person') for card in kaarten.values() ])),
            
    }
              
    # create dict to calculate the hours per day for each card   
    try:
        urenperdagperkaart = {kaart['Naam']: {'Naam': kaart['Naam'],
                                              'Leden': kaart['Leden'],
                                              'Aangemaakt': kaart['Aangemaakt'],
                                              'Epic': kaart['Epic'],
                                              'shortUrl': kaart['shortUrl'],
                                              config.get('Custom Field for Starting date'): kaart[config.get('Custom Field for Starting date')],
                                              config.get('Custom Field for Ending date'): kaart[config.get('Custom Field for Ending date')],
                                              'Gebied': kaart['Gebied'],
                                              config.get('Custom Field for Person'): kaart[config.get('Custom Field for Person')],
                                              config.get('Custom Field for Categories'): kaart[config.get('Custom Field for Categories')],
                                              config.get('Custom Field with hours'): kaart[config.get('Custom Field with hours')],
                                              'Cognosrapport': kaart['Cognosrapport'],
                                              'Niet meenemen in telling': kaart['Niet meenemen in telling'],
                                              'Lijst': kaart['Lijst'],
                                              'Status': kaart['Status'],
                                              'urenperdag': {i:0 for i in dates},
                                              'urenperperiode': {i:0 for i in arrays['perioden']}}              

                                             for kaart in kaarten.values()}
    except:
        urenperdagperkaart = {kaart['Naam']: {'Naam': kaart['Naam'],
                                              'Leden': kaart['Leden'],
                                              'Aangemaakt': kaart['Aangemaakt'],
                                              'Epic': kaart['Epic'],
                                              'shortUrl': kaart['shortUrl'],
                                              config.get('Custom Field for Starting date'): kaart[config.get('Custom Field for Starting date')],
                                              config.get('Custom Field for Ending date'): kaart[config.get('Custom Field for Ending date')],
                                              config.get('Custom Field for Person'): kaart[config.get('Custom Field for Person')],
                                              config.get('Custom Field for Categories'): kaart[config.get('Custom Field for Categories')],
                                              config.get('Custom Field with hours'): kaart[config.get('Custom Field with hours')],
                                              'Lijst': kaart['Lijst'], 
                                              'Status': kaart['Status'],
                                              'urenperdag': {i:0 for i in dates},
                                              'urenperperiode': {i:0 for i in arrays['perioden']}}              

                                             for kaart in kaarten.values()}
                                         
    # do the same for available hours  
    beschikbareuren = {key: {'urenperdag': {i:0 for i in dates},
                             'urenperperiode': {i:0 for i in arrays['perioden']}}
                           for key in hours.keys()}
    for i in dates:
        datekey = datetime.strptime(i,'%Y-%m-%d').date()
        for k,l in kaarten.items():
            if l['Niet meenemen in telling'] != True:
                try:
                    if l[config.get('Custom Field for Starting date')].date() < datekey <= l[config.get('Custom Field for Ending date')].date():
                        delta = l[config.get('Custom Field for Ending date')] - l[config.get('Custom Field for Starting date')]
                        hoursperday = int(l[config.get('Custom Field with hours')])/int(delta.days)                
                        urenperdagperkaart[l['Naam']]['urenperdag'][i] = hoursperday
                except:
                    pass
        for k,l in hours.items():
            try:
                if l[config.get('Custom Field for Starting date')].date() < datekey <= l[config.get('Custom Field for Ending date')].date():
                    hoursperday = int(l[config.get('Custom Field with hours')])/int(30.4)                
                    beschikbareuren[k]['urenperdag'][i] = hoursperday
            except:
                pass
    
    # calculate the hours per month with the hours per day for each card
    for i,j in urenperdagperkaart.items():
        for k,l in j['urenperdag'].items():
            for m in j['urenperperiode'].keys():
                if m==k[0:4]+k[5:7]:
                    j['urenperperiode'][m] += l

    
    # do the same for available hours 
    for i,j in beschikbareuren.items():
        for k,l in j['urenperdag'].items():
            for m in j['urenperperiode'].keys():
                if m==k[0:4]+k[5:7]:
                    j['urenperperiode'][m] += l

    
    # create data for a dataframe with the hours per month
    dfurenpermaand = copy.deepcopy(urenperdagperkaart)
    for i,j in dfurenpermaand.items():
        try:
            j['Geplande uren'] = int(j['Geplande uren'])
        except:
            j['Geplande uren'] = 0
        for k,l in j['urenperperiode'].items():
            j[k] = round(l,2)
        del j['urenperperiode']
    
    # create a bar chart with all cards with no begin and end date
    bars = []
    labelsnietingepland = []
    for j in kaarten.values():
        if j[config.get('Custom Field for Starting date')] == None and j[config.get('Custom Field for Ending date')] == None and j[config.get('Custom Field with hours')] !=None and j['Status'] == 'Niet gestart':
            labelsnietingepland.append(j['Lijst'])
    labelsnietingepland = list(dict.fromkeys(labelsnietingepland))
    for i,j in kaarten.items():
        if j[config.get('Custom Field for Starting date')] == None and j[config.get('Custom Field for Ending date')] == None and j[config.get('Custom Field with hours')] !=None and j['Status'] == 'Niet gestart':
            tmp = []
            for label in labelsnietingepland:
                if j['Lijst'] == label:
                    tmp.append(int(j['Geplande uren']))
                else:
                    tmp.append(0)
            bars.append(dict(x=labelsnietingepland,
                            y=tmp,
                            name=j['Naam'],
                            type='bar',
                            opacity='0.6')) 
    
    # create a bar chart with all cards with no begin and end date per epic    
    epicbars = []
    tmpepicsforbarchart = {epic: 0 for epic in [name['Naam'] for name in kaarten.values() if name['Status'] in ['Epics Doing', 'Epics Done']]}
    tmpepicsforbarchart['Geen epic'] = 0
    for i,j in kaarten.items():
        if j[config.get('Custom Field for Starting date')] == None and j[config.get('Custom Field for Ending date')] == None and j[config.get('Custom Field with hours')] !=None and j['Status'] == 'Niet gestart':
            tmpepicsforbarchart[j['Epic']] += int(j[config.get('Custom Field with hours')])

    epicsforbarchart = { k:v for k,v in tmpepicsforbarchart.items() if v!=0 }

    epicbars.append(dict(x=[key for key in epicsforbarchart.keys()],
                         y=[value for value in epicsforbarchart.values()],
                         type='bar',
                         text=[value for value in epicsforbarchart.values()],
                         textposition='outside',
                         opacity='0.6'))

    # create figure for gauge (planned vs available hours)
    thismonth = datetime.strftime(datetime.now(), '%Y%m')
    nextmonth = (datetime.now() + relativedelta(months=1)).strftime('%Y%m')
    twomonths = (datetime.now() + relativedelta(months=2)).strftime('%Y%m')
    
    arrays['threemonths'] = [(thismonth, datetime.strptime(thismonth,'%Y%m').strftime('%B')), (nextmonth, datetime.strptime(nextmonth,'%Y%m').strftime('%B')), (twomonths, datetime.strptime(twomonths,'%Y%m').strftime('%B'))]
    
    
    gaugegeplandthismonth = round(sum([value for card in urenperdagperkaart.values() for keys,value in card['urenperperiode'].items() if keys==thismonth]))
    gaugegeplandnextmonth = round(sum([value for card in urenperdagperkaart.values() for keys,value in card['urenperperiode'].items() if keys==nextmonth]))
    gaugegeplandtwomonths = round(sum([value for card in urenperdagperkaart.values() for keys,value in card['urenperperiode'].items() if keys==twomonths]))

    deltathismonth = round(sum([value for card in beschikbareuren.values() for keys,value in card['urenperperiode'].items() if keys==thismonth]))
    deltanextmonth = round(sum([value for card in beschikbareuren.values() for keys,value in card['urenperperiode'].items() if keys==nextmonth]))
    deltatwomonths = round(sum([value for card in beschikbareuren.values() for keys,value in card['urenperperiode'].items() if keys==twomonths]))

    if deltathismonth > gaugegeplandthismonth:
        gaugerangethismonth = deltathismonth + 20
    else:
        gaugerangethismonth = gaugegeplandthismonth + 20

    if deltanextmonth > gaugegeplandnextmonth:
        gaugerangenextmonth = deltanextmonth + 20
    else:
        gaugerangenextmonth = gaugegeplandnextmonth + 20

    if deltatwomonths > gaugegeplandtwomonths:
        gaugerangetwomonths = deltatwomonths + 20
    else:
        gaugerangetwomonths = gaugegeplandtwomonths + 20

    gaugestepsthismonth = {'axis': {'range': [None, gaugerangethismonth]},
                 'bar': {'color': '#3eb6eb'},
                 'steps': [
                     {'range': [0, deltathismonth*0.5], 'color': '#3deb34'},
                     {'range': [deltathismonth*0.5, deltathismonth*0.75], 'color': '#b4eb34'},
                     {'range': [deltathismonth*0.75, deltathismonth*0.9], 'color': '#ebb434'},
                     {'range': [deltathismonth*0.9, deltathismonth], 'color': '#eb6e34'},
                     {'range': [deltathismonth,gaugerangethismonth], 'color': '#eb3434'},
                     ],
                  'threshold': {'line': {'color': "#5c0000", 'width': 4}, 'thickness': 0.75, 'value': deltathismonth}
                 }
    gaugestepsnextmonth = {'axis': {'range': [None, gaugerangenextmonth]},
                 'bar': {'color': '#3eb6eb'},
                 'steps': [
                     {'range': [0, deltanextmonth*0.5], 'color': '#3deb34'},
                     {'range': [deltanextmonth*0.5, deltanextmonth*0.75], 'color': '#b4eb34'},
                     {'range': [deltanextmonth*0.75, deltanextmonth*0.9], 'color': '#ebb434'},
                     {'range': [deltanextmonth*0.9, deltanextmonth], 'color': '#eb6e34'},
                     {'range': [deltanextmonth,gaugerangenextmonth], 'color': '#eb3434'},
                     ],
                  'threshold': {'line': {'color': "#5c0000", 'width': 4}, 'thickness': 0.75, 'value': deltanextmonth}
                 }  
    gaugestepstwomonths = {'axis': {'range': [None, gaugerangetwomonths]},
                 'bar': {'color': '#3eb6eb'},
                 'steps': [
                     {'range': [0, deltatwomonths*0.5], 'color': '#3deb34'},
                     {'range': [deltatwomonths*0.5, deltatwomonths*0.75], 'color': '#b4eb34'},
                     {'range': [deltatwomonths*0.75, deltatwomonths*0.9], 'color': '#ebb434'},
                     {'range': [deltatwomonths*0.9, deltatwomonths], 'color': '#eb6e34'},
                     {'range': [deltatwomonths,gaugerangetwomonths], 'color': '#eb3434'},
                     ],
                  'threshold': {'line': {'color': "#5c0000", 'width': 4}, 'thickness': 0.75, 'value': deltatwomonths}
                 }  
    gaugefig = go.Figure()

    gaugefig.add_trace(go.Indicator(
        domain = {'x': [0, 0.3], 'y': [0, 1]},
        value = gaugegeplandthismonth,
        mode = "gauge+number+delta",
        title = {'text': "Totale uren voor " + datetime.strptime(thismonth,'%Y%m').strftime('%B')},
        delta = {'reference': deltathismonth},
        gauge = gaugestepsthismonth
    ))
    gaugefig.add_trace(go.Indicator(
        domain = {'x': [0.35, 0.65], 'y': [0, 1]},
        value = gaugegeplandnextmonth,
        mode = "gauge+number+delta",
        title = {'text': "Totale uren voor " + datetime.strptime(nextmonth,'%Y%m').strftime('%B')},
        delta = {'reference': deltanextmonth},
        gauge = gaugestepsnextmonth
    ))    
    gaugefig.add_trace(go.Indicator(
        domain = {'x': [0.7, 1], 'y': [0, 1]},
        value = gaugegeplandtwomonths,
        mode = "gauge+number+delta",
        title = {'text': "Totale uren voor " + datetime.strptime(twomonths,'%Y%m').strftime('%B')},
        delta = {'reference': deltatwomonths},
        gauge = gaugestepstwomonths
    ))     

    gaugefig.update_layout(paper_bgcolor='rgba(0,0,0,0)', 
                                        plot_bgcolor='rgba(0,0,0,0)',)




    graphdata = {'nietingepland': bars, 'nietingeplandepics': epicbars, 'gaugefig': gaugefig}
    
    columntypes = {}
    for key, value in kaarten[next(iter(kaarten))].items():
        if 'datum' in key or key == 'Aangemaakt':
            columntypes[key] = 'datetime'
        elif type(value) == int:
            columntypes[key] = 'numeric'
        elif type(value in [str,bool]):
            columntypes[key] = 'text'
    
    columntypesurenpermaand = dict(columntypes)
    
    columntypesurenpermaand.update({i: 'text' for i in arrays['perioden']})
    
    data = {'kaarten': kaarten, 
            'arrays': arrays,
            'urenperdagperkaart': urenperdagperkaart,
            'beschikbareuren': beschikbareuren,
            'graphdata': graphdata,
            'dfs': {'kaartendf': pd.DataFrame(data=kaarten).T,
                    'columntypes': columntypes,
                    'urenpermaand': pd.DataFrame(data=dfurenpermaand).T,
                    'columntypesurenpermaand': columntypesurenpermaand
                    
            }
                    
    }
                                
#--! Create layout function. Only create a simple layout with a few components. The rest will be loaded using callbacks.
def make_layout():
    return html.Div(
        className='First Div',
        
        children=[
            html.Div(
                style={
                    'font-style': 'italic',
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
                    },
                className='Banner',
                children=[
                    html.Div(
                        style={'display': 'inline-block', 'width': '80%'},
                        children=[
                            html.H1('Trello borden USD'),
                            ]
                        ),
                    html.Div(
                        style={'display': 'inline-block', 'margin-right': '1px'},
                        children=[
                            html.Img(src=app.get_asset_url('logonop.png'), style={'width': '150px','margin-right': '0px'})
                            ]
                        )
                    ]
                ),


            html.H5('Kies hieronder een bord', style={'text-align': 'center'}),
            dcc.Dropdown(
                id='dropdown_boards',
                options=[{'label': i['name'], 'value': i['id']} for i in boards],
                value = boards[0]['id'],
                ),


            html.Button('Data verversen', id='refreshdatabtn', n_clicks=0),
            html.Div(
                id='test'
                )
            ]
    )#/firstdiv    
        
#--! Get CSS files and scripts and set App (including layout)        
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_scripts = ['https://cdn.plot.ly/plotly-locale-nl-latest.js']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,external_scripts=external_scripts, url_base_pathname='/dash/')
app.layout = make_layout
#--! Set Dash to suppress callback exceptions, because some callbacks can only be made when the first callback in the main layout has been made.
app.config['suppress_callback_exceptions'] = True



#--! Define app callbacks

#---! dropdown_boards
    # This function should be changed when more boards are added. For now, only Werkvoorraad is compatible.
@app.callback(Output('test', 'children'),
    [Input('dropdown_boards', 'value'),
    Input('refreshdatabtn', 'n_clicks')]
    )
def create_maindiv(value, n_clicks):
    # first retrieve all data
    get_data(value)
    import os
    if os.name=='nt':
        daterefreshed = datetime.strftime(datetime.now(), '%A %d %b, %H:%M')
    else:
        daterefreshed = datetime.strftime(datetime.now(),'%A %-d %B, %H:%M')
    # Return all other divs
    return html.Div(
        className='', 
        children=[
            # Show date of refresh
            dcc.Markdown('''**Laatst ververst: **''' + daterefreshed),
            # Create tabs
            dcc.Tabs(
                className='Tabs', 
                children=[
                    # Create first tab
                                            
                    dcc.Tab(
                        label='Gantt charts',
                        style=globals['styles']['tabs'], 
                        children=[
                            html.Div(
                                className='tab2_div1',
                                style=globals['styles']['maindivs'],
                                children=[
                                    html.H3('Uitleg'),
                                    html.Div(
                                        style=globals['styles']['divgraphs'],
                                        children=[                                    
                                            dcc.Markdown('''In dit tabblad worden de kaarten in GANTT charts weergegeven. Kies in de dropdown voor welke epic de kaarten moeten worden weergegeven.'''),
                                            ]
                                        ),
                                    ]
                                ),                             
                            html.Div(
                                className='tab2_div2',
                                style=globals['styles']['maindivs'],
                                children=[
                                    html.H4('Gantt per epic'),
                                    dcc.Dropdown(
                                        style = globals['styles']['dropdowns'],
                                        id='dropdownganttepics',
                                        options=[{'label':name, 'value':name} for name in data['arrays']['epics']],
                                        value = [next(iter(data['arrays']['epics']))]
                                        ),
                                    html.Div(
                                        style=globals['styles']['divgraphs'],
                                        children=[                                        
                                            dcc.Graph(id='ganttepics'),
                                            ]
                                        ),
                                    ]
                                ),
                            html.Div(
                                className='tab2_div3',
                                style=globals['styles']['maindivs'],
                                children=[
                                    html.H4('Gantt per persoon'),
                                    dcc.Dropdown(
                                        style = globals['styles']['dropdowns'],
                                        id='dropdownganttpersoon',
                                        options=[{'label':name, 'value':name} for name in data['arrays'][config.get('Custom Field for Person')]],
                                        ),
                                    dcc.Dropdown(
                                        style = globals['styles']['dropdowns'],
                                        id='dropdownganttpersoonstatus',
                                        options=[{'label':name, 'value':name} for name in data['arrays']['statuses']],
                                        value = data['arrays']['statuses'],
                                        multi=True,
                                        ),
                                        
                                    html.Div(
                                        style=globals['styles']['divgraphs'],
                                        children=[                                        
                                            dcc.Graph(id='ganttpersoon'),
                                            ]
                                        ),
                                    ]
                                ),                                
                            ]
                        ),
                    dcc.Tab(
                        label='Data export',
                        style=globals['styles']['tabs'], 
                        children=[
                            html.Div(
                                className='tab3_div1',
                                style=globals['styles']['maindivs'],
                                children=[
                                    html.H3('Uitleg'),
                                    html.Div(
                                        style=globals['styles']['divgraphs'],
                                        children=[                                    
                                            dcc.Markdown('''Hieronder kan de data worden geëxporteerd. Via de buttons 'Export' downloadt je een excelbestand.'''),
                                            dcc.Markdown('''In het dashboard kun je met de knop 'Toggle columns' ook velden zichtbaar maken, om van tevoren te filteren. Kies dan de velden, filter daarna en klik op 'Export'.'''),
                                            ]
                                        ),
                                    ]
                                ),                             
                            html.Div(
                                className='tab3_div2',
                                style=globals['styles']['maindivs'],
                                children=[
                                    html.H4('Platte dump'),
                                    dcc.Markdown('Deze tabel laat de platte data zien, zoals in Trello gevuld.'),
                                    dash_table.DataTable(
                                        id='table_plattedump',
                                        
                                        columns=[{'name': i, 'id': i, 'type': data['dfs']['columntypes'].get(i), 'hideable': True} for i in data['dfs']['kaartendf'].columns if i in data['dfs']['columntypes'].keys()],
                                        data=data['dfs']['kaartendf'].to_dict('records'),
                                        hidden_columns=[i for i in data['dfs']['columntypes']],
                                        export_format='xlsx',
                                        export_headers='display',
                                        export_columns='all',
                                        filter_action="native",
                                        sort_action="native",
                                        sort_mode="multi",  
                                        style_table={'overflowX': 'scroll'},
                                        style_header={'backgroundColor': 'rgba(62,182,235,0.6)','color': 'black', 'fontWeight': 'bold', 'fontFamily': 'Arial'},
                                        style_cell = {'backgroundColor': 'rgba(62,182,235,0.2)', 'color': 'black','text-align': 'left', 'fontFamily': 'Arial', 'height': 'auto'},                                        
                                        )

                                    ]
                                ),
                            html.Div(
                                className='tab3_div3',
                                style=globals['styles']['maindivs'],
                                children=[
                                    html.H4('Uren per maand'),
                                    
                                    dcc.Markdown('Hieronder kan een export gemaakt worden van de uren zoals ze per maand zijn ingepland.'),
                                    dcc.Markdown('Ook hierin kan gefilterd worden. filter bijvoorbeeld in de maand naar keuze op >0 om alle kaarten die geen ingeplande uren hebben niet te tonen.'),                                    
                                    dash_table.DataTable(
                                        id='table_urenpermaand',
                                        columns=[{'name': i, 'id': i, 'type': data['dfs']['columntypesurenpermaand'].get(i), 'hideable': True} for i in data['dfs']['urenpermaand'].columns if i in data['dfs']['columntypesurenpermaand'].keys()],
                                        data=data['dfs']['urenpermaand'].to_dict('records'),
                                        hidden_columns=[i for i in data['dfs']['columntypesurenpermaand']],
                                        export_format='xlsx',
                                        export_headers='display',
                                        export_columns='all',
                                        filter_action="native",
                                        sort_action="native",
                                        sort_mode="multi",  
                                        style_header={'backgroundColor': 'rgba(62,182,235,0.6)','color': 'black', 'fontWeight': 'bold', 'fontFamily': 'Arial'},
                                        style_cell = {'backgroundColor': 'rgba(62,182,235,0.2)', 'color': 'black','text-align': 'left', 'fontFamily': 'Arial'},                                        
                                        )


                                    ]
                                ),                                
                            ]
                        ),
                    dcc.Tab(
                        label='Langetermijnplanning',
                        style=globals['styles']['tabs'],                         
                        children=[
                            html.Div(
                                className='maindivs',
                                style=globals['styles']['maindivs'],
                                children=[
                                    html.H3('Uitleg'),
                                    html.Div(
                                        style=globals['styles']['divgraphs'],
                                        children=[                                    
                                            dcc.Markdown('''In dit tabblad wordt een langetermijnplanning getoond.'''),
                                            dcc.Markdown('''De focus hierbij ligt vooral op de categorieen.'''),
                                            ]
                                        ),
                                    ]
                                ), 
                            html.Div(
                                className='maindivs',
                                style=globals['styles']['maindivs'],
                                children=[
                                    html.H4('Ingeplande uren per categorie'),
                                    dcc.Dropdown(
                                        style = globals['styles']['dropdowns'],
                                        id='dropdownurenpermaand',
                                        options=[{'label':name, 'value':name} for name in data['arrays'][config.get('Custom Field for Categories')] if name != None],
                                        multi=True,
                                        searchable=False,
                                        value = data['arrays'][config.get('Custom Field for Categories')]
                                        ),
                                    html.Div(
                                        style=globals['styles']['divgraphs'],
                                        children=[                                    
                                            dcc.Graph(id='urenpermaand')
                                           ]
                                        ),
                                    ]
                                ),
                            html.Div(
                                className='tab1_div3',
                                style=globals['styles']['maindivs'],
                                children=[
                                    html.H4('Nog in te plannen uren (per lijst)'),
                                    dcc.Markdown('''*Nieuw* zijn werkzaamheden die **nog niet** zijn besproken of ze worden gedaan.'''),
                                    dcc.Markdown('''*Wensenlijst* zijn werkzaamheden die **wel** zijn besproken, maar **geen prioriteit** hebben.'''),
                                    dcc.Markdown('''*Inplannen* zijn werkzaamheden die **moeten** gebeuren.'''),
                                    dcc.Markdown('''**NB:** Alleen werkzaamheden waarvan we een ureninschatting kunnen maken, worden getoond!'''),                                    
                                    html.Div(
                                        style=globals['styles']['divgraphs'],
                                        children=[
                                            dcc.Graph(
                                                id='graph_nietingepland',
                                                figure={'data': data['graphdata']['nietingepland'],
                                                        'layout': globals['graphlayouts']['bars']}                          
                                                )
                                            ]
                                        ),
                                    ]
                                ), 
                            html.Div(
                                className='tab1_div4',
                                style=globals['styles']['maindivs'],
                                children=[
                                    html.H4('Nog in te plannen uren (per epic)'),
                                    dcc.Markdown('''**NB:** Alleen werkzaamheden waarvan we een ureninschatting kunnen maken, worden getoond!'''),                                     
                                    html.Div(
                                        style=globals['styles']['divgraphs'],
                                        children=[                                    
                                            dcc.Graph(
                                                id='graph_nietingepland_epics',
                                                figure={'data': data['graphdata']['nietingeplandepics'],
                                                        'layout': globals['graphlayouts']['bars']}
                                                )      
                                            ]
                                        ),
                                    ]
                                ),                                                                   
                            ]
                        ), 
                    dcc.Tab(
                        style=globals['styles']['tabs'],  
                        label='Tactische planning',
                        children=[
                            html.Div(
                                className='maindivs',
                                style=globals['styles']['maindivs'],  
                                children=[
                                    html.H3('Uitleg'),
                                    dcc.Markdown('''In dit tabblad is een middellange termijnplanning te zien.'''),

                                    ]
                                ),
                            html.Div(
                                className='maindivs',
                                style=globals['styles']['maindivs'],  
                                children=[
                                    html.H4('Totalen'),
                                    dcc.Markdown('''Hieronder staan twee totaaloverzichten van de aankomende maanden.'''),
                                    dcc.Markdown('''De blauwe balk geeft de ingeplande uren weer. De streep geeft de beschikbare uren aan.'''),
                                    dcc.Markdown('''Het kleine getal eronder geeft aan hoeveel uren tekort/over zijn voor die maand.'''),
                                    html.Div(
                                        style=globals['styles']['divgraphs'],
                                        children=[
                                            dcc.Graph(
                                                figure=(data['graphdata']['gaugefig'])
                                                )
                                            ]
                                        )

                                    ]
                                ),
                            html.Div(
                                className='maindivs',
                                style=globals['styles']['maindivs'],  
                                children=[
                                    html.H4('Gantt'),
                                    dcc.Dropdown(
                                        style = globals['styles']['dropdowns'],
                                        id='dropdowngantttactisch',
                                        options=[{'label':j, 'value': i} for i,j in data['arrays']['threemonths']],
                                        multi=False,
                                        searchable=False,
                                        value = data['arrays']['threemonths'][0][0],
                                        ),
                                    html.Div(
                                        style=globals['styles']['divgraphs'],
                                        children=[
                                            dcc.Graph(id='gantttactisch'
                                                )
                                                
                                            ]
                                        )

                                    ]
                                ),
                            ]


                        ),
#                     dcc.Tab(
#                         style=globals['styles']['tabs'],  
#                         label='Configuratie',
#                         children=[
#                             html.Div(
#                                 className='maindivs',
#                                 style=globals['styles']['maindivs'],  
#                                 children=[
#                                     html.H3('Uitleg'),
#                                     dcc.Markdown('''Klik op de button hieronder om de huidige configuratie te downloaden.'''),
#                                     html.A(id='export_link', href='/dash/configuration/', children=[html.Button(id='export_button', type='button', children=['Export'])]),

#                                     dcc.Markdown('''Pas het bestand aan en upload deze hieronder.'''),
#                                     dcc.Upload(
#                                         id='configupload',
#                                         children=html.Div([
#                                             'Sleep het bestand of ',
#                                             html.A('selecteer het bestand')

#                                         ]),
#                                         style=globals['styles']['divgraphs'],
#                                         multiple=False,

#                                         ),
                             
#                                     html.Div(id='confirmupload',style=globals['styles']['divgraphs'])
#                                     ]
#                                 ),                           
#                             ]


#                         )                                                              
                    ]
                )
            ]
        )


#---! gantttactisch
@app.callback(Output('gantttactisch', 'figure'),
    [Input('dropdowngantttactisch','value')]

)

def update_gantttactisch(v1):
    if v1 != None: 
        if v1[4:] == '12':
            v1plus1 = str(int(v1[0:4])+1)+'01'
        else:
            v1plus1 = str(int(v1)+1)
        if v1[4:] == '01':
            v1min1 = str(int(v1[0:4])-1)+'12'
        else:
            v1min1 = str(int(v1)-1)
        if v1[4:] == '11':
            v1plus2 = str(int(v1[0:4])+1)+'01'
        else:
            v1plus2 = str(int(v1)+2)

        import random
        import numpy as np
        from operator import itemgetter
        ganttdata= []
        monthkey = int(v1)
        for i,j in data['kaarten'].items():
            if j['Status'] in ['Niet gestart', 'Doing', 'Blocked']:
                try:
                    if int(datetime.strftime(j['Begindatum'], '%Y%m')) <= monthkey and int(datetime.strftime(j['Einddatum'], '%Y%m')) >= monthkey:
                        if j['Begindatum'].date() < datetime.strptime(v1min1+'01','%Y%m%d').date():
                            start=datetime.strptime(v1min1+'01','%Y%m%d').date()
                        else:
                            start = j['Begindatum'].date()
                        if j['Einddatum'].date() >= datetime.strptime(v1plus2+'01','%Y%m%d').date():
                            eind=datetime.strptime(v1plus2+'01','%Y%m%d').date()
                        else:
                            eind =  j['Einddatum'].date()
                        ganttdata.append(dict(Task=j['Epic'],
                                            Start=start,
                                            Finish=eind,
                                            Resource=j['Naam'] + ' (uren: ' + str(round(data['urenperdagperkaart'][j['Naam']]['urenperperiode'][v1])) + ')'
                                            ))
                except:
                    pass
        result = sorted(ganttdata, key=itemgetter('Task'))
        rgb = []
        for c in range(len(result)):
            r = list(np.random.choice(range(256), size=3))
            s2 = ','.join(map(str,r))
            s1 = "rgb("
            s3 = ")"
            rgb.append(s1 + s2 + s3) 
        fig = ff.create_gantt(result, index_col='Resource', show_colorbar=True, group_tasks=False, showgrid_x=True, showgrid_y=True, colors=rgb)
        fig['layout'].update(paper_bgcolor='rgba(0,0,0,0)', 
                            plot_bgcolor='rgba(0,0,0,0)',)

        fig.add_trace(go.Scatter(mode='lines', x=[v1[0:4]+'-'+v1[4:]+'-01',v1[0:4]+'-'+v1[4:]+'-01'],y=[-1,len(result)], line={'shape': 'spline', 'color': 'black', 'width': 4}, showlegend=False))
        fig.add_trace(go.Scatter(mode='lines', x=[v1plus1[0:4]+'-'+v1plus1[4:]+'-01',v1plus1[0:4]+'-'+v1plus1[4:]+'-01'],y=[-1,len(result)], line={'shape': 'spline', 'color': 'black', 'width': 4}, showlegend=False))
        return fig               
    else:
        return {'data': [go.Pie()],'layout': go.Layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')}




# #---! configupload
# @app.callback(Output('confirmupload', 'children'),
#     [Input('configupload','contents')]

# )
# def confirm_upload(contents):
#     global newconfig
#     if contents is not None:
#         try:
#             newconfig = json.loads(base64.b64decode(contents[23:]).decode('ASCII'))
#             d = {}
#             for key,value in newconfig.items():
#                 if type(value) == list:
#                     d[key] = ''
#                     for i in value:
#                         if d[key] == '':
#                             d[key] += i 
#                         else:
#                             if i == value[-1]:
#                                 d[key] += (', '+i)
#                 else:
#                     d[key] = value

#             return html.Div(
#                 id='returneddiv',
#                 style=globals['styles']['divgraphs'],
#                 children=[ 
#                     dcc.Markdown('''Check hieronder of de juiste data is ingevoerd. Klik daarna daaronder op 'Opslaan'.'''),
#                     dash_table.DataTable(
#                         style_header={'backgroundColor': 'rgba(62,182,235,0.6)','color': 'black', 'fontWeight': 'bold', 'fontFamily': 'Arial'},
#                         style_cell = {'backgroundColor': 'rgba(62,182,235,0.2)', 'color': 'black','text-align': 'left', 'fontFamily': 'Arial'},                                                                
#                         columns=[{'name': 'Sleutel', 'id': 'Sleutel'}, {'name': 'Waarde', 'id': 'Waarde'}],
#                         data=[{'Sleutel': key, 'Waarde': value} for key, value in d.items()]

#                         ),
#                     html.Button(
#                         'Opslaan',
#                         id='save_button', 
#                         n_clicks=0
#                         ),
#                     html.Div(
#                         id='savedornot',
                        
#                         )
#                     ]
#                 )
#         except:
#             return html.H5('Het bestand is incorrect. Download en upload opnieuw!')

#     else:
#         return


# #---! save-button
# @app.callback(Output('savedornot','children'),
#     [Input('save_button','n_clicks'),])
# def save_fnct(n_clicks):
#     if n_clicks > 0:
#         with open('./configuration/configuration.txt','w') as outfile:
#             json.dump(newconfig, outfile, indent=4, sort_keys=True)
#         return 'Opgeslagen. Refresh de page.'
#     else:
#         return 


#---! ganttpersoon 
@app.callback(Output('ganttpersoon','figure'),
    [Input('dropdownganttpersoon','value'),
    Input('dropdownganttpersoonstatus', 'value')])
def update_ganttpersoon(v1, v2):
    ganttdata = []
    for i,j in data['kaarten'].items():
        if j[config.get('Custom Field for Person')] == v1 and j['Status'] != 'Archived' and j['Status'] in v2:
            try:
                ganttdata.append(dict(Task=j['Naam'],
                                      Start=j[config.get('Custom Field for Starting date')].date(),
                                      Finish = j[config.get('Custom Field for Ending date')].date(),
                                      Resource=j['Epic']
                                     ))
            except:
                pass
    if ganttdata != []:
        fig = ff.create_gantt(ganttdata, index_col='Resource', show_colorbar=True, showgrid_x=True, showgrid_y=True)
        fig['layout'].update(paper_bgcolor='rgba(0,0,0,0)', 
                            plot_bgcolor='rgba(0,0,0,0)',)
        return fig               
    else:
        return {'data': [go.Pie()],'layout': go.Layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')}


    



#---! ganttepics
@app.callback(Output('ganttepics','figure'),
    [Input('dropdownganttepics','value')])
def update_ganttepics(value):
    ganttdata = []
    for i,j in data['kaarten'].items():
        if j['Epic'] == value and j['Status'] != 'Archived':
            try:
                ganttdata.append(dict(Task=j['Naam'],
                                      Start=j[config.get('Custom Field for Starting date')].date(),
                                      Finish = j[config.get('Custom Field for Ending date')].date(),
                                      Resource=j['Status']
                                     ))
            except:
                pass
    if ganttdata != []:
        fig = ff.create_gantt(ganttdata, index_col='Resource', show_colorbar=True, showgrid_x=True, showgrid_y=True)
        fig['layout'].update(paper_bgcolor='rgba(0,0,0,0)', 
                            plot_bgcolor='rgba(0,0,0,0)',)
        return fig               
    else:
        return {'data': [go.Pie()],'layout': go.Layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')}


    

#---! urenpermaand callback
@app.callback(Output('urenpermaand', 'figure'),
    [Input('dropdownurenpermaand', 'value')]
    )
def update_urenpermaand(value):
    layout = go.Layout(paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis={'title': 'Datum', 'gridcolor': 'gray'},
                        yaxis={'title': 'Ingeplande uren', 'gridcolor': 'gray'})
    bars = []
    if 'Regulier werk' in value:
            yaxis = []
            for i in data['arrays']['perioden']:
                yaxis.append(round(sum([value['urenperperiode'][i] for value in data['urenperdagperkaart'].values() if value[config.get('Custom Field for Categories')] == 'Regulier werk']),0))
            bars.append(dict(x=data['arrays']['xaxis_months'],
                             y=yaxis,
                             name='Regulier werk',
                            line = {'shape': 'spline', 'smoothing': 0.4},
                            mode='lines+markers',
                            marker= {'symbol': 'triangle-up-open', 'size': 10},
                            stackgroup='one',                             
                            ))
                            
        
    for categorie in data['arrays'][config.get('Custom Field for Categories')]:
        if categorie in value and categorie != 'Regulier werk':
            if categorie == None:
                categorienaam = 'Geen categorie'
            else:
                categorienaam = categorie
            yaxis = []
            for i in data['arrays']['perioden']:
                yaxis.append(round(sum([value['urenperperiode'][i] for value in data['urenperdagperkaart'].values() if value[config.get('Custom Field for Categories')] == categorie]),0))
            bars.append(dict(x=data['arrays']['xaxis_months'],
                             y=yaxis,
                             name=categorienaam,
                            line = {'shape': 'spline', 'smoothing': 0.4},
                            mode='lines+markers',
                            marker= {'symbol': 'triangle-up-open', 'size': 10},
                            stackgroup='one',                             
                            ))
    yaxis = []
    for i in data['arrays']['perioden']:
        yaxis.append(round(sum([value['urenperperiode'][i] for value in data['beschikbareuren'].values()]),0))
    bars.append(dict(name='Totaal beschikbare uren',
        mode = 'lines',
        x = data['arrays']['xaxis_months'],
        y = yaxis,
        size=10,
        line = {'shape': 'spline', 'smoothing': 0.3, 'width':6, 'color': 'black'},
        
    ))    
    
            
            
    return {
         'data': bars,
         'layout': layout}

#--! App routes

@app.server.route("/dash/configuration/")
def download_file():

    return flask.send_file('./configuration/configuration.txt',
        attachment_filename="configuration.txt",
        as_attachment=True,
        cache_timeout=0
    )







#--! Check if this is the main app and if so, run Dash!
if __name__ == '__main__':
    app.run_server(debug=False,host='0.0.0.0', port=8050)
    

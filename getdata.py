#!/usr/bin/env python
# coding: utf-8

# In[8]:



import requests,json,os, pprint,requests
import pandas as pd
from datetime import date,datetime,timedelta
import copy


configurationfile = './configuration/configuration.txt'
credentialsfile = './configuration/credentials.txt'

def createfolders():
    try:
        os.stat('./configuration')
    except:
        os.mkdir('./configuration')
    try:
        os.stat('./data')
    except:
        os.mkdir('./data')
createfolders()

with open('credentialsoptions.txt') as json_file:
    credentialsoptions = json.load(json_file)
with open('configoptions.txt') as json_file:
    configoptions = json.load(json_file)

def loadconfig():
    global configfound
    global credentialsfound
    global config
    global credentials
    if os.path.exists(configurationfile):
        with open(configurationfile) as json_file:
            config = json.load(json_file)
        configfound = True
    else:
        config = {}
        for i,j in configoptions.items():
            config[i] = j
            configfound = False

    if os.path.exists(credentialsfile):
        with open(credentialsfile) as json_file:
            credentials = json.load(json_file)
        credentialsfound = True
    else:
        credentials = {}
        for i,j in credentialsoptions.items():
            credentials[i] = j
        credentialsfound=False
loadconfig()


def updateconfig(file,olddict,newdict):
    ans = input('Old or no ' + file[16:] + ' found. Update now? (Y/N)')
    if ans.upper() == 'Y':
        print('This is your old config:')
        pprint.pprint(olddict)
        newconfig = {'Script options': {}}
        newconfig['Version'] = newdict.get('Version')
        newconfig['__Comment'] = newdict['__Comment']
        keystoupdate = []
        for i,j in newdict.items():
            if not i in olddict.keys():
                keystoupdate.append(i)
        for i,j in olddict.items():
            if type(j) == dict:
                for k,l in j.items():
                    if l == True:
                        newconfig[i][k] = True
                    else:
                        keystoupdate.append(k)
            elif type(j) == list:
                if j == []:
                    keystoupdate.append(i)
                else:
                    newconfig[i] = j
            else:
                if j != '':
                    newconfig[i] = j
                else:
                    keystoupdate.append(i)
        for i,j in newdict.items():
            if type(j) == list:
                if i in keystoupdate:
                    newconfig[i] = []
                    value = input('Give the number of lists to add for the status '+i)
                    if value != '0':
                        try:
                            x = int(value)
                        except:
                            x = int(input('Not an integer. Please try again!'))
                        count = 1
                        while count <= x:
                            newconfig[i].append(input('Give the name of one list each time for the status ' + i))
                            count += 1
            elif type(j) == dict:
                newconfig[i] = {}
                for k,l in j.items():
                    try:
                        if k not in olddict['Script options'].keys():
                            keystoupdate.append(k)
                    except:
                        keystoupdate.append(k)
                    if k in keystoupdate:
                        answer = input(k + ' (Y/N)').upper()
                        if answer == 'Y':
                            newconfig[i][k] = True
                        else:
                            newconfig[i][k] = False
            else:
                if i in keystoupdate:
                    newconfig[i] = input(i)
        with open(file, 'w') as outfile:
            json.dump(newconfig, outfile, indent=4, sort_keys=True)




try:
    version = float(config['Version'])
except:
    version = 0.0
if version == 0.0 or version < float(configoptions['Version']) or configfound == False:
    updateconfig(configurationfile, config, configoptions)
    loadconfig()
try:
    version = float(credentials['Version'])
except:
    version = 0.0
if version == 0.0 or version < float(credentialsoptions['Version']) or credentialsfound == False:
    updateconfig(credentialsfile,credentials, credentialsoptions)
    loadconfig()


keys = "key="+credentials.get('API key')+"&token="+credentials.get('API token')
trello_base_url = "https://api.trello.com/1/"
board_url = trello_base_url+"boards/"+config.get('Board ID')
url_cards = board_url+"?cards=all&card_pluginData=true&card_attachments=true&card_customFieldItems=true&filter=all&"+keys
url_lists = board_url+"/lists?filter=all&"+keys
url_customfields = board_url+"/customFields?"+keys
url_labels = board_url+"/labels?"+keys
url_members = board_url+"/members?"+keys



board = json.loads(json.dumps(requests.get(url_cards).json()))
lists = json.loads(json.dumps(requests.get(url_lists).json()))
customfields = json.loads(json.dumps(requests.get(url_customfields).json()))
labels = json.loads(json.dumps(requests.get(url_labels).json()))
members = json.loads(json.dumps(requests.get(url_members).json()))
cards = board['cards']


def dateCalc(date):
    newdate = datetime.strptime(date[0:19],'%Y-%m-%dT%H:%M:%S')
    return newdate


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


chosenlists = []
for i in config.get('Not Started'):
    chosenlists.append(i)
chosenlists.extend(config.get('Blocked'))
chosenlists.extend(config.get('Doing'))
chosenlists.extend(config.get('Done'))
if config['Script options']['Calculate hours'] == True:
    for i in config.get('Epics'):
        chosenlists.append(i)
    for i in config.get('Always continuing'):
        chosenlists.append(i)
    for i in config.get('List with Epics Done'):
        chosenlists.append(i)


def idtodate(cardid):
    hex = cardid[0:8]
    timestamp = int(hex,16)
    timedate = datetime.fromtimestamp(timestamp)
    return timedate


kaarten = {}
for i in cards:
    kaarten[i['id']] = {'name': i['name'],
                        'cardid': i['id'],
                        'idlist': i['idList'],
                        'customfields': i['customFieldItems'],
                        'created': idtodate(i['id']),
                        'labels': {},
                        'members': {},
                        'sjabloon': i['isTemplate'],
                        'due': None,
                        'closed': i['closed'],
                        'epic': None,
                        'epicid': None,
                        'attachments': {},
                        'shortUrl': i['shortUrl']
                       }
    for j in i['idMembers']:

        for k in members:

            if j == k['id']:
                    kaarten[i['id']]['members'][k['id']] = k['fullName']
    if i['due'] != None:
        kaarten[i['id']]['due'] = dateCalc(i['due'])
    for j in i['labels']:
        kaarten[i['id']]['labels'][j['id']] = j['name']
    for j in i['attachments']:
        try:
            if 'epicId=' in j['url']:
                start = j['url'].find('epicId=')+7
                end = j['url'].find('&attachmentId=')
                kaarten[i['id']]['epicid'] = j['url'][start:end]
        except:
            pass

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
                    
                    
epicIdNameCategory = []
for i,j in kaarten.items():
    epicIdNameCategory.append((j['cardid'],j['name'],j['Categorie']))                    
                    
                    
for i,j in kaarten.items():
    if j['epicid'] == None:
        j['epic'] = 'Geen epic'
        j['Category'] = None
    else:
        for k in epicIdNameCategory:
            if k[0] == j['epicid']:
                j['epic'] = k[1]
                j['Category'] = k[2]

                    
for i,j in kaarten.items():
    for k in lists:
        if j['idlist'] == k['id']: j['list'] = k['name']
    if j['list'] in config.get('Not Started'):
        j['status'] = 'Not Started'
    elif j['list'] in config.get('Doing'):
        j['status'] = 'Doing'
    elif j['list'] in config.get('Blocked'):
        j['status'] = 'Blocked'
    elif j['list'] in config.get('Done'):
        j['status'] = 'Done'
    elif j['list'] in config.get('Always continuing'):
        j['status'] = 'Always continuing'
    elif j['list'] in config.get('Epics'):
        j['status'] = 'Epics Doing'
    elif j['list'] in config.get('List with Epics Done'):
        j['status'] = 'Epics Done'
    else:
        j['status'] = 'Archived'
    del j['customfields']
    del j['idlist']



for i,j in kaarten.items():
    if j['closed'] == True and j['status'] != 'Done':
        j['status'] = 'Archived'


liststodelete = []
for i in lists:
    if i['name'] not in chosenlists:
        liststodelete.append(i['name'])

cardstodelete = []
for i,j in kaarten.items():
    if j['sjabloon'] == True:
        cardstodelete.append(i)
    elif j['list'] in liststodelete:
        cardstodelete.append(i)


hours = {}
for i,j in kaarten.items():
    if j['list'] == config.get('List for hours'):
        hours[j['name']] = {config['Custom Field for Starting date']: j[config['Custom Field for Starting date']], config['Custom Field for Ending date']: j[config['Custom Field for Ending date']], config['Custom Field with hours']: j[config['Custom Field with hours']]}


for i in cardstodelete:
    if i in kaarten:
        del kaarten[i]

                    
                    
                    


# In[9]:



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


# In[10]:



epics = {}
for i,j in kaarten.items():
    if j['list'] in config.get('Epics') or j['list'] in config.get('List with Epics Done'):
        epics[i] = j
        
epicdates = {}
for i,j in epics.items():
    epicdates[i] = {'Starts': [], 'Ends': [], 'hours': 0}
    for k,l in kaarten.items():
        if i == l['epicid']:
            if l[config.get('Custom Field for Starting date')] != None:
                epicdates[i]['Starts'].append(l[config.get('Custom Field for Starting date')])
            if l['Einddatum'] != None:
                epicdates[i]['Ends'].append(l[config.get('Custom Field for Ending date')])
            try:
                epicdates[i]['hours'] += int(l['Geplande uren'])
            except:
                pass
    if epicdates[i]['Starts'] != []:
        epicdates[i]['Starts'] = min(epicdates[i]['Starts'])
    else:
        epicdates[i]['Starts'] = None
    if epicdates[i]['Ends'] != []:
        epicdates[i]['Ends'] = max (epicdates[i]['Ends'])
    else:
        epicdates[i]['Ends'] = None        
for i,j in epics.items():
    for k,l in epicdates.items():
        if i == k:
            j['Begindatum'] = l['Starts']
            j['Einddatum'] = l['Ends'] 
            j['Geplande uren'] = l['hours']

jsonforallepics = copy.deepcopy(epics)


 

alldates = {'datesforlists': [], 'history': {'datum': [], 'periode': [], 'Months': []}, 'future': {'datum': [], 'periode': [], 'Months': []}, 'all': {'datum': [], 'periode': [], 'Months': []}}
listtimeline = {}
for i in dates:
    datekey = datetime.strptime(i,'%Y-%m-%d').date()
    alldates['all']['datum'].append(i)
    periode = i[0:4]+i[5:7]
    firstdayofmonth = i[0:4]+'-'+i[5:7]+'-01'
    alldates['all']['periode'].append(periode)
    alldates['all']['Months'].append(firstdayofmonth)
    if datekey <= now:
        alldates['history']['datum'].append(i)
        alldates['history']['periode'].append(periode)
        alldates['history']['Months'].append(firstdayofmonth)
        listtimeline[datekey] = {}
        
#         for k in historicallists:
#             listtimeline[datekey][k] = 0
#         for l,m in kaarten.items():
#             if m['list'] in chosenlists:
#                 if m['status'] != 'Archived':
#                     for n,o in m['movements'].items():
#                         if n.date() < datekey <= now:
#                             if o['listBefore'] != None:
#                                 listtimeline[datekey][o['listBefore']] -= 1
#                                 listtimeline[datekey][o['listAfter']] += 1
#                             else:
#                                 listtimeline[datekey][o['listAfter']] += 1
    else:
        alldates['future']['datum'].append(i)
        alldates['future']['periode'].append(periode)
        alldates['future']['Months'].append(firstdayofmonth)

alldates['all']['periode'] = list(dict.fromkeys(alldates['all']['periode']))
alldates['all']['Months'] = list(dict.fromkeys(alldates['all']['Months']))

    
# jsonlists = {}
# for i in historicallists:
#     jsonlists[i] = {'Datum': []}


# for i,j in listtimeline.items():
#     for k,l in j.items():
#         jsonlists[k]['Datum'].append(l)





allcardstimeline = {}
for i in alldates['all']['datum']:
    datekey = datetime.strptime(i,'%Y-%m-%d').date()
    allcardstimeline[i] = {}
    for k,l in kaarten.items():
        allcardstimeline[i][l['name']] = 0

        try:
            if l[config.get('Custom Field for Starting date')].date() < datekey <= l[config.get('Custom Field for Ending date')].date():
                start = l[config.get('Custom Field for Starting date')]
                stop = l[config.get('Custom Field for Ending date')]
                delta = stop - start
                hoursperday = int(l[config.get('Custom Field with hours')])/int(delta.days)

                allcardstimeline[i][l['name']] += hoursperday
        except:
            pass
jsonallcards = {}
for i,j in kaarten.items():
    jsonallcards[j['name']] = {'Datum': [],'Perioden': {},'epic': j['epic'], 'status': j['status']}
    for k,l in alldates['all'].items():
        if k == 'periode':
            for m in l:
                jsonallcards[j['name']]['Perioden'][m] = 0



for i,j in allcardstimeline.items():
    monthkey = i[0:4]+i[5:7]
    for k,l in j.items():
        jsonallcards[k]['Perioden'][monthkey] += l
        jsonallcards[k]['Datum'].append(l)
        
cardstodelete = []
        
for i,j in jsonallcards.items():
    j['periode'] = []
    for k,l in j.items():
        if k == 'Perioden':
            for m,n in l.items():
                j['periode'].append(n)
    del j['Perioden']
    del j['Datum']
    if sum(j['periode']) == 0:

        cardstodelete.append(i)
for i in cardstodelete:
    del jsonallcards[i]        
    
    
    
    
allepics = []
for j in epics.values():
    allepics.append(j['name'])
allepics = list(dict.fromkeys(allepics))

epictimeline = {}
for i in alldates['all']['datum']:
    datekey = datetime.strptime(i,'%Y-%m-%d').date()
    epictimeline[i] = {}
    for k in allepics:
        epictimeline[i][k] = 0

        try:
            if l['Begindatum'].date() < datekey <= l['Einddatum'].date():
                start = l[config.get('Custom Field for Starting date')]
                stop = l[config.get('Custom Field for Ending date')]
                delta = stop - start
                hoursperday = int(l[config.get('Custom Field with hours')])/int(delta.days)

                epictimeline[i][l['name']] += hoursperday
        except:
            pass

jsonepics = {}
for i in allepics:
    jsonepics[i] = {'Datum': [],'Perioden': {}}
    for j,k in alldates['all'].items():
        if j == 'periode':
            for l in k:
                jsonepics[i]['Perioden'][l] = 0

for i,j in epictimeline.items():
    monthkey = i[0:4]+i[5:7]
    for k,l in j.items():
        jsonepics[k]['Perioden'][monthkey] += l
        jsonepics[k]['Datum'].append(l)

for i,j in jsonepics.items():
    j['periode'] = []
    for k,l in j.items():
        if k == 'Perioden':
            for m,n in l.items():
                j['periode'].append(n)
    del j['Perioden']
     




allcategories = []

for i,j in customfields_dict.items():
    if i == 'list':
        for k,l in j.items():
            if l['name'] == config.get('Custom Field for Categories'):
                for m in l['options'].values():
                    allcategories.append(m) 

categoriestimeline = {}
for i in alldates['all']['datum']:
    datekey = datetime.strptime(i, '%Y-%m-%d').date()
    categoriestimeline[i] = {}
    for k in allcategories:
        categoriestimeline[i][k] = 0
        for m,n in kaarten.items():
            if k == n['Category']:
                try:
                    if n['Begindatum'].date() <= datekey <= n['Einddatum'].date():
#                         if (n['epic'] == 'Regulier beheer' and n['Category'] == 'Regulier werk') or (n['Category'] != 'Regulier werk'):
                            start = n[config.get('Custom Field for Starting date')]
                            stop = n[config.get('Custom Field for Ending date')]
                            delta = stop - start
                            hoursperday = int(n[config.get('Custom Field with hours')])/int(delta.days)
                            categoriestimeline[i][k] += hoursperday
                except:
                    pass
jsoncategories = {}
for i in allcategories:
    jsoncategories[i] = {'Datum': [], 'Perioden': {}}
    for j,k in alldates['all'].items():
        if j == 'periode':
            for l in k:
                jsoncategories[i]['Perioden'][l] = 0
for i,j in categoriestimeline.items():
    monthkey = i[0:4]+i[5:7]
    for k,l in j.items():
        jsoncategories[k]['Perioden'][monthkey] += l
        jsoncategories[k]['Datum'].append(l) 
for i,j in jsoncategories.items():
    j['periode'] = []
    for k,l in j.items():
        if k == 'Perioden':
            for m,n in l.items():
                j['periode'].append(n)
    del j['Perioden']
          
urentimeline = {}
for i in alldates['all']['datum']:
    datekey = datetime.strptime(i, '%Y-%m-%d').date()
    urentimeline[i] = {'totaal': 0}
    for k,l in hours.items():
        urentimeline[i][k] = 0
    for k,l in hours.items():
        if l[config.get('Custom Field for Starting date')].date() <= datekey <= l[config.get('Custom Field for Ending date')].date():
            hoursperday = int(l[config.get('Custom Field with hours')])/int(30.4)
            urentimeline[i][k] += hoursperday

for i,j in urentimeline.items():
    for k,l in j.items():
        if k != 'totaal':
            j['totaal'] += l

jsonuren = {'totaal': {'Datum': [], 'Perioden': {}}}
for i in alldates['all']['periode']:
    jsonuren['totaal']['Perioden'][i] = 0
for i in hours.keys():
    jsonuren[i] = {'Datum': [], 'Perioden': {}}
    for j,k in alldates['all'].items():
        if j == 'periode':
            for l in k:
                jsonuren[i]['Perioden'][l] = 0
for i,j in urentimeline.items():
    monthkey = i[0:4]+i[5:7]
    for k,l in j.items():
        jsonuren[k]['Perioden'][monthkey] += l
        jsonuren[k]['Datum'].append(l)
for i,j in jsonuren.items():
    j['periode'] = []
    for k,l in j.items():
        if k == 'Perioden':
            for m,n in l.items():
                j['periode'].append(n)
    del j['Perioden']            

    
    
    
listsnotdone = []
for i in chosenlists:
    if i in config.get('Not Started'):
        listsnotdone.append(i)
nietingeplandeuren = {}
for i in listsnotdone:
    nietingeplandeuren[i] = {}
    for j in allcategories:
        nietingeplandeuren[i][j] = 0
for i,j in kaarten.items():
    if j['list'] in listsnotdone:
        if j[config.get('Custom Field for Starting date')]==None or j[config.get('Custom Field for Ending date')]==None:

            try:
                nietingeplandeuren[j['list']][j['Category']] += int(j[config.get('Custom Field with hours')])

            except:
                pass
jsonnietingepland = {'labels': [],'data':{}}
for i in listsnotdone:
    jsonnietingepland['labels'].append(i)
    for j in allcategories:
        jsonnietingepland['data'][j] = []
    for j,k in nietingeplandeuren.items():
        for l,m in k.items():
            jsonnietingepland['data'][l].append(m)

    
    
    
cardswithfields = {}

for i,j in kaarten.items():
    cardswithfields[i] = j
    if j['labels'] != {}:
        cardswithfields[i]['Labels'] = ''
        for m,n in j['labels'].items():
            if cardswithfields[i]['Labels'] == '':
                cardswithfields[i]['Labels'] = n
            else:
                cardswithfields[i]['Labels'] = cardswithfields[i]['Labels']+', '+ n
    else:
        cardswithfields[i]['Labels'] = ''
    if j['members'] != {}:
        cardswithfields[i]['Members'] = ''
        for m,n in j['members'].items():
            if cardswithfields[i]['Members'] == '':
                cardswithfields[i]['Members'] = n 
            else:
                cardswithfields[i]['Members'] = cardswithfields[i]['Members']+ ', '+n
    else:
        cardswithfields[i]['Members'] = ''
for x,y in cardswithfields.items():
    del y['attachments']
    del y['members']
    del y['labels']
    del y[config.get('Custom Field for Categories')]
    
    del y['epicid']

belangrijkekaarten = {'upcoming': {}, 'due': {}, 'epics': {}, 'cardswoepic': {}, 'epicswocat': {}, 'cardswometa': {}}
upcoming = {}
for i,j in cardswithfields.items():
    if j['status'] in ['Not Started','Doing','Blocked']:
        try:
            if  now - timedelta(days=7) <= j[config.get('Custom Field for Ending date')].date() <= now:
                belangrijkekaarten['due'][i] = j
        except:
            pass
        if j['status'] in ['Not Started']:
            try:
                if  j[config.get('Custom Field for Starting date')].date() <= now + timedelta(days=7):
                    belangrijkekaarten['upcoming'][i] = j
            except:
                pass
        if j['epic'] == None:
            belangrijkekaarten['cardswoepic'][i] = j
        if j['status'] in ['Doing','Blocked']:
            try:
                test = j[config.get('Custom Field for Starting date')] - j[config.get('Custom Field for Ending date')]
                test = int(j[config.get('Custom Field with hours')])
            except:
                belangrijkekaarten['cardswometa'][i] = j
    if j['list'] in config.get('Epics') or j['list'] in config.get('List with Epics Done'):
        belangrijkekaarten['epics'][i] = j
        if j['Category'] == None:
            belangrijkekaarten['epicswocat'][i] = j
jsonimportantcards = {}
for k,l in belangrijkekaarten.items():
    jsonimportantcards[k] = {}
    for i,j in l.items():
        try:
            del j['listmovements']
        except:
            pass
        try:
            del j['movements']
        except:
            pass
        jsonimportantcards[k][i] = {}
        for m,n in j.items():
            if type(n) == datetime:
                jsonimportantcards[k][i][m] = 'date, ' + n.strftime("%Y-%m-%d, %H:%M:%S")
            else:
                jsonimportantcards[k][i][m] = n
                
## NEW

for i,j in belangrijkekaarten['epics'].items():
    j[config.get('Custom Field with hours')] = 0
    for k,l in kaarten.items():
        if j['name'] == l['epic']:
            try:
                j[config.get('Custom Field with hours')] += int(l[config.get('Custom Field with hours')])
            except:
                pass
            
            
            
jsonimportantcards = {}
for k,l in belangrijkekaarten.items():
    jsonimportantcards[k] = {}
    for i,j in l.items():
        try:
            del j['listmovements']
        except:
            pass
        try:
            del j['movements']
        except:
            pass
        jsonimportantcards[k][i] = {}
        for m,n in j.items():
            if type(n) == datetime:
                jsonimportantcards[k][i][m] = 'date, ' + n.strftime("%Y-%m-%d, %H:%M:%S")
            else:
                jsonimportantcards[k][i][m] = n
                
                
                
jsonstatuses = []
for i,j in kaarten.items():
    jsonstatuses.append(j['status'])
jsonstatuses = list(dict.fromkeys(jsonstatuses))
jsonstatusesremove = ['Archived','Epics Doing', 'Epics Done', 'Always continuing']
for i in jsonstatusesremove:
    try:
        jsonstatuses.remove(i)
    except:
        pass
    
    
jsonmeta = {'listswithstatus': {'Doorlopend': [],
            'Blocked': [],
            'Niet gestart': [],
            'Doing': [],
            'Done': [],
            'Epics': []
           }}

for i in chosenlists: 
    if i in config.get('Always continuing'):
        jsonmeta['listswithstatus']['Doorlopend'].append(i)
    elif i in config.get('Not Started'):
        jsonmeta['listswithstatus']['Niet gestart'].append(i)
    elif i in config.get('Blocked'):
        jsonmeta['listswithstatus']['Blocked'].append(i)
    elif i in config.get('Doing'):
        jsonmeta['listswithstatus']['Doing'].append(i)
    elif i in config.get('Done'):
        jsonmeta['listswithstatus']['Done'].append(i)
    elif i in config.get('Epics') or i in config.get('List with Epics Done'):
        jsonmeta['listswithstatus']['Epics'].append(i)
        
        
        

jsoncards = {}
for i,j in kaarten.items():
    try:
        del j['listmovements']
    except:
        pass
    try:
        del j['movements']
    except:
        pass

    jsoncards[i] = {}
    for k,l in j.items():
        if type(l) == datetime:
            jsoncards[i][k] = 'date, ' + l.strftime("%Y-%m-%d, %H:%M:%S")
        else:
            jsoncards[i][k] = l

jsonallepics = {}
for i,j in jsonforallepics.items():
    try:
        del j['listmovements']
    except:
        pass
    try:
        del j['movements']
    except:
        pass

    jsonallepics[i] = {}
    for k,l in j.items():
        if type(l) == datetime:
            jsonallepics[i][k] = 'date, ' + l.strftime("%Y-%m-%d, %H:%M:%S")
        else:
            jsonallepics[i][k] = l   
            
# def dumpjson(file, data):
#     with open('./data/'+file, 'w') as outfile:
#         json.dump(data, outfile, sort_keys=True) 

# dumpjson('kaarten.json',jsoncards)
# dumpjson('dates.json',alldates)
# dumpjson('epics.json',jsonepics)
# # dumpjson('lists.json',jsonlists)
# dumpjson('categories.json',jsoncategories)
# dumpjson('uren.json',jsonuren)
# dumpjson('nietingepland.json',jsonnietingepland)
# dumpjson('belangrijkekaarten.json',jsonimportantcards)
# dumpjson('allcards.json',jsonallcards)
# dumpjson('statuses.json',jsonstatuses)
# dumpjson('meta.json',jsonmeta)
# dumpjson('allepics.json',jsonallepics)


# string = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
# text_file = open("./data/date.txt", "w")
# n = text_file.write(string)
# text_file.close()











    


# In[6]:


# %time
# jsoncards = {}
# for i,j in kaarten.items():
#     try:
#         del j['listmovements']
#     except:
#         pass
#     try:
#         del j['movements']
#     except:
#         pass

#     jsoncards[i] = {}
#     for k,l in j.items():
#         if type(l) == datetime:
#             jsoncards[i][k] = 'date, ' + l.strftime("%Y-%m-%d, %H:%M:%S")
#         else:
#             jsoncards[i][k] = l

# jsonallepics = {}
# for i,j in jsonforallepics.items():
#     try:
#         del j['listmovements']
#     except:
#         pass
#     try:
#         del j['movements']
#     except:
#         pass

#     jsonallepics[i] = {}
#     for k,l in j.items():
#         if type(l) == datetime:
#             jsonallepics[i][k] = 'date, ' + l.strftime("%Y-%m-%d, %H:%M:%S")
#         else:
#             jsonallepics[i][k] = l   
            
# def dumpjson(file, data):
#     with open('./data/'+file, 'w') as outfile:
#         json.dump(data, outfile, sort_keys=True) 

# dumpjson('kaarten.json',jsoncards)
# dumpjson('dates.json',alldates)
# dumpjson('epics.json',jsonepics)
# # dumpjson('lists.json',jsonlists)
# dumpjson('categories.json',jsoncategories)
# dumpjson('uren.json',jsonuren)
# dumpjson('nietingepland.json',jsonnietingepland)
# dumpjson('belangrijkekaarten.json',jsonimportantcards)
# dumpjson('allcards.json',jsonallcards)
# dumpjson('statuses.json',jsonstatuses)
# dumpjson('meta.json',jsonmeta)
# dumpjson('allepics.json',jsonallepics)


# string = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
# text_file = open("./data/date.txt", "w")
# n = text_file.write(string)
# text_file.close()


import os, json, requests
from os import listdir
from datetime import date, datetime, timedelta


with open('./configuration/credentials.txt') as json_file:
    credentials = json.load(json_file)
    
with open('./configuration/configuration.txt') as json_file:
    config = json.load(json_file)
    
    
def get_data():
    with open('./data/date.txt', 'r') as f2:
        dateofdata = f2.read()

    daterefreshed = 'Refreshen. Laatste refresh: ' + datetime.strftime(datetime.strptime(dateofdata,'%Y-%m-%d, %H:%M:%S'),'%A %-d %B, %H:%M')
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

get_data()

for i,j in data['kaarten'].items():
    try:
        j['datedone'] = datetime.strptime(j['datedone'][6:16], '%Y-%m-%d').date()
    except:
        pass

maxdate = datetime.now().date() - timedelta(days = int(config['Maximum days a card can be in Done']))

for i,j in data['kaarten'].items():
    if j['status'] == 'Done' and j['closed'] == False and j['datedone']<maxdate:
        url = "https://api.trello.com/1/cards/"+i
        querystring = {"closed":"true","key":credentials.get('API key'),"token":credentials.get('API token')}
        resp = requests.request("PUT", url, params=querystring)
        resp

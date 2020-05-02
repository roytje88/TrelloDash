#!/usr/bin/env python
# coding: utf-8

#In[]
import os,json,shutil

# start setup
## load files
### set files locations
configurationfile = './configuration/configuration.txt'
credentialsfile = './configuration/credentials.txt'

### define funcions for loading and updating files
#In[]
## str
def question_str(i):
    answer = input('Add value for '+i+': ')
    return answer
## list
def question_list(i):
    print('List: multiple answers possible. End with "x"')
    answer = []
    listitem = ""
    while listitem != "x":
        listitem = input('Add listitem for '+i+' (end with "x"): ')
        answer.append(listitem)
    answer.remove("x")
    return answer
## bool
def question_bool(i):
        while True:
            answer = input('ADD VALUE FOR "'+str(i)+'"? (True/False) ')
            if answer == 'True':
                v = bool(answer)
                break
            elif answer == 'False':
                v = bool()
                break
            else:
                print("Value is not boolean. Try again.")
                continue
        return v

def question_per_type(i,t):
    if t == str:
        answer = question_str(i)
        print('ADDING VALUE FOR '+str(i)+': '+str(answer))
        return answer
    elif t ==list:
        answer = question_list(i)
        print('ADDIND LIST FOR '+str(i)+': '+str(answer))
        return answer
    elif t == bool:
        answer = question_bool(i)
        print('ADDING BOOLEAN FOR '+str(i)+': '+str(answer))
        return answer

def load_update(file, template):
    # load file
    with open(file) as json_file:
        c = json.load(json_file)
    # check if update is needed
    if c.keys() == template.keys():
        print(file+': No difference in keys. Only updating version value')
    else:
        # add new entries
        for i in template.keys():
            if c.get(i) == None:
                # To Do: debug iteration
                new = {i:question_per_type(i,type(template[i]))}
                c.update(new)
                print("Added: "+str(new))
        # remove removed entries
        remove = []
        for i in c.keys():
            if template.get(i) == None:
                remove.append(i)
        print(remove)
        for j in remove:
            c.pop(j)
            print("removed: "+i)
        print(file+": File is synced with new template, and values wil be added to file.")
    # copy version from config_template to config
    c['Version'] = template['Version']
    # write dictionary to file
    with open(file, 'w') as outfile:
        json.dump(c, outfile, indent=4, sort_keys=True)

def new_fill(file, template):
    #check if folder exists, githelse create it
    try:
        os.stat('./configuration')
    except:
        os.mkdir('./configuration')
    # update all valuea in template
    for i in template:
        # itertate through entries, checking for type and adjusting entry methode
        if i == '__Comment' or i == 'Version':
            print('skipping '+i)
        else:
            if isinstance(template[i],dict):
                for k,v in template[i].items():
                    template[i][k] = question_per_type(k,type(v))
            else:
                template[i] = question_per_type(i,type(template[i]))
    # write values to file
    with open(file, 'w') as outfile:
        json.dump(template, outfile, indent=4, sort_keys=True)

def load(file):
    if file == configurationfile:
        with open('./templates/configuration_template.txt') as json_file:
            template = json.load(json_file)
    else:
        with open('./templates/credentials_template.txt') as json_file:
            template = json.load(json_file)

    try:
        load_update(file, template)
    except:
        new_fill(file, template)
#In[]
# create, load or update files
load(configurationfile)
load(credentialsfile)
# done


# %%

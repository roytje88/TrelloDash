#!/usr/bin/env python
# coding: utf-8

#In[]
import os,json,shutil

# start setup
## set files locations
configurationfile = './configuration/configuration.txt'
credentialsfile = './configuration/credentials.txt'

## define funcions for loading and updating files
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

def update(c,template,file):
    # check if update is needed
    if c.keys() == template.keys():
        print(file+': No difference in keys. Only updating version value')
        return(c)
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
        print('Keys to remove: ', remove)
        for j in remove:
            c.pop(j)
            print("removed: "+j)
            print(file+": File is synced with new template, and values wil be added to file.")
        return(c)

def load_file(file):
    with open(file) as json_file:
        c = json.load(json_file)
    return c

def write_file(file, c):
    with open(file, 'w') as outfile:
        json.dump(c, outfile, indent=4, sort_keys=True)

def load_update(file, template):
    # backup existing file
    shutil.copy(file,file[:-3]+"bak")
    load_file(file)
    if file == configurationfile:
        # check if upgrade is needed
        if float(c['Version']) < 2:
           upgrade = template.copy()
           upgrade.pop('Board ID')
           upgrade.update({c['Board ID']:c.copy()})
           upgrade[c['Board ID']].pop('Version')
           upgrade[c['Board ID']].pop('Board ID')
           c = upgrade
        # itterate over boards
        for b in c:
            if b == 'Version':
                pass
            else:
                c[b] = update(c[b],template['Board ID'],file)
    else:
        c = update(c,template,file)
        
    # copy version from config_template to config
    c['Version'] = template['Version']
    # write dictionary to file
    write_file(file,c)

def new_fill(file, template):
    # copy template to dictionary for the file
    c = template.copy()
    # update all values in new dictionary
    c.pop('Version')
    for b,d in c.items():
        b = input('Board ID = ')
        # itertate through entries, checking for type and adjusting entry methode
        for i in d:
            if i == '__Comment':
                print('skipping '+i)
            else:
                if isinstance(d[i],dict):
                    for k,v in d[i].items():
                        d[i][k] = question_per_type(k,type(v))
                else:
                    d[i] = question_per_type(i,type(d[i]))
    return c

def add_board(file,template):
    c = load_file(file)
    c.update(new_fill(file, template))
    write_file(file,c)

def load(file):
    # set template
    if file == configurationfile:
        with open('./templates/configuration_template.txt') as json_file:
            template = json.load(json_file)
    else:
        with open('./templates/credentials_template.txt') as json_file:
            template = json.load(json_file)
    # load existing or creaing new file
    try:
        load_update(file, template)
    except:
        # create new file
        ## check if folder exists, githelse create it
        try:
            os.stat('./configuration')
        except:
            os.mkdir('./configuration')
        ## set dictionary for new file
        print(file+' was not found. Creating new one.')
        newfile = template.copy()
        newfile.pop('Board ID')
        print('Enter values for settings on promt.')
        newfile.update(new_fill(file, template))
        write_file(file,newfile)
        # write new file
    # add another Board?
    answer = 'yes'
    while answer == 'yes':
    	answer = input('Add another board? (yes/no)')
    	add_board(file,template)
#In[]
# create, load or update files
load(configurationfile)
load(credentialsfile)
# done


# %%

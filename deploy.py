#!/usr/bin/env python
# coding: utf-8

import os,json,shutil

# start setup
## load files
### set files locations
configurationfile = './configuration/configuration.txt'
credentialsfile = './configuration/credentials.txt'
### define funcions for loading and updating files

def load_update(file, template):
    # load file
    with open(file) as json_file:
        c = json.load(json_file)
    # check if update is needed
    if c['Version'] == template['Version']:
        print('No change in Version, so no update needed')
    elif c.keys() == template.keys():
        print('No difference in keys. Only updating version value')
    else:
        #add new entries
        for i in template.keys():
            if c.get(i) == None:
                new = {i:input("Add value for "+i+" as "+str(type(template.get(i))))}
                c.update(new)
                print("Added: "+str(new))
        #remove removed entries
        remove = []
        for i in c.keys():
            if template.get(i) == None:
                remove.append(i)
        print(remove)
        for j in remove:
            c.pop(j)
            print("removed: "+i)
    # copy version from config_template to config
    c['Version'] = template['Version']
    # write dictionary to file
    with open(file, 'w') as outfile:
        json.dump(c, outfile, indent=4, sort_keys=True)

def new_fill(file, template):
    #check if folder exists, else create it
    try:
        os.stat('./configuration')
    except:
        os.mkdir('./configuration')
    # update all valuea in template
    for i in template:
        # itetate through entries, checking for type and adjusting entry methode
        if isinstance(template[i],str):
            if i == "__Comment":
                print('skipping Comment')
                pass
            else:
                template[i] = input("Add value for "+i)
                print("VALUE ADDED FOR "+i+": "+template[i])
        elif isinstance(template[i],list):
            print('List: multiple answers possible. End with "x"')
            listitem = ""
            while listitem != "x":
                listitem = input('Add listitem for '+i+'. (end with "x")')
                template[i].append(listitem)
            template[i].remove("x")
            print("LIST ADDED FOR "+str(i)+": "+str(template[i]))
        elif isinstance(template[i],dict):
            for k,v in template[i]:
                print(k+":"+v)
                #To DO itterate over dictionary for answers
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

# create, load or update files
load(configurationfile)
load(credentialsfile)
# done

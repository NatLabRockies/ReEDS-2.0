#!/usr/bin/env python
# coding: utf-8

# In[1]:


#author: akarmaka
#This file processes the existing sources.csv file from the repo to check for any changes 
# and generates a new version of sources.csv containing details about each input and script files

import os
from os import walk
import csv
import pandas as pd
from datetime import datetime
import re

timestamp = datetime.now().strftime("%Y%m%d%H%M")


# Description holder file
desc_holder = 'sources.csv'
desc_holder = desc_holder.replace("\\","/")


#Setting correct path to main ReEDS folder        
current_path = os.getcwd()
current_path = current_path.replace("\\","/")
current_path = current_path.replace("/postprocessing/documentation_tools","")


#dir_path = get_correct_directory_path(root_folder_name)
dir_path = current_path.replace("\\","/")
            
desc_file_path = os.path.join(dir_path, desc_holder).replace("\\","/")



#file extensions dictionary to filter for
extensions = ['.csv', '.h5', '.xlsx', 'csv.gz'] #['.csv', '.py', 'csv.gz', '.gms', '.h5', '.r']

#folders to be excluded for source.csv population
omit_folders = ['.git', '.github', 'runs']

#Temp files to be ignored
ignore_files = ['sources_interim', 'sources_{timestamp}']
timestamp_pattern = re.compile(r'^sources_\d{12}$')



descriptions = {}
indices = {}
citations = {}
dollar_year = {}
filetypes = {}

        
#Use for reading sources.csv if re-running the script!        
with open(desc_file_path, "r") as csv_file:
    read = csv.DictReader(csv_file)
    for row in read:
        file_loc = row["FileName_new"] 
        ext = row["FileExtension"]
        rel_path = row["RelativeFilePath"]
        #full_path = row["FullFilePath"]
        description = row["Description_new"]
        index = row["Indices"]
        dollar_yr = row["DollarYear"]
        citation = row["Citation"]
        
        filetype = row["type"]
        descriptions[rel_path] = description
        indices[rel_path] = index
        citations[rel_path] = citation
        dollar_year[rel_path] = dollar_yr
        filetypes[rel_path] = filetype



#Saving the latest sources.csv for the interim
interim_sources_csv = "sources_interim.csv"
interim_sources_csv_path = os.path.join(dir_path, interim_sources_csv).replace("\\","/")


#Open csv file to store new sources.csv data
with open(interim_sources_csv_path, "w", newline="") as csv_file:
    writer = csv.writer(csv_file)
    
    #Specifying headers
    writer.writerow(["RelativeFilePath", "RelativeFolderPath", "FileName_new", "FileExtension", "Description_new", "Indices", "DollarYear", "Citation", "type"])
    
    data = []
    #To navigate entire directory and subdirectories within it
    for root, dirs, files in os.walk(dir_path, topdown=True):
        
        dirs[:] = [d for d in dirs if d not in omit_folders]

        files.sort(key=str.casefold)
        
        for file_name in files:
            
            #Store file paths
            file_path = os.path.join(root, file_name)
            file_path = file_path.replace("\\", "/")
                       
            #Store relative paths
            relative_path = os.path.relpath(file_path, dir_path)
            relative_path = "\\"+ relative_path
            relative_path = relative_path.replace("\\", "/")
            
            rel_folder_path = os.path.dirname(relative_path).replace("\\", "/")

            #Store file names and their respective extensions
            file_name, file_ext = os.path.splitext(file_name)

            if file_name in ignore_files or timestamp_pattern.match(file_name):
                continue

            #Filter files based on extensions present in our dictionary
            if file_ext in extensions:
                
                description = descriptions.get(relative_path, '')
                index = indices.get(relative_path, '')
                
                citation = citations.get(relative_path, '')
                dollar_yr = dollar_year.get(relative_path, '')
                filetype = filetypes.get(relative_path, '')

                data.append({"RelativeFilePath" : relative_path, "RelativeFolderPath": rel_folder_path, "FileName_new": file_name, "FileExtension": file_ext, "Description_new": description, "Index": index, "DollarYear": dollar_yr, "Citation": citation, "FileType": filetype})

    sorted_data = sorted(data, key=lambda x: x["RelativeFilePath"].casefold())

    for row in sorted_data:
        relative_file_path = row["RelativeFilePath"]
        relative_folder_path = row["RelativeFolderPath"]
        file_name = row["FileName_new"]
        file_ext = row["FileExtension"]
        description = row["Description_new"]
        index = row["Index"]
        dollar_yr = row["DollarYear"]
        citation = row["Citation"]
        filetype = row["FileType"]

        writer.writerow([relative_file_path, relative_folder_path, file_name, file_ext, description, index, dollar_yr, citation, filetype])
            

            
#Function to compare the 2 csv files to generate an added and deleted files list
def compare_sources_csv(old_csv_file, new_csv_file): #, tracking_file):
    with open(old_csv_file, 'r') as file:
        old_csv = csv.DictReader(file)
        old_files = [row['RelativeFilePath'] for row in old_csv]
        
    with open(new_csv_file, 'r') as file:
        new_csv = csv.DictReader(file)
        new_files = [row['RelativeFilePath'] for row in new_csv]

         
        added_files = set(new_files) - set(old_files)
        # tracked_and_added_files = added_files.intersection(tracked_files)

        
        deleted_files = set(old_files) - set(new_files)
        # tracked_and_deleted_files = set(deleted_files) - set(tracked_files)
        
        with open('local_sources_files_added.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['RelativeFilePath'])
            writer.writerows([[file_path] for file_path in added_files])
            
        with open('sources_files_deleted.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['RelativeFilePath'])
            writer.writerows([[file_path] for file_path in deleted_files])
            
#Call the compare function which compares local versions of old vs new sources.csv
compare_sources_csv(desc_file_path, interim_sources_csv_path)


#Read the tracked files list which contains all the files committed to the branch
tracked_file = "tracked_files_list.txt"
tracked_file_path = os.path.join(dir_path, tracked_file).replace("\\","/")

df_tracked_file_list = pd.read_csv(tracked_file_path, header=None, names=['RelativeFilePath'])
df_tracked_file_list['RelativeFilePath'] = df_tracked_file_list['RelativeFilePath'].str.replace('\\', '/', regex=False)
df_tracked_file_list['RelativeFilePath'] = "/" + df_tracked_file_list['RelativeFilePath']

df_sources_added_file = pd.read_csv("local_sources_files_added.csv", header=0)

#Function to compare local version of files added and the files committed
def compare_commited_files(tracked_sources_added, tracked_list):
    
    #Comparison to generate added and tracked files (tracked = committed)
    df_added_tracked_files = pd.merge(tracked_sources_added, tracked_list, on='RelativeFilePath', how='inner')
    df_added_tracked_files.to_csv('sources_files_added.csv', sep=',', encoding='utf-8', index=False)

    #Comparison to generate untracked files
    df_untracked_files = tracked_sources_added[~tracked_sources_added['RelativeFilePath'].isin(tracked_list['RelativeFilePath'])]
    df_untracked_files.to_csv('sources_untracked_files.csv', sep=',', encoding='utf-8', index=False)
    

#Call function to compare local vs committed versions of files
compare_commited_files(df_sources_added_file, df_tracked_file_list)



#Function to rename files
def rename_file(dir_path, old_sources_csv, new_sources_csv):
    old_file_path = os.path.join(dir_path, old_sources_csv).replace("\\", "/")
    
    new_file_path = os.path.join(dir_path, new_sources_csv).replace("\\", "/")
    
    os.rename(old_file_path, new_file_path)
    
    
    
#Old sources csv is the original sources.csv file
old_sources_csv = f"sources.csv"
#Adding a timestamp for log purposes and to compare with the latest sources.csv if needed
new_sources_csv = f"sources_{timestamp}.csv"

#Renaming original sources to sources file with a timestamp; to be kept for comparison if needed
rename_file(dir_path, old_sources_csv, new_sources_csv)

#Renaming latest sources.csv to take the place of the original sources.csv
rename_file(dir_path, interim_sources_csv, old_sources_csv)


#Removing the tracked files list generated by git comamnd
os.remove(tracked_file_path)




print("Added & Deleted Files list generated")

print("New Sources File list generated")


# In[ ]:





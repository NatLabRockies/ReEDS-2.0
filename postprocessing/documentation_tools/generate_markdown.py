#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
from os import walk
import csv
import pandas as pd
from datetime import datetime
import re

#Conversion of latest version of sources.csv to markdown/readme format


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


#Dataframe to store the newly generated sources.csv data
with open(desc_file_path, "r") as csv_file:
    reader = csv.DictReader(csv_file)
    data = list(reader)

sorted_data = sorted(data, key=lambda x: x["RelativeFilePath"].casefold())

#Dictionary to map folder names to respective files i.e create a hierarchy map  
folder_hierarchy = {}

#Group files by relative folder paths
for row in sorted_data:
    rel_file_path = row["RelativeFilePath"]
    rel_folder_path = row["RelativeFolderPath"]
    file_ext = row["FileExtension"]
    #folder_path = os.path.dirname(rel_file_path)
    if rel_folder_path == '/':
        rel_folder_path = ''
    file_name = row["FileName_new"]
    
    folders = rel_folder_path.split("/")
    current_folder = folder_hierarchy
    
    for folder in folders:
        if folder not in current_folder:
            current_folder[folder] = {}
            
        current_folder = current_folder[folder]
        
    if "files" not in current_folder:
        current_folder["files"] = []
        
    current_folder["files"].append((file_name, file_ext, rel_file_path))
    
#Generate readme for ReEDS 2.0 Sources files
main_readme_file = "sources_documentation.md"
main_readme_file_path = os.path.join(dir_path, main_readme_file).replace("\\","/")

#Open markdown file for entries
with open(main_readme_file_path, "w") as main_file:
    main_file.write(f"# ReEDS 2.0\n\n")
    main_file.write("## Table of Contents\n\n")
    
    #Function to generate Table of Contents using folder hierarchy
    def write_folder_hierarchy(folder_hierarchy, depth=1, parent_folder=None):
        if depth == 4:
            return
        indent = "  " * depth
        
        #Table of Contents - Folders and Subfolders (with anchor links)
        for folder, contents in folder_hierarchy.items():
            
            if folder != "files":
                #Generate anchor links
                
                anchor = os.path.join(parent_folder, folder).replace("\\", "/").replace("//", "/") if parent_folder else folder    #.lower().replace(" ", "-")
                
                anchor_link = f"<a name='{anchor}'></a>"
                
                header_level = min(depth+1, 10)
                #Write folder name with anchor link
                main_file.write(f"{indent}- {'#' + '#' * header_level} [{folder}](#{anchor}) \n")
                
                #Write recursively for contents of subfolder
                write_folder_hierarchy(contents, depth + 1, f"{parent_folder}/{folder}" if parent_folder else folder)
                
                        
    main_file.write(f"\n")    
    write_folder_hierarchy(folder_hierarchy)
    
    main_file.write(f"\n\n")
    main_file.write(f"## Input Files\n\n")
    
    #Write file entries for each folder
    def write_file_entries(file_entries, indent):
        
        for file_data in file_entries:
            file_name, file_ext, rel_file_path = file_data
            #Write file name with relative link
            rel_file_path = rel_file_path.replace(" ", "%20")
            main_file.write(f"{indent}- [{file_name}{file_ext}]({rel_file_path})\n")
            
            for row in data:
                if row["RelativeFilePath"] == rel_file_path:
                    description = row["Description_new"]
                    citation = row["Citation"]
                    indices = row["Indices"]
                    dollar_yr = row["DollarYear"]
                    file_type = row["type"]
                    
                    if file_type:
                        main_file.write(f"{indent}  - **File Type:** {file_type}\n")
                            
                    if description:
                        main_file.write(f"{indent}  - **Description:** {description}\n")
                        
                    if indices:
                        main_file.write(f"{indent}  - **Indices:** {indices}\n")
                        
                    if dollar_yr:
                        main_file.write(f"{indent}  - **Dollar year:** {dollar_yr}\n")
                        
                    if citation:
                        citation_link = f"[({citation})]"
                        main_file.write(f"\n{indent}  - **Citation:** {citation_link}\n\n")
            main_file.write(f"---\n\n")
                            
            
    #Write files present in folders
    if "files" in folder_hierarchy:
        write_file_entries(folder_hierarchy["files"], "")

    #Generate folder sections based on hierarchy and generate files within them    
    def write_folder_sections(folder_hierarchy, depth=1, parent_folder=None):
        for folder, contents in folder_hierarchy.items():
            
            if folder != "files":
                anchor = os.path.join(parent_folder, folder).replace("\\", "/").replace("//", "/") if parent_folder else folder
                
                anchor_link = f"<a name='{anchor}'></a>"
                header_level = min(depth + 1, 10)
                folder_path = f"{parent_folder}/{folder}" if parent_folder else folder
                folder_path = folder_path.replace(" ", "%20")
                folder_link = f"[{folder}]({folder_path})"
                main_file.write(f"\n{'#' * header_level} {folder_link} {anchor_link}\n") 
                
                
                if "files" in contents:
                    contents["files"].sort(key=lambda x: x[0].casefold())
                    write_file_entries(contents["files"], "  ")
                
                #Recursively writing sections of subfolders
                write_folder_sections(contents, depth + 1, folder_path)
                

                
    write_folder_sections(folder_hierarchy)
    
    if "files" in folder_hierarchy:
        main_file.write("\n## Files \n\n")
        write_file_entries(folder_hierarchy["files"], "")
        
print("Sources Documentation Markdown file has been generated!")
            

        


# In[ ]:





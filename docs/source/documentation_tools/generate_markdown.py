#!/usr/bin/env python
# coding: utf-8

# In[1]:

import os
import csv
import argparse
import re

def slugify(text: str) -> str:
    """
    Convert a string to a stable anchor id for markdow.
    Lowercase, replace spaces and slashes with hyphens, remove special characters except hyphens, and collapse multiple hyphens into one.

    Args:
        text (str): The input string to be converted.
    Returns:
        str: The slugified string suitable for use as a markdown anchor.
    """
    s = text.lower().strip().replace("\\", "/")
    s = s.replace(" ", "-").replace("/", "-")
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "section"

def is_url(s: str) -> bool:
    """
    Check if a string is a URL or mailto link.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string is a URL or mailto link, False otherwise.
    """
    return bool(re.match(r'^(https?://|mailto:)', (s or "").strip()))

def write_file_entries(data, main_file, file_entries, indent, githubURL):
    """
    Write markdown entries for files, including metadata such as description, citation, indices, dollar year, file type, and units.

    Args:
        data (list): List of dictionaries containing the file metadata.
        main_file (file object): The markdown file to write to.
        file_entries (list): List of file tuples (name, extension, relative path).
        indent (str): Indentation for markdown formatting.
        githubURL (str): Base GitHub URL for linking files.
    """
    for file_data in sorted(file_entries, key=lambda x: x[0].casefold()):
        file_name, file_ext, rel_file_path = file_data
        
        #Write file name with relative link (encode for link, keep raw for lookups)
        rel_file_path_raw = rel_file_path
        rel_file_path_link = rel_file_path_raw.replace(" ", "%20")
        main_file.write(f"{indent}- [{file_name}{file_ext}]({githubURL}{rel_file_path_link})\n")


        for row in data:
            if row["RelativeFilePath"] == rel_file_path_raw:
                description = row["Description_new"]
                citation = row["Citation"]
                indices = row["Indices"]
                dollar_yr = row["DollarYear"]
                file_type = row["Filetype"]
                unit = row["Units"]
                
                if file_type:
                    main_file.write(f"{indent}  - **File Type:** {file_type}\n")
                        
                if description:
                    main_file.write(f"{indent}  - **Description:** {description}\n")
                    
                if indices:
                    main_file.write(f"{indent}  - **Indices:** {indices}\n")
                    
                if dollar_yr:
                    main_file.write(f"{indent}  - **Dollar year:** {dollar_yr}\n")
                    
                if citation:
                    if is_url(citation):
                        main_file.write(f"{indent}  - **Citation:** [{citation}]({citation})\n")
                    else:
                        main_file.write(f"{indent}  - **Citation:** {citation}\n")

                if unit:
                    main_file.write(f"{indent}  - **Units:** {unit}\n\n")

                
                main_file.write("---\n\n")

#Function to generate Table of Contents using folder hierarchy
def write_folder_hierarchy(main_file, folder_hierarchy, depth=1, parent_folder=None):
    """
    Recursively write the folder hierarchy as a markdown table of contents with anchor links.

    Args:
        main_file (file object): The markdown file to write to.
        folder_hierarchy (dict): Nested dictionary representing the folder structure.
        depth (int, optional): Current depth in the folder hierarchy. Defaults to 1.
        parent_folder (str, optional): The parent folder path. Defaults to None.
    """
    if depth == 5:
        return
    indent = "  " * depth
    
    #Table of Contents - Folders and Subfolders (with anchor links)
    for folder in sorted([k for k in folder_hierarchy.keys() if k not in ("files", "")], key=str.casefold):
        contents = folder_hierarchy[folder]

        if folder != "files":

            anchor_src = os.path.join(parent_folder, folder).replace("\\", "/").replace("//", "/") if parent_folder else folder
            anchor = slugify(anchor_src)
            main_file.write(f"{indent}- [{folder}](#{anchor})\n")

            #Write recursively for contents of subfolder
            write_folder_hierarchy(main_file, contents, depth + 1, f"{parent_folder}/{folder}" if parent_folder else folder)


#Generate folder sections based on hierarchy and generate files within them    
def write_folder_sections(data, main_file,folder_hierarchy, githubURL, depth=1, parent_folder=None):
    """
    Recursively write markdown sections for each folder and its files, using the folder hierarchy.
    
    Args:
        data (list): List of dictionaries containing file metadata.
        main_file (file object): The markdown file to write to.
        folder_hierarchy (dict): Nested dictionary representing folder structure.
        githubURL (str): Base GitHub URL for file links.
        depth (int): Current depth in the folder hierarchy.
        parent_folder (str or None): Path to the parent folder.
    """
    for folder in sorted([k for k in folder_hierarchy.keys() if k not in ("files", "")], key=str.casefold):
        contents = folder_hierarchy[folder]
        
        if folder != "files":
            # Use stable slug anchors and plain headings (no link in heading)
            full_path = f"{parent_folder}/{folder}" if parent_folder else folder
            anchor = slugify(full_path)
            header_level = min(depth + 2, 6)  # start at ### under "## Input Files"
            # Put the anchor on its own line to avoid odd rendering
            main_file.write(f"\n<a id='{anchor}'></a>\n")
            main_file.write(f"{'#' * header_level} {full_path}\n\n")
                

            
            if "files" in contents:
                contents["files"].sort(key=lambda x: x[0].casefold())
                write_file_entries(data, main_file, contents["files"], "  ", githubURL)
            
            #Recursively writing sections of subfolders
            write_folder_sections(data, main_file, contents, githubURL, depth + 1, full_path)         


def main():
    """
    Main function to generate markdown documentation for ReEDS sources.
    Reads sources.csv, builds folder hierarchy, and writes a markdown file with file metadata and structure.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--githubURL', '-g', type=str, default='', help='base github url')
    parser.add_argument('--reedsPath', '-r', type=str, default='', help='path to reeds directory' )
    args = parser.parse_args()
    githubURL = args.githubURL
    reedsPath = args.reedsPath

    #Conversion of latest version of sources.csv to markdown/readme format

    # Description holder file
    desc_holder = 'sources.csv'
    desc_holder = desc_holder.replace("\\","/")


    #Setting correct path to main ReEDS folder        
    current_path = os.getcwd()
    if reedsPath != '':
        reeds_path = reedsPath
    else: 
        reeds_path = os.path.dirname(os.path.dirname(os.path.dirname(current_path)))
        reeds_path = reeds_path.replace("\\","/")

               
    desc_file_path = os.path.join(reeds_path, desc_holder).replace("\\","/")


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
        
        folders = [f for f in rel_folder_path.split("/") if f]
        current_folder = folder_hierarchy
        
        for folder in folders:
            if folder not in current_folder:
                current_folder[folder] = {}
                
            current_folder = current_folder[folder]
            
        if "files" not in current_folder:
            current_folder["files"] = []
            
        current_folder["files"].append((file_name, file_ext, rel_file_path))
        
    #Generate separate readme for ReEDS 2.0 Sources files
    main_readme_file = "sources_documentation.md"
    main_readme_file_path = os.path.join(reeds_path, main_readme_file).replace("\\","/")

    #Open markdown file for entries
    with open(main_readme_file_path, "w") as main_file:
        main_file.write("## Table of Contents\n\n")    

                            
        main_file.write("\n")    
        write_folder_hierarchy(main_file, folder_hierarchy)
        
        main_file.write("\n\n")
        main_file.write("## Input Files\n")
            
        #Write files present in folders
        if "files" in folder_hierarchy:
            write_file_entries(data, main_file, folder_hierarchy["files"], "", githubURL)
                    
        write_folder_sections(data, main_file, folder_hierarchy, githubURL)
        
        if "files" in folder_hierarchy:
            main_file.write("\n## Files \n\n")
            write_file_entries(data, main_file, folder_hierarchy["files"], "", githubURL)

    print("Sources Documentation Markdown file has been generated!")

if __name__ == "__main__":
    main()

# In[ ]:
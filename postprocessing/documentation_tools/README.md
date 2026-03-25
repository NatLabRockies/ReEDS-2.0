# How to Use Sources Documentation

1. Before running the .bat script, please ensure the sources.csv file is closed. If open, the script will be unable to replace the file and will throw an error.
2. Run **generate_sources_md_file.bat** script (for Mac and Linux users **generate_sources_md_file.sh**)located within the documentation_tools folder (ReEDS-2.0/postprocessing/documentation_tools).
3. This will run the first script **generate_new_sources.py**. generating a new **sources.csv** file at the top directory of the repository, please note,the existing sources.csv in your Repository root will be renamed to sources_{timestamp}.csv format. This can be deleted manually if no longer required; or can be held on to if required for comparison. Tree change files are generated in the documentations_tools folder to indicate files not included in the prior sources file (**sources_files_added.csv**), files removed from the prior sources file (**sources_files_deleted.csv**), and files not included in the sources file becasue they aren't committed (**sources_untracked_files.csv**). These change files should not be committed and can be deleted when no longer needed.
4. Once this has finished running, please proceed to update relevant fields in the *sources.csv* file
5. Once relevant fields have been updated, please save sources.csv and close it.
6. Run **generate_markdown.bat** (for Mac and Linux users **generate_markdown.sh**)located within the documentation_tools folder. This will generate a README file with all the Source files and their details for the Repository by running the script **generate_markdown.py**.
7. Commit and push the updated **sources.csv** and **sources_documenation.md** files.
---

## How to Update Relevant Fields in sources.csv
1. Once prompted by the .bat script, open **sources.csv** (found at the Repository root).
2. Using the Added Files List, **sources_files_added.csv** (found within the documentation_tools folder) which displays all the input files added by the user, enter relevant details in corresponding columns of **sources.csv**. Fields that do not apply can be left blank. Do not add new columns to sources.csv without also updating the scripts to support the expanded fields.
3. Save the sources.csv and close the file.

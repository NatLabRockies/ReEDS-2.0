#%% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import argparse
import pandas as pd
import numpy as np
import os
import sys
import datetime
# Time the operation of this script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


#%% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

def append_parent_rows(df, parent_tech, child_tech, tech_col='i'):
    #copy the rows with the parent technology
    copy_techs = df[df.isin([parent_tech]).any(axis=1)].copy()
    if copy_techs.empty:
        print(f'No rows found for parent technology {parent_tech}. Skipping.')
        return df

    # Change the technology column to the child technology
    copy_techs[tech_col] = child_tech
    return pd.concat([df, copy_techs], ignore_index=True)


def copy_parents(inputs_case):
    """
    Copy parent technologies of hybrid techs in the relevant files under the hybrid techs name, append the hybrid technology to the original dataframe and resave the files.
    """

    print('Copying and appending hybrid tech parent parameters for', inputs_case)

    sw = reeds.io.get_switches(inputs_case)
    sw['endyear'] = int(sw['endyear'])
    sw['sys_eval_years'] = int(sw['sys_eval_years'])

    # Import tech groups. Used to expand data inputs 
    # (e.g., 'UPV' expands to all of the upv subclasses, like upv_1, upv_2, etc)
    tech_groups = reeds.techs.import_tech_groups(os.path.join(inputs_case, 'tech-subset-table.csv'))

    # Set up scen_settings object
    scen_settings = reeds.financials.scen_settings(
        dollar_year=int(sw['dollar_year']), tech_groups=tech_groups, inputs_case=inputs_case,
        sw=sw)
    
    hybrid_types = [tech for tech in scen_settings.sw['GSw_HybridTypes'].split('|')]
    hybrid_gentechs = [tech for tech in scen_settings.sw['GSw_HybridGenTechs'].split('|')]

    hybrid_stortechs = [tech for tech in scen_settings.sw['GSw_HybridStorTechs'].split('|')]
    hybrid_techs = hybrid_gentechs + hybrid_stortechs
    
    # Loop only over top-level files (no recursion)
    for entry in os.scandir(inputs_case):
        if not entry.is_file():
            continue  # skip subdirectories
        fname = entry.name
        full_path = entry.path
        # Limit to tabular text files (adjust extensions as needed)
        if fname.lower().endswith('.csv'):
            try:
                df = pd.read_csv(full_path)
                # Skip file if it contains no hybrid tech references
                if not df.isin(hybrid_techs).any().any():
                    continue
                
                # Determine which column contains the technology names in hybrid_techs
                tech_col = None
                for col in df.columns:
                    if df[col].isin(hybrid_techs).any():
                        tech_col = col
                        break
                
            except Exception as e:
                print(f'Error processing {full_path}: {e}')





#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================
if __name__ == '__main__':

    #%% Parse arguments
    parser = argparse.ArgumentParser(description="copy_parents.py")
    parser.add_argument("reeds_path", help="ReEDS-2.0 directory")
    parser.add_argument("inputs_case", help="ReEDS-2.0/runs/{case}/inputs_case directory")
    
    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )

    #%% Run it
    tic = datetime.datetime.now()

    copy_parents(inputs_case)

    reeds.log.toc(tic=tic, year=0, process='input_processing/copy_parents.py', 
        path=os.path.join(inputs_case,'..'))
    
    print('Finished copy_parents.py')
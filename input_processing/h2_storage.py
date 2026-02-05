'''
This script calculates the H2 storage type for each model region.
Specifically, the script identifies the storage sites that exist in each
zone and associates the zone with its cheapest available storage site type.
'''

import argparse
import pandas as pd
import os
import sys
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


#%% ===========================================================================
### --- MAIN FUNCTION ---
### ===========================================================================
def main(reeds_path, inputs_case):
    print('Starting h2_storage.py')

    # Get model regions
    dfzones = reeds.io.get_dfmap(
        os.path.dirname(inputs_case),
        levels=['r'],
        exclude_water_areas=True
    )['r']
    dfzones['geometry'] = dfzones['geometry'].buffer(0.)
    dfzones['km2'] = dfzones.geometry.area / 1e6

    for h2_storage_type in ['hardrock', 'salt']:
        # Get storage sites of the given type and combine them into one region
        h2_storage_sites = reeds.io.get_h2_storage_sites(
            h2_storage_type=h2_storage_type
        )
        h2_storage_region = (
            h2_storage_sites.dissolve()
            .loc[0,'geometry']
            .buffer(0.)
        )

        # Calculate the areas of intersection between model regions and the
        # collection of storage sites as percentages of total model region area
        dfzones[h2_storage_type] = dfzones.intersection(h2_storage_region)
        dfzones[h2_storage_type+'_km2'] = (
            dfzones[h2_storage_type].area / 1e6
        )
        dfzones[h2_storage_type+'_frac'] = (
            dfzones[h2_storage_type+'_km2'] / dfzones['km2']
        )

    # Determine the H2 storage types available in each model region
    # and reformat dataframe
    scalars = reeds.io.get_scalars()
    dfout = (
        pd.concat(
            {
                col: pd.Series(
                    dfzones.loc[(
                        dfzones[col+'_frac']
                        > scalars["h2_storage_area_threshold"]
                    )]
                    .index
                    .values
                )
                for col in ['hardrock','salt']
            }
        )
        .reset_index(level=1, drop=True)
        .rename('rb')
        .reset_index()
        .rename(columns={'index':'*h2stortype'})
        .assign(exists=1)
        .pivot(index='rb',columns='*h2stortype',values='exists')
        .reindex(dfzones.index.rename('rb'))
        .fillna(0)
        .astype(int)
    )
    
    # Downselect to one row per model region, selecting the cheapeast storage
    # type available in the region, assuming salt is cheaper than hardrock.
    outname = {
        'hardrock':'h2_storage_hardrock',
        'salt':'h2_storage_saltcavern',
        'underground':'h2_storage_undergroundpipe',
    }
    dfout['keep'] = (
        dfout.apply(
            lambda row: (
                'salt' if row.get('salt', False)
                else 'hardrock' if row.get('hardrock', False)
                else 'underground'
            ),
            axis=1
        )
        .replace(outname)
    )
    dfout = (
        dfout.reset_index()
        .rename(columns={'keep':'*h2_stor'})
        [['*h2_stor','rb']]
    )

    dfout.to_csv(
        os.path.join(inputs_case, 'h2_storage_rb.csv'),
        index=False
    )

#%% ===========================================================================
### --- PROCEDURE ---
### ===========================================================================

if __name__ == '__main__':
    # Time the operation of this script
    tic = datetime.datetime.now()

    ### Parse arguments
    parser = argparse.ArgumentParser(
        description='Process H2 storage inputs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('reeds_path', help='ReEDS-2.0 directory')
    parser.add_argument('inputs_case', help='ReEDS-2.0/runs/{case}/inputs_case directory')

    args = parser.parse_args()
    reeds_path = args.reeds_path
    inputs_case = args.inputs_case

    #%% Set up logger
    log = reeds.log.makelog(
        scriptname=__file__,
        logpath=os.path.join(inputs_case,'..','gamslog.txt'),
    )

    #%% Run it
    main(reeds_path=reeds_path, inputs_case=inputs_case)

    reeds.log.toc(tic=tic, year=0, process='input_processing/h2_storage.py',
        path=os.path.join(inputs_case,'..'))
    
    print('Finished h2_storage.py')
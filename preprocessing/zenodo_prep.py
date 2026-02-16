"""
Collection of helper functions for uploading files to Zenodo and sanity-checking the file
contents (specifically for hourly capacity factor and electricity demand profiles).
"""

#%% Imports
import sys
import time
import h5py
import cmocean
import hashlib
import argparse
import requests
import subprocess
import pandas as pd
import geopandas as gpd
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
sys.path.append(str(Path(__file__).parent.parent))
import reeds


#%% Constants
baseurl = 'https://zenodo.org/api'
tokenfile = Path('~/.zenodo').expanduser()

INFILES = [
    ## tech, access, resolution, special
    ('upv', 'limited', 'ba', ''),
    ('upv', 'reference', 'ba', ''),
    ('upv', 'open', 'ba', ''),
    ('upv', 'limited', 'county', ''),
    ('upv', 'reference', 'county', ''),
    ('upv', 'open', 'county', ''),

    ('wind-ons', 'limited', 'ba', ''),
    ('wind-ons', 'reference', 'ba', ''),
    ('wind-ons', 'open', 'ba', ''),
    ('wind-ons', 'limited', 'county', ''),
    ('wind-ons', 'reference', 'county', ''),
    ('wind-ons', 'open', 'county', ''),

    ('wind-ofs', 'limited', 'ba', 'radial'),
    ('wind-ofs', 'reference', 'ba', 'radial'),
    ('wind-ofs', 'open', 'ba', 'radial'),
    ('wind-ofs', 'limited', 'county', 'radial'),
    ('wind-ofs', 'reference', 'county', 'radial'),
    ('wind-ofs', 'open', 'county', 'radial'),

    ('wind-ofs', 'limited', 'ba', 'meshed'),
    ('wind-ofs', 'reference', 'ba', 'meshed'),
    ('wind-ofs', 'open', 'ba', 'meshed'),
]

### Derived constants
with open(tokenfile, 'r') as f:
    ACCESS_TOKEN = f.read().split()[-1]

headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}


#%% Functions
### Supply curve
def get_cap_class_region(
    tech:str='upv',
    access:str='reference',
    resolution:str='ba',
    special:str='',
):
    """
    Load a site-level supply curve and convert to region/class resolution

    Args:
        tech (str): VRE technology class. Options: ['upv', 'wind-ons', 'wind-ofs']
        access (str): Siting access scenario. Options: ['limited', 'reference', 'open']
        resolution (str): Output resolution. Options: ['ba', 'county']
        special (str): Only used for offshore wind. Options: ['', 'meshed', 'radial']
    
    Returns:
        pd.Series: Capacity [MW] by class|region
    """
    scfile = Path(
        reeds.io.reeds_path, 'inputs', 'supply_curve', f'supplycurve_{tech}-{access}.csv'
    )
    supplycurve = reeds.io.assemble_supplycurve(
        scfile=scfile,
        GSw_OffshoreZones=(1 if special == 'meshed' else 0),
    )
    supplycurve['pFIPS'] = 'p' + supplycurve.FIPS
    regioncolumn = 'region' if resolution == 'ba' else 'pFIPS'
    supplycurve['label'] = supplycurve['class'].astype(str) + '|' + supplycurve[regioncolumn]

    cap_classr = (
        supplycurve.groupby('label').capacity.sum()
        .rename('MW').rename_axis('class|region')
        .round(0).astype(int)
    )

    return cap_classr


def write_regionclass_capacity(
    tech:str='upv',
    access:str='reference',
    resolution:str='ba',
    special:str='',
    savepath=Path('~/Desktop').expanduser(),
):
    """
    Write a region/class-resolution supply curve file

    Args:
        tech (str): VRE technology class. Options: ['upv', 'wind-ons', 'wind-ofs']
        access (str): Siting access scenario. Options: ['limited', 'reference', 'open']
        resolution (str): Output resolution. Options: ['ba', 'county']
        special (str): Only used for offshore wind. Options: ['', 'meshed', 'radial']
        savepath (Path or str): Directory name for output .csv file

    Returns:
        None
    """
    print(tech, access, resolution, special)
    cap_classr = get_cap_class_region(tech, access, resolution, special)

    ## Make sure it matches the dimensions of the CF file
    fname = f"{tech}{f'_{special}' if special else ''}_{access}_{resolution}"
    labels = reeds.io.read_file(
        Path(
            reeds.io.reeds_path, 'inputs', 'profiles_cf', f'cf_{fname}.h5',
        )
    ).columns.values

    missing_from_cf = [i for i in cap_classr.index if i not in labels]
    missing_from_sc = [i for i in labels if i not in cap_classr.index]
    if len(missing_from_cf):
        raise KeyError(
            f"{len(missing_from_cf)} missing from CF: {' '.join(missing_from_cf)}"
        )
    if len(missing_from_sc):
        raise KeyError(
            f"{len(missing_from_sc)} missing from supply curve: {' '.join(missing_from_sc)}"
        )

    ## Write it
    outfile = Path(savepath, f"sc_{fname}.csv")
    cap_classr.to_csv(outfile)


def write_zonal_supplycurves(savepath):
    """Write all region/class-resolution supply curve files"""
    Path(savepath).mkdir(exist_ok=True)
    for (tech, access, resolution, special) in INFILES:
        write_regionclass_capacity(tech, access, resolution, special, savepath)


### Upload
def get_my_draft_records(verbose=0):
    """
    Return a list of your own Zenodo records, where a "record" is a dictionary
    of Zenodo metadata for a given "record_id".
    """
    r = requests.get(
        f'{baseurl}/deposit/depositions',
        params={'status': 'draft'},
        headers=headers,
    )
    if verbose:
        print(r.status_code)
    return r.json()


def print_my_draft_records():
    """Print your own Zenodo record titles and IDs"""
    records = get_my_draft_records()
    for record in records:
        print(f"ID: {record['id']}  |  Title: {record['title']}")


def get_record(record_id) -> dict:
    """Get the complete metadata for the specified Zenodo record_id"""
    r = requests.get(
        f'{baseurl}/deposit/depositions/{record_id}',
        headers=headers,
    )
    status = r.status_code
    if status != 200:
        raise Exception(status)
    record = r.json()

    return record


def create_record():
    """Create a new empty record and return the record metadata"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    r = requests.post(
        f'{baseurl}/deposit/depositions',
        json={},
        headers=headers,
    )
    record = r.json()
    return record


def get_files(record) -> list:
    """
    Return a list of filenames associated with the specified record.

    Args:
        record: record id (int) or record (dict)

    Returns:
        list of filenames in the record
    """
    if isinstance(record, int):
        record = get_record(record)

    return [i['filename'] for i in record['files']]


def add_file_to_record(
    filepath,
    record_id:int,
    timeout=600,
    attempts:int=10,
    wait=10,
):
    """
    Upload a local file to an existing Zenodo draft record.

    Development notes:
        - Consider https://stackoverflow.com/questions/492519/timeout-on-a-function-call

    Args:
        filepath (str or Path): Path to local file
        record_id (int): Zenodo record ID (the end of the draft record URL)
        timeout [seconds]: Time to wait before restarting the upload
        attempts (int): Number of times to try the upload (in case it times out)
        wait [seconds]: Time to wait between uploads
    """
    fpath = Path(filepath).expanduser()
    if not fpath.is_file():
        raise FileNotFoundError(fpath)

    record = get_record(record_id)
    files = get_files(record)
    if fpath.name in files:
        print(f"{fpath.name} is already in record, so was not uploaded")
        return

    ## Upload it
    bucket_url = record['links']['bucket']
    success = False
    for attempt in range(attempts):
        try:
            with open(fpath, 'rb') as f:
                r = requests.put(
                    f'{bucket_url}/{fpath.name}',
                    data=f,
                    headers=headers,
                )
            status = r.status_code
            if status == 201:
                print(f"{fpath.name}: Success after {attempt+1} attempts")
                success = True
                time.sleep(wait)
                break
            else:
                raise Exception(status)
        # except requests.exceptions.Timeout:
        except Exception as err:
            print(f"Failed on attempt {attempt+1} with error '{err}'; retrying")
            time.sleep(wait)
            continue

    if not success:
        raise Exception(f"{fpath.name}: Failed after {attempts} attempts")


def get_checksums_remote(verbose=1):
    """
    Get (and print if verbose) all the files and md5 checksums for your Zenodo records.
    """
    records = get_my_draft_records()
    reeds_records = [r for r in records if r['metadata']['title'].startswith('ReEDS:')]
    out = {}
    for r in reeds_records:
        if verbose:
            print(r['title'])
            print('-'*len(r['title']))
        record = get_record(r['id'])
        for file in record['files']:
            out[file['filename']] = file['checksum']
            if verbose:
                print(f"{file['checksum']} {file['filename']}")
        if verbose:
            print()
    return out


def get_checksums_local(localpath, verbose=1):
    """
    Get (and print if verbose) the files and md5 checksums for files in localpath.
    """
    filedirs = [i for i in sorted(Path(localpath).glob('[!.]*')) if i.is_dir()]
    out = {}
    for filedir in filedirs:
        if verbose:
            print(filedir.name)
            print('-'*len(filedir.name))
        files = sorted(filedir.glob('[!.]*'))
        for file in files:
            with open(file, 'rb') as f:
                filehash = hashlib.md5(f.read()).hexdigest()
            out[file.name] = filehash
            if verbose:
                print(f"{filehash} {file.name}")
        if verbose:
            print()
    return out


def compare_checksums(localpath=None):
    """
    If localpath is provided, compare remote checksums to files in localpath;
    otherwise, compare remote checksums to table of checksums from get_remote_filemap()
    """
    checksums_remote = pd.Series(get_checksums_remote(), name='remote')
    if localpath:
        checksums_local = pd.Series(get_checksums_local(localpath), name='local')
    else:
        checksums_local = reeds.remote.get_remote_filemap()['md5'].rename('local')
    checksums = pd.concat([checksums_local, checksums_remote], axis=1)
    ## Only keep results for local files
    checksums = checksums.dropna(subset='local')
    if not len(checksums):
        raise ValueError('No matches between local and remote!')
    checksums['mismatch'] = (checksums.local != checksums.remote).astype(int)
    mismatch = checksums.loc[checksums.mismatch == 1]
    if len(mismatch):
        print("ERROR: The following files don't match:")
        print(mismatch)
    return checksums


### Visualization for quality control
def plot_cf(
    tech, access, resolution, special, dfmap, scmaps,
    cmap=plt.cm.turbo,
):
    """Plot average CF by model zone and return (f, ax)"""
    fname = (
        f"{tech}{f'_{special}' if special else ''}"
        f"{f'_{access}' if access else ''}_{resolution}"
    )
    dfcf = reeds.io.read_file(
        Path(
            reeds.io.reeds_path, 'inputs', 'profiles_cf', f'cf_{fname}.h5',
        )
    ).mean()

    if special == 'meshed':
        dfplot = pd.concat([scmaps[resolution], scmaps['offshore']])
    else:
        dfplot = scmaps[resolution].copy()

    if tech == 'distpv':
        dfplot['cf'] = dfcf
    else:
        cap_classr = get_cap_class_region(tech, access, resolution, special)
        cap_classr.index = pd.MultiIndex.from_tuples(
            cap_classr.index.str.split('|').map(lambda x: tuple(x)), names=('class','r')
        )
        dfcf.index = pd.MultiIndex.from_tuples(
            dfcf.index.str.split('|').map(lambda x: tuple(x)), names=('class','r')
        )
        dfplot['cf'] = (dfcf * cap_classr).groupby('r').sum() / cap_classr.groupby('r').sum()

    dfplot = dfplot.dropna(subset='cf')
    vmin = 0.
    vmax = dfplot.cf.max()

    plt.close()
    f,ax = plt.subplots()
    ## Background
    dfmap['st'].plot(ax=ax, facecolor='none', edgecolor='k', lw=0.25, zorder=1e6)
    ## Values
    dfplot.plot(ax=ax, column='cf', edgecolor='none', cmap=cmap, vmin=vmin, vmax=vmax)
    reeds.plots.addcolorbarhist(
        f, ax, dfplot.cf.values, vmin=vmin, vmax=vmax, cmap=cmap,
        cbarheight=0.8, title='CF [.]', nbins=51,
    )
    ## Formatting
    ax.axis('off')
    ax.set_title(fname, y=0.92)

    return f, ax


def plot_cf_maps(savepath):
    """Plot average CF for all scenarios and save to savepath"""
    dfmap = reeds.io.get_dfmap()
    scmaps = {
        'ba': dfmap['r'],
        'county': reeds.io.get_countymap().set_index('rb'),
        'offshore': gpd.read_file(
            Path(reeds.io.reeds_path, 'inputs', 'shapefiles', 'offshore_zones.gpkg')
        ).set_index('zone').to_crs(dfmap['r'].crs),
    }
    plot_infiles = INFILES + [('distpv', '', 'county', '')]
    for (tech, access, resolution, special) in plot_infiles:
        fname = (
            f"{tech}{f'_{special}' if special else ''}"
            f"{f'_{access}' if access else ''}_{resolution}"
        )
        outfile = Path(savepath, f'map_cf_{fname}.png')
        f,ax = plot_cf(tech, access, resolution, special, dfmap, scmaps)
        plt.savefig(outfile)
        print(outfile)


def plot_demand(
    GSw_LoadProfiles='EER2025_IRAlow',
    dfmap=None,
    scale=2,
    cmap=cmocean.cm.rain,
) -> tuple:
    """Plot average demand for GSw_LoadProfiles at state resolution and return (f, ax)"""
    if dfmap is None:
        dfmap = reeds.io.get_dfmap()
    h5path = Path(
        reeds.io.reeds_path, 'inputs', 'profiles_demand', f'demand_{GSw_LoadProfiles}.h5'
    )
    if GSw_LoadProfiles == 'historic':
        load_hourly = reeds.io.read_file(h5path)
    else:
        load_hourly = pd.concat(reeds.io.read_h5_groups(h5path))
    ## Average by state and convert to GW
    if isinstance(load_hourly.index, pd.MultiIndex):
        dfload = load_hourly.groupby(axis=0, level=0).mean().rename_axis('t') / 1e3
    else:
        dfload = load_hourly.mean().to_frame().T.rename_axis('t') / 1e3

    vmin = 0.
    vmax = dfload.max().max()
    years = dfload.index.values
    nrows, ncols, coords = reeds.plots.get_coordinates(years, aspect=1.1)

    plt.close()
    f,ax = plt.subplots(
        nrows, ncols, figsize=(ncols*scale, nrows*scale*0.75),
        sharex=True, sharey=True, gridspec_kw={'hspace':0, 'wspace':0},
    )
    for year, df in dfload.iterrows():
        dfplot = dfmap['st'].copy()
        dfplot['gw'] = df
        if nrows == ncols == 1:
            _ax = ax
        else:
            _ax = ax[coords[year]]
        dfplot.plot(ax=_ax, column='gw', cmap=cmap, vmin=vmin, vmax=vmax)
        _ax.set_title(year, y=0.87)
        _ax.axis('off')
    reeds.plots.trim_subplots(ax, nrows, ncols, len(years))
    return f, ax


def plot_demands(savepath):
    """Plot average demand for all scenarios at state resolution and save to savepath"""
    demand_switches = [
        'historic',
        'EFS_HIGH',
        'EFS_MEDIUM',
        'EFS_MEDIUMStretch2040',
        'EFS_MEDIUMStretch2046',
        'EFS_REFERENCE',
        'EFS_Clean2035',
        'EFS_Clean2035_LTS',
        'EFS_Clean2035clip1pct',
        'EFS_Baseline',
        'EER2025_100by2050',
        'EER2025_Baseline_AEO2023',
        'EER2025_IRAlow',
        'EER2023_100by2050',
        'EER2023_Baseline_AEO2022',
        'EER2023_IRAlow',
        'EER2023_IRAmoderate',
    ]
    dfmap = reeds.io.get_dfmap()
    for GSw_LoadProfiles in demand_switches:
        f,ax = plot_demand(GSw_LoadProfiles=GSw_LoadProfiles, dfmap=dfmap)
        outfile = Path(savepath, f'map_demand_{GSw_LoadProfiles}.png')
        plt.savefig(outfile)


### File-reading functions included in Zenodo metadata
def read_profile(filepath):
    """
    Read an hourly profile from `filepath` and return a pandas dataframe.
    Usage:
    `df = read_profile('/path/to/filename.h5')`
    """
    encoding = 'utf-8'
    with h5py.File(filepath, 'r') as f:
        df = pd.DataFrame(
            f['data'][:],
            columns=pd.Series(f['columns']).str.decode(encoding),
            index=f['index_0'],
        )
        df.index = pd.to_datetime(
            pd.Series(df.index, name='datetime').str.decode(encoding)
        )
    return df


def read_demand_profile(filepath):
    """
    Read a demand profile from `filepath` and return a pandas dataframe.
    Usage:
    `df = read_profile('/path/to/filename.h5')`
    """
    encoding = 'utf-8'
    with h5py.File(filepath, 'r') as f:
        years = list(f.keys())
        first_year = years[0]
        not_states = ['columns', 'datetime']
        states = [i for i in list(f[first_year].keys()) if i not in not_states]
        dictout = {}
        for year in years:
            for state in states:
                dictout[year,state] = pd.Series(f[year][state][:])
        df = pd.concat(dictout, axis=1, names=('year','state'))
        df.index = pd.to_datetime(
            pd.Series(f[first_year]['datetime'], name='datetime')
            .str.decode(encoding)
        )
    return df


def test_read_profiles(localpath:str|Path):
    """Test file-reading functions for all profiles in localpath"""
    filedirs = [i for i in sorted(Path(localpath).glob('[!.]*')) if i.is_dir()]
    for filedir in filedirs:
        files_no_modelyear = (
            sorted(filedir.glob('cf_*.h5'))
            + sorted(filedir.glob('demand_hist*.h5'))
        )
        for file in files_no_modelyear:
            read_profile(file)
            print(file.name)

        files_modelyear = sorted(filedir.glob('demand_E*.h5'))
        for file in files_modelyear:
            read_demand_profile(file)
            print(file.name)


def get_lfs_files() -> pd.DataFrame:
    """
    Get the paths and sizes for files managed by LFS for the present commit.
    Must be run from within a git repo.
    """
    r = subprocess.run('git lfs ls-files -s', shell=True, capture_output=True)
    df = pd.DataFrame(r.stdout.decode().strip().split('\n'), columns=['text'])
    delim = ' - ' if ' - ' in df.loc[0,'text'] else r' \* '
    df['filepath'] = df.text.str.split(delim).str[-1].str.split(' ').str[0]
    df['sizestring'] = df.text.str.split('(').str[-1].str.strip(')')
    df['sizeunits'] = df.sizestring.str.split(' ').str[-1].str.upper()
    df['size_in_units'] = df.sizestring.str.split(' ').str[0].astype(float)
    scale = {'KB':1e-3, 'MB':1, 'GB':1e3}
    df['MB'] = df.size_in_units * df.sizeunits.map(scale)
    df['dirname'] = df.filepath.map(lambda x: Path(x).parent)
    df['filename'] = df.filepath.map(lambda x: Path(x).name)
    return df[['filepath','dirname','filename','MB','text']]


def plot_lfs_files(savepath:str|Path=None, cutoff:float=1) -> tuple:
    """
    Args:
        savepath (str or Path): Directory to save "git_lfs_filesize.png" to.
            If not provided, will not save the figure.
        cutoff [MB]: Only plot files with size above this value

    Returns:
        tuple: (f, ax)
    """
    lfs = get_lfs_files().sort_values('MB', ascending=False)
    total_mb = lfs.MB.sum()
    dfplot = lfs.loc[lfs.MB >= cutoff].reset_index(drop=True)

    categories = dfplot.groupby('dirname').MB.sum().sort_values(ascending=False)
    colors = reeds.plots.rainbowmapper(categories.index)

    ### Plot it
    plt.close()
    f,ax = plt.subplots(figsize=(12, 2.75))
    ## Data
    for i, row in dfplot.iterrows():
        ax.bar(
            i, row.MB, color=colors[row.dirname],
        )
    ## Legend
    handles = [
        mpl.patches.Patch(
            facecolor=c,
            label=f"{k} ({lfs.loc[lfs.dirname==k].MB.sum():.0f} MB)",
        )
        for k,c in colors.items()
    ]
    ax.legend(
        handles=handles, loc='upper right', frameon=False,
        handletextpad=0.3, handlelength=0.7, labelspacing=0.2,
        title=f'LFS total: {total_mb:.0f} MB', title_fontsize=12,
    )
    ## Formatting
    ax.set_xticks(dfplot.index)
    ax.set_xticklabels(dfplot.filename, rotation=90)
    ax.set_xlim(-0.5, len(dfplot)-0.5)
    ax.set_ylabel('File size [MB]')
    ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    reeds.plots.despine(ax)
    if savepath:
        plt.savefig(Path(savepath, 'git_lfs_filesize.png'))
    return f, ax


#%% Procedure
def main(savepath, localpath):
    #%% Make working directory
    savepath.mkdir(exist_ok=True)

    #%% Create the zonal supply curve files
    write_zonal_supplycurves(savepath)

    #%% Plot the average CFs
    plot_cf_maps(savepath)

    #%% Plot the average demands
    plot_demands(savepath)

    #%% Test files to upload (Could automate the actual upload here if we want)
    test_read_profiles(localpath)

    #%% Verify the checksums
    compare_checksums(localpath)

#%%
if __name__ == '__main__':
    #%% Argument inputs
    parser = argparse.ArgumentParser(
        description=(
            'Zenodo: Create zonal supply curves, plot average CF and demand, '
            'and verify checksums'
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        'savepath', type=str,
        help='path to working directory for plots and supply curves',
    )
    parser.add_argument(
        'localpath', type=str,
        help='path to local directory of files to upload to Zenodo',
    )
    args = parser.parse_args()
    savepath = args.savepath
    localpath = args.localpath

    # #%% Inputs for testing
    # savepath = Path('~/Projects/ReEDS/zenodo/20260203_test').expanduser()
    # localpath = Path('~/Projects/ReEDS/zenodo/20260128').expanduser()

    #%% Run it
    main(savepath, localpath)

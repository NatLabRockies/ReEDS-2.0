#%% Imports
import io
import sys
import hashlib
import zipfile
import argparse
import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import reeds
reeds_path = reeds.io.reeds_path


#%% Functions
def download(url, path, unzip=False, progressbar=True, access_token=None):
    if access_token:
        url += f'?access_token={access_token}'
    r = requests.get(url, stream=True)
    if url.endswith('.zip') and unzip:
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(path=path)
    else:
        if progressbar:
            with tqdm.wrapattr(
                open(path, 'wb'),
                'write',
                miniters=1,
                desc=Path(path).name,
                total=int(r.headers.get('content-length', 0)),
                file=sys.stdout,
            ) as f:
                for chunk in r.iter_content(chunk_size=4096):
                    f.write(chunk)
        else:
            with open(path, 'wb') as f:
                f.write(r.content)


def _get_url(row):
    return row.url_base.format(record_id=row.record_id, filename=row.filename)

def _add_id(row):
    filepath = Path(row.filename)
    return f"{filepath.stem}_{row.record_id}{filepath.suffix}"

def _get_rawpath(row):
    return Path(reeds.io.reeds_path, 'inputs', 'remote', row.filename_id)

def _get_linkpath(row):
    return Path(reeds.io.reeds_path, 'inputs', row.inputs_path, row.filename)

def get_remote_filemap():
    remote_files = pd.read_csv(Path(reeds.io.reeds_path, 'inputs', 'remote_files.csv'))
    remote_files['url'] = remote_files.apply(_get_url, axis=1)
    remote_files['filename_id'] = remote_files.apply(_add_id, axis=1)
    remote_files['rawpath'] = remote_files.apply(_get_rawpath, axis=1)
    remote_files['linkpath'] = remote_files.apply(_get_linkpath, axis=1)
    filemap = remote_files.set_index('filename')
    return filemap


def get_md5sum(filepath):
    with open(filepath, 'rb') as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    return md5


def download_remote_files(only=None, force=False, access_token=None):
    """
    Downloads remote files. Only downloads the the files specified by `only` if `only`
    is provided; otherwise, downloads all remote files that could be used by the
    present commit.

    Args:
        only (optional): List of files to download
        force (bool): Always download, even if file already exists
    """
    filemap = get_remote_filemap()
    if only:
        filemap = filemap.loc[only]
    for filename, row in filemap.iterrows():
        url = row.url
        rawpath = Path(row.rawpath)
        ## Download it if necessary
        md5 = get_md5sum(rawpath) if rawpath.is_file() else ''
        if (not rawpath.is_file()) or (md5 != row.md5) or force:
            download(url, rawpath, access_token=access_token)
        ## Always update the link
        linkpath = Path(row.linkpath)
        linkpath.unlink(missing_ok=True)
        try:
            linkpath.symlink_to(rawpath)
        except OSError:
            ## On Windows systems, admin privileges are required to create symlinks,
            ## so we fall back to a hardlink if the user isn't able to create a symlink.
            ## Symlinks are otherwise used by default since they cause less confusion
            ## when estimating file/folder sizes.
            linkpath.hardlink_to(rawpath)


def identify_required_remote_files(sw) -> list:
    """
    Determine the remotely hosted files required for this run

    Returns:
        required_files: List of file names (no directories)
    """
    required_files = []
    if sw.GSw_RegionResolution in ['county', 'mixed']:
        required_files.extend([
            f"cf_upv_{sw.GSw_SitingUPV}_county.h5",
            f"cf_wind-ons_{sw.GSw_SitingWindOns}_county.h5"
        ])
        if int(sw.GSw_OfsWind):
            required_files.append(
                f"cf_wind-ofs_{sw.GSw_OffshoreFiles}_{sw.GSw_SitingWindOfs}_county.h5"
            )

    if sw.GSw_RegionResolution not in ['county']:
        required_files.extend([
            f"cf_upv_{sw.GSw_SitingUPV}_ba.h5",
            f"cf_wind-ons_{sw.GSw_SitingWindOns}_ba.h5"
        ])
        if int(sw.GSw_OfsWind):
            required_files.append(
                f"cf_wind-ofs_{sw.GSw_OffshoreFiles}_{sw.GSw_SitingWindOfs}_ba.h5"
            )

    ## If a filepath is provided to GSw_LoadProfiles, we don't pull it from the remote
    if not Path(sw.GSw_LoadProfiles).is_file():
        required_files.append(f"demand_{sw.GSw_LoadProfiles}.h5")
    if sw.GSw_LoadProfiles.startswith('EER'):
        # In hourly_load.py, EER load profiles are calibrated using
        # historical load profiles, so the latter are required for
        # EER load scenarios.
        required_files.append("demand_historic.h5")

    if int(sw.GSw_distpv):
        required_files.append("cf_distpv_county.h5")
    
    return required_files


def download_required_remote_files(sw):
    required_files = identify_required_remote_files(sw)
    download_remote_files(required_files)


#%% Procedure
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download all remote files used for this commit',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--token', '-t', type=str, required=False, default='',
        help='Remote access token. Not required; only used for testing draft records.'
    )
    args = parser.parse_args()
    ACCESS_TOKEN = args.token

    download_remote_files(access_token=ACCESS_TOKEN)

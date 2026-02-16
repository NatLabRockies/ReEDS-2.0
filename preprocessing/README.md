# Preprocessing tools

## Updating or creating new remote data

The `preprocessing/zenodo_prep.py` script provides a collection of helper functions for uploading files to Zenodo and sanity-checking the file contents
(specifically for hourly capacity factor and electricity demand profiles).
The general steps for creating or updating a Zenodo record are:

1. Create a [Zenodo account](https://zenodo.org/) if you haven't already
1. If you are not already a member of the [ReEDS community](https://zenodo.org/communities/nrel-reeds), ask one of the community managers (Patrick, Kodi, Brian, or Kennedy) to invite you
1. Discuss the planned update with the ReEDS team and decide whether you are creating a new record or updating an existing record
    1. If you are creating a new record for a new type of data file, click "New upload" on your [uploads page](https://zenodo.org/me/uploads)
    1. If you are updating an existing record, click "New version" on the existing record (here's an [example](https://zenodo.org/records/18407659))
1. Decide what files to include
    1. In addition to the files used directly by ReEDS, we also include files that help the data stand alone without direct reference to files in the ReEDS repository.
    For example, for the [VRE supply curves](https://zenodo.org/records/18407659) at BA resolution, we also include a copy of the `county2zone.csv` file to define the BAs and `sc_{tech}_{access}_{resolution}.csv` files to indicate the MW capacity available for each column (class/region) of the CF profiles.
1. Plot the data in the files for quality control
    1. Look at both the hourly profiles averaged across zones and maps of the profiles averaged across hours
    1. Functions to help with sanity-checking large data files are available in:
        1. `preprocessing/zenodo_prep.py`
        1. `postprocessing/input_plots.py`
        1. `postprocessing/input_diff_plots.py`
1. Write the metadata
    1. Determine the author list
    1. Include each author's [ORCID ID](https://orcid.org/) if they have one
    1. Write or update the following sections for the description, using an [existing](https://zenodo.org/records/18435263) [record](https://zenodo.org/records/18407659) as a guide:
        1. General description, including links to relevant model github pages, the [ReEDS](https://github.com/NREL/ReEDS-2.0) model, and the [ReEDS documentation](https://natlabrockies.github.io/ReEDS-2.0/model_documentation.html)
        1. Technical assumptions (such as losses, orientation and inverter loading ratio for PV, specific power and hub height for wind, etc.), with citations to relevant published papers or reports
        1. Temporal resolution
        1. Spatial resolution
        1. File structure and naming conventions (if multiple files are in the record)
        1. An example Python script for reading the file (if using a non-text-based format like `.h5`)
            1. Double check that it works for all uploaded files using `zenodo_prep.test_read_profiles()`
    1. Ask the authors of the record to review the text
1. Upload the files
    1. Try using the web interface first.
    If your uploads hang indefinitely, try using the [Zenodo API](https://developers.zenodo.org/) via `preprocessing.zenodo_prep.add_file_to_record()`.
    If you're still having trouble, try at different times of day on different days of the week.
    (The Zenodo servers experience [a lot of traffic](https://blog.zenodo.org/2026/01/28/2026-01-28-improvements-and-support-expectations/) and sometimes slow down.)
    1. Make sure the md5 checksums of the uploaded files match the checksums of the local files using `preprocessing.zenodo_prep.compare_checksums()`
1. Review the record preview a few times
1. Publish the record
1. Update the ReEDS repository as necessary
    1. Update the affected file entries in `inputs/remote_files.csv`
        1. If a new file was added, add a new row
        1. If an existing file was updated, change the `record_id` and `md5` for an existing row
    1. If new switch options were added, update the choices in `cases.csv`
    1. Update the documentation if necessary
        1. Descriptions of assumptions and links to relevant papers or reports
        1. Figures
        1. Tables and numeric values ("X GW in the supply curve", "Y% CAGR in demand", etc.)
        1. References to switch options if the options have changed
    1. Open a pull request to merge the changes into the main branch, following all the usual steps (compare reports against the main branch, description of changes, etc.)

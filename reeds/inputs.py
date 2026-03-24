### Imports
import os
import sys
import pandas as pd
import sklearn.cluster
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds


### Functions
def parse_regions(case_or_string, case=None):
    """
    Inputs
    ------
    case_or_string: path to a ReEDS case or a parseable string in the format of GSw_Region
    case: path to a ReEDS case. Only used if case_or_string is not a ReEDS case. Should be
        used if you want to select a subset of model zones from a ReEDS case that used
        region aggregation.

    Returns
    -------
    np.array of zone names
        - If case_or_string is a case, return the regions modeled in the run
        - If case_or_string is a parseable string in the format of GSw_Region, return
          the regions that obey that string

    Examples
    --------
    parse_regions('transreg/NYISO') -> ['p127', 'p128']
    parse_regions('st/PA') -> ['p115', 'p119', 'p120', 'p122']
    parse_regions('st/PA', 'path/to/case/using/region/aggregation') -> ['p115', 'p120', 'z122']
    """
    if os.path.exists(case_or_string):
        sw = reeds.io.get_switches(case_or_string)
        hierarchy = reeds.io.get_hierarchy(case_or_string)
        GSw_Region = sw['GSw_Region']
    ## Provide case argument if using aggregated regions
    elif os.path.exists(str(case)):
        hierarchy = reeds.io.get_hierarchy(case)
        GSw_Region = case_or_string
    else:
        hierarchy = reeds.io.get_hierarchy()
        GSw_Region = case_or_string

    if '/' in GSw_Region:
        level, regions = GSw_Region.split('/')
        regions = regions.split('.')
        if level in ['r', 'ba']:
            rs = [r for r in hierarchy.index if r in regions]
        else:
            rs = hierarchy.loc[hierarchy[level].isin(regions)].index
    else:
        modeled_regions = pd.read_csv(
            os.path.join(reeds.io.reeds_path, 'inputs', 'userinput', 'modeled_regions.csv')
        )
        modeled_regions.columns = modeled_regions.columns.str.lower()
        rs = list(
            modeled_regions[
                ~modeled_regions[GSw_Region.lower()].isna()
            ]['r'].unique()
        )
    return rs


def get_bin(
    df_in,
    bin_num,
    bin_method='equal_cap_cut',
    bin_col='capacity_factor_ac',
    bin_out_col='bin',
    weight_col='capacity',
):
    """
    bin supply curve points based on a specified bin column. Used in hourlize to create 'bins'
    for the resource classes (typically using capacity factor) and then used by
    writesupplycurves.py to create bins based on supply curve cost.
    """
    df = df_in.copy()
    ser = df[bin_col]
    # If we have less than or equal unique points than bin_num,
    # we simply group the points with the same values.
    if ser.unique().size <= bin_num:
        bin_ser = ser.rank(method='dense')
        df[bin_out_col] = bin_ser.values
    elif bin_method == 'kmeans':
        nparr = ser.to_numpy().reshape(-1,1)
        weights = df[weight_col].to_numpy()
        kmeans = (
            sklearn.cluster.KMeans(n_clusters=bin_num, random_state=0, n_init=10)
            .fit(nparr, sample_weight=weights)
        )
        bin_ser = pd.Series(kmeans.labels_)
        # but kmeans doesn't necessarily label in order of increasing value because it is 2D,
        # so we replace labels with cluster centers, then rank
        kmeans_map = pd.Series(kmeans.cluster_centers_.flatten())
        bin_ser = bin_ser.map(kmeans_map).rank(method='dense')
        df[bin_out_col] = bin_ser.values
    elif bin_method == 'equal_cap_man':
        # using a manual method instead of pd.cut because i want the first bin to contain the
        # first sc point regardless, even if its weight_col value is more than the capacity
        # of the bin, and likewise for other bins, so i don't skip any bins.
        orig_index = df.index
        df.sort_values(by=[bin_col], inplace=True)
        cumcaps = df[weight_col].cumsum().tolist()
        totcap = df[weight_col].sum()
        vals = df[bin_col].tolist()
        bins = []
        curbin = 1
        for i, _v in enumerate(vals):
            bins.append(curbin)
            if cumcaps[i] >= totcap*curbin/bin_num:
                curbin += 1
        df[bin_out_col] = bins
        # we need the same index ordering for apply to work
        df = df.reindex(index=orig_index)
    elif bin_method == 'equal_cap_cut':
        # Use pandas.cut with cumulative capacity in each class. This will assume equal capacity bins
        # to bin the data.
        orig_index = df.index
        df.sort_values(by=[bin_col], inplace=True)
        df['cum_cap'] = df[weight_col].cumsum()
        bin_ser = pd.cut(df['cum_cap'], bin_num, labels=False)
        bin_ser = bin_ser.rank(method='dense')
        df[bin_out_col] = bin_ser.values
        # we need the same index ordering for apply to work
        df = df.reindex(index=orig_index)
    df[bin_out_col] = df[bin_out_col].astype(int)
    return df

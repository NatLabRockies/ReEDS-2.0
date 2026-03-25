### This script takes a completed ReEDS run as input and identifies the
### interfaces with DC transmission capacity above a given cutoff in the
### chosen year. It then writes that collection of connections to
### inputs/transmission/transmission_capacity_future_{trtype}_{case}_{year}.
### The intended use case is to approximate the effect of a minimum investment
### size constraint for DC connections (which would require a mixed-integer
### representation to model directly).
#%% Imports
import pandas as pd
import os
from glob import glob

reeds_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


#%%### Functions
def get_biggest_network(df, weight='MW'):
    """
    Downselect a network to the subnetwork with the most nodes.
    Can be used for VSC to produce a single connected network.
    """
    ### Initialize the graph
    import networkx as nx
    G = nx.Graph()
    ### Add the nodes (BAs)
    G.add_nodes_from(
        sorted(list(set(
            df.r.tolist() + df.rr.tolist()
        )))
    )
    ### Add the edges
    G.add_edges_from(
        [(*key, val)
         for key,val in
         df.set_index(['r','rr'])[[weight]].T.to_dict().items()]
    )
    ### Get the number of disconnected subgraphs
    subgraphs = list(nx.connected_components(G))
    num_subgraphs = len(subgraphs)
    print(num_subgraphs)
    ### Get the biggest subgraph (the one with the most nodes)
    lengths = [len(s) for s in subgraphs]
    biggest_subgraph = subgraphs[lengths.index(max(lengths))]
    
    dfout = df.loc[df.r.isin(biggest_subgraph) & df.rr.isin(biggest_subgraph)].copy()

    return dfout


def downselect_hvdc(case, year, cutoff, single_network):
    ### Name the output file
    outfile = f"{os.path.basename(case)}-{cutoff*1000:.0f}MW-{year}.csv"

    ### Get final transmission capacity
    tran_out = pd.read_csv(
        os.path.join(case,'outputs','tran_out.csv')
    ).rename(columns={'Value':'MW'})

    ### Get lines
    dfwrite = tran_out.loc[
        (tran_out.t==year)
        & (~tran_out.trtype.isin(['AC','B2B']))
        & (tran_out.MW >= cutoff * 1000),
        ['r','rr','trtype']
    ].copy()

    ### Add extra fields
    dfwrite['status'] = 'Possible'
    dfwrite['t'] = 0
    dfwrite['MW'] = 100000

    ### If desired, only keep the single largest network
    if single_network:
        dfwrite = get_biggest_network(dfwrite)

    ### Write it
    os.makedirs(os.path.join(reeds_path,'inputs','transmission','cases'), exist_ok=True)
    dfwrite[['r','rr','status','trtype','t','MW']].to_csv(
        os.path.join(
            reeds_path,'inputs','transmission','cases',outfile,
        ),
        index=False,
    )
    print(outfile)


def main(args):
    ### See if the case exists; if so, run it
    if os.path.isdir(args.case):
        downselect_hvdc(
            case=args.case,
            year=args.year,
            cutoff=args.cutoff,
            single_network=args.single_network,
        )
    ### Otherwise, treat it as a prefix, find all runs that match it, and run for them
    else:
        cases = glob(args.case+'*')
        for case in cases:
            downselect_hvdc(
                case=case,
                year=args.year,
                cutoff=args.cutoff,
                single_network=args.single_network,
            )


#%% Argument inputs
import argparse
parser = argparse.ArgumentParser(description='Downselect HVDC connections')
parser.add_argument('case', type=str,
                    help='path to ReEDS run folder OR prefix of group of cases')
parser.add_argument('--year', '-y', type=int, default=2050,
                    help='capacity year to use')
parser.add_argument('--cutoff', '-c', type=float, default=1.5,
                    help='[GW] lower capacity limit for connections to include')
parser.add_argument('--single_network', '-x', action='store_true',
                    help='only keep the largest single network of connections')

args = parser.parse_args()
case = args.case
year = args.year
cutoff = args.cutoff
single_network = args.single_network


#%%### Procedure
if __name__ == '__main__':
    main(args)

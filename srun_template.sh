#!/bin/bash
#SBATCH --account=ACCOUNT
##SBATCH --partition=debug
#SBATCH --time=3:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mail-user=EMAIL
#SBATCH --mem=90000    # RAM in MB; 90000 for normal or 184000 for big-mem
#SBATCH --output=

# add >>> #SBATCH --qos=high <<< above for quicker launch at double AU cost

#load your default settings

. $HOME/.bashrc

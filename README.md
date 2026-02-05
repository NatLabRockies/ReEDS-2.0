## ReEDS 2.0
**Regional Energy Deployment System (ReEDS) Model**

 
[![CI](https://github.nrel.gov/ReEDS/ReEDS-2.0/actions/workflows/python-app.yaml/badge.svg)](https://github.nrel.gov/ReEDS/ReEDS-2.0/actions/workflows/python-app.yaml)
[![Documentation](https://img.shields.io/badge/Documentation-view%20online-0a7f5e?logo=readthedocs&logoColor=white&labelColor=555)](https://natlabrockies.github.io/ReEDS-2.0)
![Static Badge](https://img.shields.io/badge/python-3.11-blue)
![GitHub License](https://img.shields.io/github/license/natlabrockies/ReEDS-2.0)
[![DOI](https://zenodo.org/badge/189060033.svg)](https://doi.org/10.5281/zenodo.16943302)

</br>
</br>

This GitHub repository contains the source code for NLR's ReEDS model.
The ReEDS model source code is available at no cost from the National Laboratory of the Rockies.
The ReEDS model can be downloaded or cloned from [https://github.com/NatLabRockies/ReEDS-2.0](https://github.com/NatLabRockies/ReEDS-2.0).

**For more information about the model, see the [open source ReEDS-2.0 Documentation](https://NatLabRockies.github.io/ReEDS-2.0).**

ReEDS training videos are available on the [NLR Learning YouTube channel](https://youtube.com/playlist?list=PLmIn8Hncs7bG558qNlmz2QbKhsv7QCKiC&si=NgGBaL_MxNcYiIEX).



<a name="Introduction"></a>

## Introduction

[ReEDS](https://www.nrel.gov/analysis/reeds/) is a capacity planning and dispatch model for the U.S. electricity system.

As NLR's flagship long-term power sector model, ReEDS has served as the primary analytic tool for [many studies](https://natlabrockies.github.io/ReEDS-2.0/publications.html) of electricity sector research questions.
Example model results are available in the [Scenario Viewer](https://scenarioviewer.nrel.gov/).




<a name="Software"></a>

## Quick-start guide

The ReEDS model is written in [Python](https://www.python.org/), [GAMS](https://www.gams.com/), and [Julia](https://julialang.org/).
Python and Julia are free, open-source languages;
GAMS requires a software license from the vendor.
A step-by-step guide for getting started with ReEDS is available [here](https://pages.github.nrel.gov/ReEDS/ReEDS-2.0/setup.html), and a quick-start guide for advanced users is outlined below.

1. Install Python using the Anaconda Distribution: <https://www.anaconda.com/download/success>
2. Set up GAMS:
    1. Install GAMS: <https://www.gams.com/download/>
    2. Obtain a combined GAMS/CPLEX license: <https://www.gams.com/sales/licensing/>
        1. Small ReEDS systems have been solved using the open-source [COIN-OR](https://www.coin-or.org/) solver as described [here](https://www.nrel.gov/docs/fy21osti/77907.pdf), but this capability is not actively maintained.
        2. Other commercial solvers have also been succussfully applied to ReEDS, but setup details and some solver tuning are specific to the CPLEX solver.
3. Install Julia: <https://julialang.org/downloads/>
4. Open a command-line interface and set up your environments:
    1. Clone the ReEDS repository: `git clone git@github.com:NatLabRockies/ReEDS-2.0.git` or `git clone https://github.com/NatLabRockies/ReEDS-2.0.git`
    2. Navigate to the cloned repository
    3. Create the `reeds2` [conda environment](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html): `conda env create -f environment.yml`
        1. Linux and Mac users can use the environment.yml directly. Windows users need to comment out the `- julia=1.8` line from the environment.yml file before creating the enviroment and use the version of Julia installed above.
    4. Activate the `reeds2` environment: `conda activate reeds2`
    5. Instantiate the Julia environment: `julia --project=. instantiate.jl`
5. Run ReEDS on a test case from the root of the cloned repository:
    1. For interactive setup: `python runbatch.py`
    2. For one-line operation: `python runbatch.py -b v20250314_main -c test`. In this example, "v20250314_main" is the prefix for a batch of cases, and "test" is the suffix of a cases_{}.csv file located in the root of the repository (in this case, cases_test.csv).




<a name="Contact"></a>

## Contact Us

If you have comments and/or questions, you can contact the ReEDS team at [ReEDS.Inquiries@nrel.gov](mailto:ReEDS.Inquiries@nrel.gov) or post a question on the [discussion pages](https://github.com/NatLabRockies/ReEDS-2.0/discussions).

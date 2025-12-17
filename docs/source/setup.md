# Getting Started 
The ReEDS model source code is available at no cost from the National Renewable Energy Laboratory. The ReEDS model can be downloaded or cloned from [https://github.com/NREL/ReEDS-2.0](https://github.com/NREL/ReEDS-2.0).

New users may also wish to start with some ReEDS training videos which are available on the NREL YouTube channel at [https://youtu.be/aGj3Jnspk9M?si=iqCRNn5MbGZc8ZIO](https://youtu.be/aGj3Jnspk9M?si=iqCRNn5MbGZc8ZIO).

## Computer Setup for Microsoft Windows 10
The setup and execustion of the ReEDS model can be accomplished using a command-line interpreter application and launching a command line interface (referred to as a "terminal window" in this documentation). For example, initiating the Windows Command Prompt application, i.e., cmd.exe, will launch a terminal window {numref}`figure-windows-command-prompt`. (Note: If you have issues using command prompt, try using anaconda prompt or a git bash window)

```{figure} figs/readme/cmd-prompt.png
:name: figure-windows-command-prompt

Screenshot of a Windows Command Prompt terminal window
```

**SUGGESTON:** use a command line emulator such as ConEmu ([https://conemu.github.io/](https://conemu.github.io/)) for a more user-friendly terminal. The screenshots of terminal windows shown in this document are taken using ConEmu.

**IMPORTANT:** Users should exercise Administrative Privileges when installing software. For example, right click on the installer executable for one of the required software (e.g., Anaconda3-2019.07-Windows-x86\_64.exe) and click on "Run as administrator" ({numref}`figure-run-as-admin`). Alternatively, right click on the executable for the command line interface (e.g., Command Prompt) and click on "Run as administrator" ({numref}`figure-run-as-admin-2`). Then run the required software installer executables from the command line.

```{figure} figs/readme/run-as-admin.png
:name: figure-run-as-admin

Screenshot of running an installer executable using "Run as administrator"
```

```{figure} figs/readme/run-as-admin-2.png
:name: figure-run-as-admin-2

Screenshot of running "Command Prompt" with "Run as administrator"
```

### Python Configuration

Install Anaconda: [https://www.anaconda.com/download](https://www.anaconda.com/download).

**IMPORTANT** : Be sure to download the Windows version of the installer.

Add Python to the "path" environment variable

1. In the Windows start menu, search for "environment variables" and click "Edit the system environment variables" ({numref}`figure-search-env-var`). This will open the "System Properties" window ({numref}`figure-sys-prop-win`).

```{figure} figs/readme/search-env-var.png
:name: figure-search-env-var

Screenshot of a search for "environment variables" in the Windows start menu
```

```{figure} figs/readme/sys-prop-win.png
:name: figure-sys-prop-win

Screenshot of the "System Properties" window.
```


2. Click the "Environment Variables" button on the bottom right of the window ({numref}`figure-sys-prop-win`). This will open the "Environment Variables" window ({numref}`figure-env-var-wind`).


```{figure} figs/readme/env-var-win.png
:name: figure-env-var-wind

Edit the Path environment variable
```


3. Highlight the Path variable and click "Edit" ({numref}`figure-env-var-wind`). This will open the "Edit environment variable" window ({numref}`figure-edit-env-var-win`).

```{figure} figs/readme/edit-env-var-win.png
:name: figure-edit-env-var-win

Append the Path environment
```


4. Click "New" ({numref}`figure-edit-env-var-win`) and add the directory locations for \Anaconda\ and \Anaconda\Scripts to the environment path.

**IMPORTANT** : Test the Python installation from the command line by typing "python" (no quotes) in the terminal window. The Python program should initiate ({numref}`figure-python-test`).

```{figure} figs/readme/py-test.png
:name: figure-python-test

Screenshot of a test of Python in the terminal window
```

It is highly recommended to run ReEDS using the conda environment provided in the repository. This environment (named `reeds2`) is specified by the `environment.yml` and can be built with the following command:

```
conda env create -f environment.yml
```

You can verify that the environment was successfully created using the following (you should see `reeds2` in the list):

```
conda env list
```

When creating the reeds2 environment locally, you might run into an SSL error that looks like: `CondaSSLError: Encountered an SSL error. Most likely a certificate verification issue.` To resolve this issue, run the following command before creating the environment again: `conda config --set ssl_verify false`.


### GAMS Configuration

Install GAMS: [https://www.gams.com/download/](https://www.gams.com/download/). NREL uses GAMS versions 49.6.0 and 45.2.0. Older versions might also work. A valid GAMS license must be installed. Please refer to the [Required Software](#Software) section above for more information.

Add GAMS to the "path" environment variable. Follow the same instructions as for adding Python to the path in the [Python Configuration](#ConfigPy) section above. Append the environment path with the directory location for the _gams.exe_ application (e.g., C:\GAMS\win64\34).


**IMPORTANT** : Test the GAMS installation from the command line by typing "gams" (no quotes) in the terminal window. The GAMS program should initiate ({numref}`figure-gams-test`).

```{figure} figs/readme/gams-test.png
:name: figure-gams-test

Screenshot of a test of GAMS from the terminal window
```


### ReEDS Repository Setup
The ReEDS source code is hosted on GitHub: [https://github.com/NREL/ReEDS-2.0](https://github.com/NREL/ReEDS-2.0)


1. Install Git Large File Storage, instructions can be found here: [Installing Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage?platform=windows)

1. From the Git command line run the following command to enable large file storage.
```
git lfs install
```

1. Clone the ReEDS-2.0 repository on your desktop. Alternatively, download a ZIP from GitHub ({numref}`figure-github-download`).

```{figure} figs/readme/github-download.png
:name: figure-github-download

Screenshot of GitHub links to clone the ReEDS repository or download ZIP of the ReEDS files
```



## Computer Setup for MacOS
### Python Configuration
Download the latest **Intel** version of Anaconda: [https://www.anaconda.com/download](https://www.anaconda.com/download)

**IMPORTANT**: Make sure to download the Intel version even if your machine has an Apple Silicon / ARM processor. 

```{figure} figs/readme/anaconda-intel.png
:name: figure-anaconda-intel
```

During Installation, select to install Anaconda for your machine only.

```{figure} figs/readme/anaconda-install-mac.png
:name: figure-anaconda-install-mac

Image of Anaconda Install Mac
```

To have the installer automatically add anaconda to PATH, ensure that you've selected the box to "Add conda initialization to the shell"

```{figure} figs/readme/anaconda-custom-install-mac.png
:name: figure-anaconda-custom-insatll-mac

Image of Anaconda Install Mac - Customize Installation Type
```

**To validate Python was installed properly** execute the following command from a new terminal (without quotes): "python"

Python should initiate, looking similar to {numref}`figure-python-test`.

It is highly recommended to run ReEDS using the conda environment provided in the repository. This environment (named `reeds2`) is specified by the `environment.yml` and can be built with the following command - make sure you navigate to the ReEDS repository from terminal first: 

```
conda env create -f environment.yml
```

You can verify that the environment was successfully created using the following (you should see `reeds2` in the list):

```
conda env list
```


### GAMS Configuration 
Install GAMS: [https://www.gams.com/download/](https://www.gams.com/download/). A valid GAMS license must be installed. Please refer to the [Required Software](#Software) section above for more information.

**IMPORTANT**: When installing on Mac, on the 'Installlation Type' page, click 'customize' and ensure the box to 'Add GAMS to PATH' is checked.

```{figure} figs/readme/gams-install-mac.png
:name: figure-gams-install-mac

Image of GAMS Install Mac
```

**To validate GAMS was installed properly** execute the following command from a new terminal (without quotes): "gams"

GAMS should initiate, you should see something similar to {numref}`figure-gams-test`.



### ReEDS Repository Setup
The ReEDS source code is hosted on GitHub: [https://github.com/NREL/ReEDS-2.0](https://github.com/NREL/ReEDS-2.0)

1. Install Git Large File Storage, instructions can be found here: [Installing Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage?platform=mac)

2. From the Git command line run the following command to enable large file storage.
```
git lfs install
```

3. Clone the ReEDS-2.0 repository on your desktop and use the repository with GitHub Desktop. Alternatively, download a ZIP from GitHub ({numref}`figure-github-download`).

## ReEDS2PRAS, julia, and stress periods setup
Since ReEDS uses stress periods by default, julia will need to be installed and set up to run the model. To get julia and stress periods set up: 
1. Install Julia. There are different procedures for mac/linux and windows.
    1. [mac/linux]: Julia is included in the conda environment so you should be all set.
    2. [windows]: Install Julia from [https://julialang.org/downloads/](https://julialang.org/downloads/).
2. From the ReEDS-2.0 directory, run `julia --project=. instantiate.jl`

Set `GSw_PRM_CapCredit=0` in your ReEDS cases file to use the coupled ReEDS/PRAS stress periods model, or just set `pras=2` to run PRAS without necessarily using stress periods.

### Troubleshooting Issues with Julia Setup
When setting up julia on Windows, you may run into some issues when running `julia --project=. instantiate.jl`. The following steps can be followed to help resolve issues and get julia set up sucessfully: 
1. Manually install [Random123](https://github.com/JuliaRandom/Random123.jl) 

2. Re-run `julia --project=. instantiate.jl`



If that doesn't resolve the issue, the following may help: 
1. If you previously installed julia, uninstall it: `winget uninstall julia`

2. Manually install [Julia 1.8.5](https://julialang.org/downloads/oldreleases/#:~:text=ea85e0489c36324c4da62163aa1b82fcf2f52f72d173ee7dd213a3a92992cab7-,Windows,-x86_64)

3. Add the julia bin path to your environment PATH variable

4. Install [MinGW](https://www.mingw-w64.org/downloads/) 

5. Open the julia interactive command line: `julia`

6. Enter the julia package manager by pressing `]`, then run the following commands:
    * `add Random123`   
    * `registry add https://github.com/JuliaRegistries/General.git`
    * `registry add https://github.com/NREL/JuliaRegistires.git`
    * `instantiate`

7. Leave the package manager by pressing backspace or Ctrl+C

8. Run the following commands to finish setup: 
    * `import PRAS`
    * `import TimeZones`
    * `TimeZones.build()`

9. You can then leave the julia command line by typing `exit()`


**If you're experiencing issues on Mac, a possible solution is:**
1. Update the version of julia

2. Create the 'reeds2' conda environment with the environment.yml file

3. Run `julia` from the terminal to open the interactive command line

4. Run `import Pkg; Pkg.add("PRAS")`

5. Run `Pkg.add("TimeZones")`

6. Exit julia with the command `exit()`, then run `julia instantiate.jl`

7. Manually move the Manifest.toml file from the julia environment (~/miniconda3/envs/reeds2/share/julia/environments/reeds2/Manifest.toml) to the ReEDS repo


## Executing the Model
A ReEDS case (also referred to as a "run", "scenario" or "instance") is executed through a python-based case batching program called `runbatch.py` after the repository was setup. The user can execute a single case or a batch of cases using this program.

### Understanding the cases.csv file
ReEDS model switches are set in the cases.csv file and need to be specified by the user. The default case configuration file is called "cases.csv".

Within "cases.csv", the data in column A are the model "switches". Column B contains a brief description of each switch. Column C contains the choices available for the given switch (please note, this is not available for all switches). Column D contains the default value for the switch. Finally, the case configuration (or set of switches that define a case) is in column E. 

Within column E, the case name is specified in row 1. The value for each switch is specified beginning in row 2. If a switch value is left blank, the default value from column D is used. 

**Note:** all monetary switches should be entered in 2004 dollars.

```{figure} figs/readme/cases-csv.png
:name: figure-cases-csv

Screenshot of cases.csv
```

There are additional cases_*.csv files that can also be used to run different ReEDS scenarios. The two most commonly used are:
   * cases_standardscenarios.csv: contains all the scenarios that were used for Standard Scenarios
   * cases_test.csv: contains a group of "test" cases that vary specific settings within the model for testing various capabilities

The user may also create custom case configuration files by using the suffix in the file name (e.g., "cases_smalltests.csv"). It should follow the same column formatting as cases.csv, but does not need to include all available switches.

### Calling runbatch.py to run ReEDS
1. Navigate to the ReEDS directory from a new command prompt or terminal.
2. Activate the `reeds2` conda environment: `conda activate reeds2`
3. Call runbatch.py: `python runbatch.py`
   * It should look similar to {numref}`figure-exe-runbatch`
4. Provide responses to the suite of prompts in the command line. For more information about the prompts, see the [Prompts for user input during runbatch.py section](#prompts-for-user-input-during-runbatchpy).
5. Once all responses have been received, the batching program will execute the case(s) specified in the case configuration file (e.g., "cases.csv").
   * Please note, if you're running ReEDS on Windows, a separate terminal window will be launched for each case.

For each case that is run, a new subfolder will be created under the "runs/" subdirectory of ReEDS. If you run the default case found in "cases.csv", you can expect to find the outputs from the run at "/ReEDS-2.0/runs/{batch prefix}_Ref/outputs".

```{figure} figs/readme/exe-runbatch.png
:name: figure-exe-runbatch

Screenshot of initiating "runbatch.py" from the command line
```


### Prompts for user input during runbatch.py 
**Batch Prefix [string]** - Defines the prefix for files and directories that will be created for the batch of cases to be executed (as listed in a case configuration file, e.g., "cases.csv")
   * All files and directories related to a case will be named "{batch prefix}_{case}". For example, if *batch prefix = "test"* and *case = "Ref"*, then all files and directories related to this case will be named *test_Ref*. 
   * **Important:** A batch prefix cannot start with a number given incompatibility with GAMS.
   * Entering the value of "0" (zero, no quotes) will assign the current date and time for the batch prefix in the form of *v{YYYMMDD}_{HHMM}*. 
   * If you re-use a (batch prefix, case) pair, a new prompt will appear asking if you want to overwrite the existing output directories.
    
**Case Suffix [string]** - Indicates which case configuration file (in the form "cases_{case suffix}.csv") is ingested into "runbatch.py" for processing.
   * Entering an empty value(i.e., pressing "Enter/Return") will cause the default case configuration file "cases.csv" to be used

**Number of Simultaneous Runs [integer]** - Indicated how many cases should be run simultaneously.
   * "runbatch.py" uses a queue to execute multiple cases
   * If there are 4 cases and the *Number of Simultaneous Runs = 1*, then "runbatch.py" will execute the cases one at a time
   * However, if there are 4 cases and the *Number of Simultaneous Runs = 2*, then "runbatch.py" will start 2 cases simultaneously
      * As each case finishes, it will start a new one until all cases have been run
   * **WARNING! Be mindful about the amount of CPU and RAM usage needed for each case**

### Checking the outputs
To check if a run was successful, you can look in the following two places: 
- The 'runs/[batchname_scenario]/outputs' folder should have csv files, if it doesn't, something went wrong.
- There should be a 'reeds-report' and reeds-report-reduced' folder in the outputs folder for a specific run.


### Special Case Setup Requirements

For non-NREL users, some additional data is required to run the ReEDS model at the 'county' spatial resolution. This is currently considered a special case and some data was required to be kept outside the ReEDS repository because the data is simply too large. The hourly renewable capacity factor data is now available to all at : [https://data.openei.org/submissions/5986](https://data.openei.org/submissions/5986).

If you would like to run the model at county resolution, you are requested to download the files available from the link provided, unzip each folder, and place the files obtained into inputs/variability/multi-year in your locally cloned ReEDS repository. The input_processing scripts have also been updated to check for these files for any county-level runs. The 'cases_spatialflex.csv' file provides examples of specific switch settings to run ReEDS at county-level.

## NREL Specific Setup
For more information on NREL specific setup, refer to the [Internal ReEDS Documentation](https://nrel.sharepoint.com/:w:/s/ReEDS/Efathg8KjjtCkxW44vZpWQQBA2KsU3RadSsVauBMskEfUA?e=YaSIqc). You can find information there on Yampa and HPC setup, as well as the onboarding guide.

## Additional Resources
NREL has a YouTube channel that contains tutorial videos for ReEDS. The following are recommended videos for getting started with ReEDS: 
- Overview of ReEDS
  - [Introduction to the ReEDS Model: 2023 Version](https://www.youtube.com/watch?v=6SNxMWoBVr0&amp;list=PLmIn8Hncs7bG558qNlmz2QbKhsv7QCKiC&amp;index=11)
  - [Powered by ReEDS](https://www.youtube.com/watch?v=qLHdWh3uoHk)
- Getting started with ReEDS: [2023 ReEDS Training for User Group Meeting](https://www.youtube.com/watch?v=tDLwqH6YZ_E&amp;list=PLmIn8Hncs7bG558qNlmz2QbKhsv7QCKiC&amp;index=12)
- How to change inputs: [Training on Changing and Adding Inputs](https://www.youtube.com/watch?v=QxwEs0ZC5ns&amp;list=PLmIn8Hncs7bG558qNlmz2QbKhsv7QCKiC&amp;index=9)
- Debugging of ReEDS: [Training on Debugging ReEDS](https://www.youtube.com/watch?v=4I0V5F8fzDU&amp;list=PLmIn8Hncs7bG558qNlmz2QbKhsv7QCKiC&amp;index=8)

If you'd like practice with running a specific ReEDS scenario, you can walk through the [ReEDS Training Homework](reeds_training_homework).

Additional resources and learning:
* [General information on ReEDS](https://www.nrel.gov/analysis/reeds/)
* [ReEDS POC list](https://nrel.sharepoint.com/:w:/s/ReEDS/ES6GQTyzXo1DnnCPlnAhg5QB8cPY--_01HkQkiOnrPskxw?e=flEAtY)
* [GitHub README](https://github.nrel.gov/ReEDS/ReEDS-2.0/blob/main/README.md)
* [YouTube tutorials](https://www.youtube.com/playlist?list=PLmIn8Hncs7bG558qNlmz2QbKhsv7QCKiC)
* [GAMS language information](https://www.gams.com/latest/docs/UG_MAIN.html#UG_Language_Environment)
* [Tips and tricks for the bash shell](https://nrel-my.sharepoint.com/:p:/r/personal/ssundar_nrel_gov/Documents/Microsoft%20Teams%20Chat%20Files/02062024_what_the_shell.pptx?d=wa7aea3514f814d51924bf2dfa737d414&csf=1&web=1&e=qr1YuP)
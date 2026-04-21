import pandas as pd
import os
import shutil
from glob import glob

outfiles = [
    "cap",
    "cap_ivrt",
    "cap_energy_ivrt",
    "cap_new_ivrt",
    "cap_new_ann_nat",
    "capex_ivrt",
    "costnew",
    "curt_tech",
    "curt_h",
    "emit_nat",
    "expenditure_flow",
    "gen_ivrt",
    "gen_ann",
    "gen_plant_ivrt",
    "gen_objcoef",
    "gen_h",
    "gen_h_stress",
    "gen_plant_h",
    "gen_plant_h_stress",
    "gen_storage_h",
    "gen_storage_h_stress",
    "health_damages_caused_r",
    "hours",
    "storage_in_plant_h",
    "storage_in_grid_h",
    "lcoe",
    "lcoe_built",
    "lcoe_cf_act",
    "lcoe_pieces",
    "pvf_capital",
    "pvf_onm",
    "rec_outputs",
    "reduced_cost",
    "balance_rc",
    "flow_objcoef",
    "flow_rc",
    "RE_gen_price_nat",
    "reqt_price",
    "reqt_price_sys",
    "reqt_quant",
    "revenue",
    "revenue_en",
    "revenue_cap",
    "stor_in",
    "stor_in_plant",
    "stor_in_grid",
    "stor_interday_level",
    "stor_interday_dispatch",
    "stor_level",
    "stor_out",
    "hybrid_stor_out",
    "systemcost",
    "systemcost_techba",
    "tran_flow_rep",
    "tran_flow_rep_ann",
    "tran_mi_out",
    "tran_mi_out_detail",
    "tran_util_h_rep",
    "tran_util_ann_rep",
    "tran_limit_price",
    "net_import_h_rep",
    "import_h_rep",
    "import_ann_rep",
    "export_h_rep",
    "export_ann_rep",
    "valnew",
    ]

# prefix = input("Enter the batch prefix of the case to read the files from: ")
# casefile = input("Enter the name of the cases file to read the files from: ")
savefile = "Ethan_runs_03_26_2026_2"
batch_name = '03_26_2026'
reeds_path = os.path.dirname(os.path.abspath(__file__))
print(reeds_path)
#%% Get all runs
runs_all = sorted(glob(os.path.join(reeds_path,'runs',batch_name+'*')))

os.makedirs(os.path.join(reeds_path, savefile), exist_ok=True)

# Loop through runs_all and copy the outfiles to the savefile directory
for run in runs_all:
    run_name = os.path.basename(run)
    for outfile in outfiles:
        src = os.path.join(run, 'outputs', outfile + '.csv')
        dst = os.path.join(reeds_path, savefile, f"{run_name}_{outfile}.csv")
        if os.path.exists(src):
            shutil.copy(src, dst)
        else:
            print(f"File {src} does not exist and will be skipped.")

# Now zip the savefile directory
shutil.make_archive(savefile, 'zip', savefile)

    


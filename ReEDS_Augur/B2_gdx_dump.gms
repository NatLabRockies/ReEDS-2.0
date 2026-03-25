*Setting the default directory separator
$setglobal ds \

*Change the default slash if in UNIX
$ifthen.unix %system.filesys% == UNIX
$setglobal ds /
$endif.unix

$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx" format=csv epsout=0 symb=prices > "ReEDS_Augur%ds%augur_data%ds%prices_%prev_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx" format=csv epsout=0 symb=flows_output > "ReEDS_Augur%ds%augur_data%ds%flows_%prev_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx" format=csv epsout=0 symb=gen_output > "ReEDS_Augur%ds%augur_data%ds%gen_%prev_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx" format=csv epsout=0 symb=storage_in_output > "ReEDS_Augur%ds%augur_data%ds%storage_in_%prev_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx" format=csv epsout=0 symb=dr_inc_output > "ReEDS_Augur%ds%augur_data%ds%dr_inc_%prev_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx" format=csv epsout=0 symb=dropped_load_output > "ReEDS_Augur%ds%augur_data%ds%dropped_load_%prev_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx" format=csv epsout=0 symb=produce_output > "ReEDS_Augur%ds%augur_data%ds%produce_%prev_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx" format=csv epsout=0 symb=storage_level_output > "ReEDS_Augur%ds%augur_data%ds%storage_level_%prev_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx" format=csv epsout=0 symb=conversion_output > "ReEDS_Augur%ds%augur_data%ds%conversion_%prev_year%.csv" '
$call 'gdxdump "ReEDS_Augur%ds%augur_data%ds%osprey_outputs_%prev_year%.gdx" format=csv epsout=0 symb=cf_output > "ReEDS_Augur%ds%augur_data%ds%cf_%prev_year%.csv" '

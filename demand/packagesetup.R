
print("")
print("Installing necessary packages")
print("")

list.of.packages <- c(	"plyr","lazyeval","colorspace","data.table",
						"dplyr","dtplyr","ggplot2","ggthemes","grid","gtools",
						"reshape2","rlang","scales","stringr","stringi",
						"xtable","zoo","tibble")


#packages used only on the demand side, 
#                   no longer used,
#                   or installed via dependency:
#"RColorBrewer",
#"taRifx"
#"doBy"
#"iterators"
#"openxlsx"
#"doParallel"
#"lpSolve"
#"MASS"

new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos = "http://cran.rstudio.com/", dep = TRUE)

get_os <- function() {
  if (.Platform$OS.type == "windows") { 
    "win"
  } else if (Sys.info()["sysname"] == "Darwin") {
    "mac" 
  } else if (.Platform$OS.type == "unix") { 
    "unix"
  } else {
    stop("Unknown OS")
  }
}

osname = get_os()

if(!("gdxrrw") %in% installed.packages()[,"Package"]){
	if (osname=="win"){install.packages(file.path("input_processing","R","gdxrrw_0.4.0.zip"), repos = NULL)}
	if (osname=="mac"){install.packages(file.path("input_processing","R","gdxrrw_1.0.5.tgz"), repos = NULL)}
	if (osname=="unix"){install.packages(file.path("input_processing","R","gdxrrw_1.0.5_r_x86_64-redhat-linux-gnu.tar.gz"), repos = NULL)}
}

######################################################
## Check to see if packages are installed correctly ##
######################################################

for(i in c(list.of.packages,"gdxrrw")) {
	if (!suppressMessages(require(i,character.only = TRUE)))
		{print(paste("Package",i,"not installed correctly"))}
		else 
		{print(paste("Package",i,"installed correctly"))}
}



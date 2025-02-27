# pre_basher_filter

This script is desinged to run on Windows machine. It can be run as a stanalone python script or wrapped into the .exe file. 

To run standalone python script, download the github repo from https://github.com/moka-guys/pre_basher_filter

To run the script on Windows --> python filter.py -d <path/to/dir/for/rhchp_files>

To build into .exe --> python -m PyInstaller --onefile --add-data "<file/path/to/MSVtool>;." .\filter.py. This will generate the filter.exe in "dist" folder

To run exe file --> .\dist\filter.exe -d <path/to/dir/for/rhchp_files>

The tool has optional input args to filter by chromosome and POS. For that use the flag -c (for seleted chromosome), --start and --end for POS. 

***How the tool works***
The tool converts all rhchp files in the given dir to txt file by running the MSV tool. The converted txt files are filtered to remove the bad snp using the reference excel sheet "HT-CMA hg38 genome coverage.xlsx". The filtered txt files are combined into one txt file which is to be used as Basher output.

***Refrence files required***
- CytoScan_HTCMA_96.na36.r3.a1.annot.db - required for converting the rhchp file to txt file
- MSV.CNGenotypeExportTool.exe - thermofisher tool used to convert the rhchp file to txt file
- HT-CMA hg38 genome coverage.xlsx - refernece SNP file to filter bad SNP

***Input***
- file dir - str to direct the folder where rhchp files are located (-d or --file_dir)
- chromosome number - int/str for chromosome to filter (optional) (-c or --chr)
- start - int for start position to filter (opitional) (--start)
- end - int for end position to filter (optional) (--end)

***Output***
- combined filtered txt file to be used as a Basher input
- log file 
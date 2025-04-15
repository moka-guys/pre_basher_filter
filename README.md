# pre_basher_filter
The tool has two mode (option1 and option2). Option1 converts all rhchp files (if not specify) in the given dir to txt files by running the MSV.CNGenotypeExportTool. The converted txt files are filtered to remove the unwanted snp using the reference excel sheet "HT-CMA hg38 genome coverage.xlsx". The filtered txt files are combined into one txt file which is to be used as Basher input. Option2 uses already converted single txt file as an input and filters out the unwanted SNP.

To run standalone python script, download the github repo from https://github.com/moka-guys/pre_basher_filter

To run option1 --> `python filter.py -d </dir/for/rhchp_files>`
To run option2 --> `python filter.py -d </dir/for/rhchp_files> -m opiton2 -i <txt file name>`


The tool has optional input args to filter by chromosome and POS. For that, use the flag -c (for selected chromosome), --start and --end for POS. 

***Requirements***
- CytoScan_HTCMA_96.na36.r4.a1.annot.db - required for converting the rhchp file to txt file.
- MSV.CNGenotypeExportTool.exe (tool from Thermofisher)
- HT-CMA hg38 genome coverage.xlsx - reference file used to filter the unwanted SNP

***Input***
- file dir - str to direct the folder where rhchp files are located (-d or --file_dir)
- mode to run - str to choose mode (optional for option1) (-m or --mode) 
- chromosome number - int/str for chromosome to filter (optional) (-c or --chr)
- start - int for start position to filter (optional) (--start)
- end - int for end position to filter (optional) (--end)
- ref file - str to direct the file path for reference file (optional) (-r, --snp_ref)
- msv tool - str to direct the path for msv tool (optional) (--msv)
- annot file - str to direct the path for annot file (optional) (-a or --annot)
- included files - list of file(s) to include to filter (compulsory in option2) (-i or --included)

***Note*** if the optional inputs are not provided, either default values are taken or the input args are not used.

***Output***
These two ouput files are genearted in the subfolder named "filtered_array_output"
- combined filtered txt file to be used as a BASHer input
- log file 
Note: if option1 is used, the converted txt files are generated in the same dir as rhchp files.

Please see more detailed doc here https://seglh.atlassian.net/wiki/spaces/~63bc0b8427c8920a5c01e2e6/pages/380862466/How+to+run+pre_basher_filter+on+Windows



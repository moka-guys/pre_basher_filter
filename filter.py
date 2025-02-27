import os
import subprocess
import argparse
import pandas as pd
import logging
    
logger = logging.getLogger(__name__)

def get_log() -> None:
    """
    Set for log file
        Return: None
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler('D:/Downloads/wmt/basher_filter_log.log') # need to update
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

def conversion(file_dir) -> None:
    """
    Convert the rhchp file to txt file using MSV tool from Thermofisher
        Return: None
    """
    all_files = os.listdir(file_dir)
    rhchp_files = [item for item in all_files if item.endswith('.rhchp') and os.path.isfile(os.path.join(file_dir, item))]
    for rhchp in rhchp_files:
        rhchp_file = os.path.join(file_dir, rhchp)
        file_name = os.path.splitext(os.path.basename(rhchp))[0]
        file_name1 = os.path.join(file_dir, file_name)
        powershell_command = f"D:\Downloads\wmt\MSV.CNGenotypeExportTool\MSV.CNGenotypeExportTool.exe --input {rhchp_file} --output {file_name1}.txt" #update

        # Run PowerShell through subprocess
        process = subprocess.Popen(["powershell", "-Command", powershell_command], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True)
        # Get the output and errors (if any)
        output, error = process.communicate()
        # Print the output
        if output:
            logger.info(f"{rhchp} is successfully converted into {file_name}.txt")
        # Print the error (if any)
        if error:
            print("Error:\n", error)
            logger.error(f"Error while converting {rhchp} to txt file")


def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments
    and help menu
        Return argparse.Namespace (object): Contains the parsed arguments
    """
    parser = argparse.ArgumentParser(
    description=(
    "Given an input samplesheet, will validate the samplesheet using "
    "seglh-naming conventions and output a logfile"
    ),
    usage="Used to validate a samplesheet using the seglh-naming conventions",
    )
    parser.add_argument(
    "-d",
    "--file_dir",
    required=True,
    help="Dir to rhchp files",
    )
    parser.add_argument(
    "-c",
    "--chr",
    help="chromosome number to filter",
    )
    parser.add_argument(
    "--start",
    help="chromosome start to filter",
    )
    parser.add_argument(
    "--end",
    help="chromosome start to filter",
    )    
    return parser.parse_args()


def filter_combine(file_dir) -> None:
    """
    Filter the array file for only good snp and combine all files into a single txt file
    """
    good_snp_df = pd.read_excel("D:/Downloads/HT-CMA hg38 genome coverage.xlsx", sheet_name="Filtered SNPs good data set",
    usecols=['probeset_id', "Chr", "Position"]) # can read only probeset ID, update
    all_files = os.listdir(file_dir)
    txt_files = [item for item in all_files if item.endswith('.txt') and os.path.isfile(os.path.join(file_dir, item))]
    dfs = []
    n = 1
    sanity_check = []
    for array in txt_files:
        logger.info(f"{array} is now filtered")
        array_df = pd.read_csv(os.path.join(file_dir, array), sep="\t", low_memory=False)
        array_df = array_df[["ProbeSetID", "Chr", "Position", "CallCode"]]#
        array_df.rename({'ProbeSetID': 'probeset_id'}, axis=1, inplace=True)
        filtered_df = pd.merge(good_snp_df, array_df, on=['probeset_id'], how='inner')
        filtered_df.reset_index(drop=True, inplace=True)
        col_name = os.path.splitext(os.path.basename(array))[0]
        filtered_df.rename({'Chr_x': 'Chr', 'Position_x': 'Position', "CallCode" : col_name}, axis=1, inplace=True)
        filtered_df = filtered_df[["probeset_id", "Chr", "Position", col_name]]

        # filter with chromosome if given
        if parsed_args.chr is not None:
            filtered_chr_df = filtered_df[filtered_df["Chr"] == parsed_args.chr]
            filtered_chr_df.reset_index(drop=True, inplace=True)
            filtered_df = filtered_chr_df
            logger.info("{array} file is filtered with Chr number")

        # filter with position if given
        if (parsed_args.start is not None) & (parsed_args.end is not None):            
            filtered_pos_df = filtered_df[(filtered_chr_df["Position"] >= int(parsed_args.start)) & (filtered_df["Position"] <= int(parsed_args.end))]
            filtered_pos_df.reset_index(drop=True, inplace=True)
            filtered_df = filtered_pos_df
            logger.info("{array} file is filtered wiht Position")

        sanity_check.append(len(filtered_df))
        if n == 1:
            dfs = filtered_df
        else:
            dfs = pd.merge(dfs, filtered_df[['probeset_id', col_name]], on='probeset_id', how='left')
        n = n+1
        logger.info("complete filtering")

    # save as txt file 
    dfs.to_csv(os.path.join(file_dir, "combined.txt"), index=False)
    logger.info("combined filtered array file is saved as")

    # do sanity check
    if len(list(set(sanity_check))) > 1:
        print("check error")
        logger.error(f"Error with filtering so the number of SNP in individual files are not consistent")
        raise SystemExit()
    

if __name__== "__main__":
    print("Current working directory:", os.getcwd())    
    parsed_args = get_arguments()
    get_log()
    # convert file to txt
    conversion(parsed_args.file_dir)
    # filter snp
    filter_combine(parsed_args.file_dir)

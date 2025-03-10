import os
import sys
import subprocess
import argparse
import logging
import pandas as pd
logger = logging.getLogger(__name__)


def get_log(log_file) -> None:
    """
    Setup for log file
        Return: None
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_file) # need to update 'D:/Downloads/wmt/basher_filter_log.log'
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def conversion(file_dir, msv_tool) -> list:
    """
    Convert the rhchp file to txt file using MSV tool from Thermofisher
        Return: list of converted files
    """
    check_exist(msv_tool)
    annot_file = "C:/Users/Public/Documents/RhAS/Library/CytoScan_HTCMA_96.r3.1/CytoScan_HTCMA_96.na36.r3.a1.annot.db"
    check_exist(annot_file)
    converted_files = []
    all_files = os.listdir(file_dir)
    rhchp_files = [item for item in all_files if item.endswith('.rhchp') and
                   os.path.isfile(os.path.join(file_dir, item))]
    if len(rhchp_files) < 1:
        logger.error("There is no rhchp file in the given folder")
        sys.exit(1)
    for rhchp in rhchp_files:
        rhchp_file = os.path.join(file_dir, rhchp)
        file_name = os.path.splitext(os.path.basename(rhchp))[0]
        txt_file_name = os.path.join(file_dir, file_name)
        powershell_command = f"{msv_tool} --input {rhchp_file} --output {txt_file_name}.txt" #update D:\Downloads\wmt\MSV.CNGenotypeExportTool\MSV.CNGenotypeExportTool.exe

        # Run PowerShell through subprocess
        process = subprocess.Popen(["powershell", "-Command",
                                   powershell_command],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)
        # Get the output and errors (if any)
        output, error = process.communicate()
        if output:
            converted_files.append(f"{file_name}.txt")
            logger.info(f"{rhchp} is successfully converted into {file_name}.txt")
        if error:
            print("Error:\n", error)
            logger.error(f"Error while converting {rhchp} to txt file")
    logger.info(f"total {len(converted_files)} rhchp files are converted to txt file")
    return converted_files


def get_arguments() -> argparse.Namespace:
    """
    Uses argparse module to define and handle command line input arguments
    and help menu
        Return argparse.Namespace (object): Contains the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=(
            "Given an input rhchp file(s), will convert them into the txt file(s) and  "
            "the unwanted SNP are filtered out"
        ),
        usage="Used to filter SNP array filter before inputting into BASHER app",
        )
    parser.add_argument(
        "-d",
        "--file_dir",
        required=True,
        help="Dir to rhchp file(s)",
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
    parser.add_argument(
        "-L",
        "--log",
        default="D:/Downloads/wmt/basher_filter_log.log",
        help="path to log file",
        )
    parser.add_argument(
        "--msv",
        default='D:/Downloads/wmt/MSV.CNGenotypeExportTool/MSV.CNGenotypeExportTool.exe',
        help="path to MSV tool",
        )  
    parser.add_argument(
        "-r",
        "--snp_ref",
        default="D:/Downloads/HT-CMA hg38 genome coverage.xlsx",
        help="path to ref file to filter snp",
        )
    return parser.parse_args()


def filter_combine(args, **kwargs) -> None:
    """
    Filter the array file(s) by removing unwanted SNP and combine all files into a single txt file
    """
    check_exist(args.snp_ref)
    good_snp_df = pd.read_excel(args.snp_ref, sheet_name="Filtered SNPs good data set",
                                usecols=['probeset_id']) # update "D:/Downloads/HT-CMA hg38 genome coverage.xlsx" , "Chr", "Position"
    try:
        converted_files
    except:
        all_files = os.listdir(args.file_dir)
        txt_files = [item for item in all_files if item.endswith('.txt') and os.path.isfile(os.path.join(args.file_dir, item))]
        if len(txt_files) < 1:
            logger.error("There is no txt file in the given folder")
            sys.exit(1)
        print("not using converted append file")
    else:
        txt_files = converted_files
        print("used converted append files")
    dfs = []
    n = 1
    sanity_check = []
    for array in txt_files:
        array_df = pd.read_csv(os.path.join(args.file_dir, array), sep="\t", low_memory=False)
        array_df = array_df[["ProbeSetID", "Chr", "Position", "CallCode"]]
        array_df.rename({'ProbeSetID': 'probeset_id'}, axis=1, inplace=True)
        filtered_df = pd.merge(good_snp_df, array_df, on=['probeset_id'], how='inner')
        filtered_df.reset_index(drop=True, inplace=True)
        col_name = os.path.splitext(os.path.basename(array))[0]
        filtered_df.rename({'Chr_x': 'Chr', 'Position_x': 'Position', "CallCode" : col_name}, axis=1, inplace=True)
        filtered_df = filtered_df[["probeset_id", "Chr", "Position", col_name]]
        logger.info(f"{array} has been filtered")

        # filter with chromosome if given
        if args.chr is not None:
            args.chr = str(args.chr)
            filtered_df["Chr"] = filtered_df["Chr"].astype(str)
            filtered_chr_df = filtered_df[filtered_df["Chr"] == args.chr]
            filtered_chr_df.reset_index(drop=True, inplace=True)
            filtered_df = filtered_chr_df
            logger.info(f"{array} file is filtered with Chr {args.chr}")

        # filter with position if given
        if (args.start is not None) & (args.end is not None):
            filtered_df["Position"] = filtered_df["Position"].astype(int)
            filtered_pos_df = filtered_df[(filtered_df["Position"] >= int(args.start)) & (filtered_df["Position"] <= int(args.end))]
            filtered_pos_df.reset_index(drop=True, inplace=True)
            filtered_df = filtered_pos_df
            logger.info(f"{array} file is filtered with Position from {args.start} to {args.end}")

        sanity_check.append(len(filtered_df))
        if n == 1:
            dfs = filtered_df
        else:
            dfs = pd.merge(dfs, filtered_df[['probeset_id', col_name]], on='probeset_id', how='left')
        n = n+1
        logger.info("complete filtering")

    # save as txt file
    outdir = os.path.join(args.file_dir, "filtered_array_output")
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        logger.info("Output folder is created")
    else:
        logger.info("Output folder already exists")

    dfs.to_csv(os.path.join(outdir, "combined_filtered_array.txt"), index=False)
    logger.info("combined filtered array file is saved")

    # do sanity check
    if len(list(set(sanity_check))) > 1:
        print("check error")
        logger.error("Error with filtering so the number of SNP in individual files are not consistent")
        sys.exit(1)


def check_exist(file_path):
    if os.path.exists(file_path):
        logger.info(f"{file_path} exists")
    else:
        logger.error(f"{file_path} does not exist")
        sys.exit(1)


if __name__ == "__main__":
    print("Current working directory:", os.getcwd())    
    parsed_args = get_arguments()
    get_log(parsed_args.log)
    # convert file to txt
    #converted_files = conversion(parsed_args.file_dir, parsed_args.msv)
    converted_files = ["test.txt", "test1.txt"]
    # filter snp
    try:
        converted_files
    except:
        print("not using converted append file")
        filter_combine(parsed_args)        
    else:
        print("used converted append file")
        filter_combine(parsed_args, converted_files=converted_files)


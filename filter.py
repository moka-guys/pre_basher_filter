import os
import sys
import subprocess
import argparse
import logging
from datetime import datetime
import pandas as pd
#import config

logger = logging.getLogger(__name__)
now = datetime.now()
datetimestr = now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond // 1000:03}"


def get_arguments() -> argparse.Namespace:
    """
    Uses argparse to define and handle command line input arguments
    and help menu
        Return argparse.Namespace (object): Contains the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=(
            "Given an input rhchp file(s), convert them into "
            "the txt file(s) and the unwanted SNP are filtered out"
        ),
        usage="Used to filter SNP array file before inputting into BASHer",
        )
    parser.add_argument(
        "-d",
        "--file_dir",
        required=True,
        help="dir to rhchp file(s)",
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
        help="chromosome end to filter",
        )
    parser.add_argument(
        "--msv",
        default="S:/Genetics/Bioinformatics/Software/pre-basher/MSV.CNGenotypeExportTool/MSV.CNGenotypeExportTool.exe",
        help="path to MSV tool",
        )
    parser.add_argument(
        "-r",
        "--snp_ref",
        default="S:/Genetics/DNA LAB/Current/PGD/pgd results/SNP array/Excels & BED files/HT-CMA hg38 genome coverage.xlsx",
        help="path to ref file to filter snp",
        )
    parser.add_argument(
        "-a",
        "--annot",
        default="S:/Genetics/Bioinformatics/Software/pre-basher/CytoScan_HTCMA_96.na36.r4.a1.annot.db",
        help="path to annot file for MSV tool",
        )
    parser.add_argument(
        "-i",
        "--included",
        type=str,
        nargs="+",
        help="specify file(s) to be included, required if mode is option2",
        )
    parser.add_argument(
        "-m",
        "--mode",
        default="option1",
        help=("mode of filtering, either option1 or option2. "
              "option1 converts and filters using rhchp as input. "
              "option2 filters txt file as input"),
        )
    return parser.parse_args()


def get_log(file_dir) -> None:
    """
    Setup for log file
        Return: None
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    outdir = os.path.join(file_dir, "filtered_array_output")
    log_file = os.path.join(outdir, "pre_basher_filter_log.log")
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def conversion(args) -> list:
    """
    Convert the rhchp file to txt file using MSV tool from Thermofisher
        Return: list of converted files
    """
    check_exist(args.msv)
    annot_file = args.annot
    check_exist(annot_file)
    converted_files = []
    all_files = os.listdir(args.file_dir)

    if args.included is not None:
        rhchp_files = args.included
    else:
        rhchp_files = [item for item in all_files if item.endswith(".rhchp")
                       and os.path.isfile(os.path.join(args.file_dir, item))]
    if len(rhchp_files) < 1:
        logger.error("There is no rhchp file in the given folder")
        sys.exit(1)
    for rhchp in rhchp_files:
        rhchp_file = os.path.join(args.file_dir, rhchp)
        file_name = os.path.splitext(os.path.basename(rhchp))[0]
        txt_file_name = os.path.join(args.file_dir, file_name)
        powershell_command = (f"{args.msv} --input {rhchp_file} "
                              f"--output {txt_file_name}.txt "
                              f"--annotation {annot_file}")
        logger.info(f"Command line to convert: {powershell_command}")
        # Run PowerShell through subprocess
        convert = subprocess.Popen(["powershell", "-Command",
                                   powershell_command],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)
        output, error = convert.communicate()
        if output:
            converted_files.append(f"{file_name}.txt")
            logger.info(f"{rhchp} is successfully converted into "
                        f"{file_name}.txt")
        if error:
            print("Error while converting {rhchp} to txt file", error)
            logger.error(f"Error while converting {rhchp} to txt file")
            sys.exit(1)
    logger.info(f"Total {len(converted_files)} rhchp files are converted to "
                f"txt file. The files converted are {converted_files}")
    return converted_files


def filter_combine(args, txt_files) -> None:
    """
    Filter the array file(s) by removing unwanted SNP, and
    combine all files into a single txt file (in option1)
    """
    check_exist(args.snp_ref)
    good_snp_df = pd.read_excel(args.snp_ref,
                                sheet_name="Filtered SNPs good data set",
                                usecols=["probeset_id"])
    dfs = []
    n = 1
    sanity_check = []
    for array in txt_files:
        array_df = pd.read_csv(os.path.join(args.file_dir, array), sep="\t",
                               low_memory=False)
        if args.mode == "option1":
            array_df = array_df[["ProbeSetID", "Chr", "Position", "CallCode"]]
            array_df.rename({"ProbeSetID": "probeset_id"}, axis=1, inplace=True)
        elif args.mode == "option2":
            array_df.rename({"Probeset ID": "probeset_id"}, axis=1, inplace=True)
        filtered_df = pd.merge(good_snp_df, array_df, on=["probeset_id"],
                               how="inner")
        filtered_df.reset_index(drop=True, inplace=True)
        if args.mode == "option1":
            col_name = os.path.splitext(os.path.basename(array))[0] + ".rhchp"
            filtered_df.rename(
                {"Chr_x": "Chr", "Position_x": "Position",
                 "CallCode": col_name}, axis=1, inplace=True
                )
            filtered_df = filtered_df[["probeset_id", "Chr", "Position", col_name]]
        logger.info(f"Unwanted SNP are filtered out from {array}")

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
            filtered_pos_df = filtered_df[
                                (filtered_df["Position"] >= int(args.start))
                                & (filtered_df["Position"] <= int(args.end))
                                ]
            filtered_pos_df.reset_index(drop=True, inplace=True)
            filtered_df = filtered_pos_df
            logger.info(f"{array} file is filtered with Position from "
                        f"{args.start} to {args.end}")
        # merge df from each loop
        if n == 1:
            dfs = filtered_df
        else:
            dfs = pd.merge(dfs, filtered_df[["probeset_id", col_name]],
                           on="probeset_id", how="left")
        n = n+1
        sanity_check.append(len(filtered_df))
        logger.info(f"Complete filtering of {array}")

    # do sanity check
    if len(list(set(sanity_check))) > 1:
        print("Error with filtering so the number of SNP in individual "
              "files are not consistent")
        logger.error("Error with filtering so the number of SNP in "
                     "individual files are not consistent")
        sys.exit(1)

    # save as txt file
    outdir = os.path.join(args.file_dir, "filtered_array_output")
    outfile = os.path.basename(os.path.normpath(args.file_dir))
    dfs.rename({"probeset_id": "Probeset ID"}, axis=1, inplace=True)
    dfs.to_csv(os.path.join(outdir, outfile + "_" + datetimestr + ".txt"),
               sep="\t", index=False)
    logger.info(f"{outfile}_{datetimestr}.txt file is saved in {outdir}")


def check_exist(file_path) -> None:
    """
    Check if the file path exist
    """
    if os.path.exists(file_path):
        logger.info(f"{file_path} exists")
    else:
        logger.error(f"{file_path} does not exist")
        sys.exit(1)


def main(args):
    """
    Call functions to convert and/or filter array files
    """
    get_log(args.file_dir)
    logger.info(f"Command line: {' '.join(sys.argv)}")

    # option1 converts rhchp files to txt and then filters
    if args.mode == "option1":
        logger.info("option1 mode is used")
        converted_files = conversion(args)
        filter_combine(args, converted_files)
    # option2 does not convert, just filters
    elif args.mode == "option2":
        logger.info("option2 mode is used")
        if args.included is None or len(args.included) > 1:
            logger.error("-i empty or more than one file")
            sys.exit(1)
        converted_files = args.included
        filter_combine(args, converted_files)
    else:
        logger.error("mode has to be either option1 or option2")
        sys.exit(1)


if __name__ == "__main__":
    parsed_args = get_arguments()
    main(parsed_args)

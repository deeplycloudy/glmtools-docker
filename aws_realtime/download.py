import glob
import sys, os
import argparse
from datetime import datetime, timedelta
from time import sleep
from aws_goes import (GOESArchiveDownloader, GOESProduct, 
		      save_s3_product, netcdf_from_s3)
import logging
import subprocess

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('glmtools-docker.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

parse_desc = """ Create GLM grids fetched from the NOAA Big Data GOES bucket
on AWS."""

def create_parser():
    parser = argparse.ArgumentParser(description=parse_desc)
    parser.add_argument('-w', '--raw_dir', metavar='directory',
        required=True, dest='raw_dir', action='store',
        help="Raw L2 data will be saved to this directory, in subdirectories"
             "like /2018/Jul/04/")
    parser.add_argument('-s', '--satellite', metavar='GOES platform string',
        required=True, dest='satellite', action='store',
        help="goes16, goes17, etc.")
    return parser
    
def get_last_minute(minutes_to_try=5):
    # Fetch the previous minute of data. Get one minute ago, and then round down
    # to the nearest minute
    dt1min = timedelta(0, 60)
    lastmin = datetime.now() - dt1min
    startdate = datetime(lastmin.year, lastmin.month, lastmin.day, 
                          lastmin.hour, lastmin.minute)
    enddate = startdate + dt1min
    
    # at most, wait a few minutes for the full minute to be available
    dropdead = lastmin + dt1min*minutes_to_try

    return startdate, enddate, dropdead

def download(raw_dir, satellite):
    startdate, enddate, dropdead = get_last_minute()
    
    raw_path = os.path.join(raw_dir, startdate.strftime('%Y/%b/%d'))
    # grid_path = os.path.join(args.grid_dir, startdate.strftime('%Y/%b/%d'))
    if not os.path.exists(raw_path):
        os.makedirs(raw_path)
    # if not os.path.exists(grid_path):
        # os.makedirs(grid_path)

    arc = GOESArchiveDownloader()

    while True:
        to_process = []
        prod = GOESProduct(typ='GLM', satetlite=satellite)
        GLM_prods = arc.get_range(startdate, enddate, prod)
        for s3obj in GLM_prods:
            rawfile = save_s3_product(s3obj, raw_path)
            to_process.append(rawfile)
        if len(to_process) >= 3:
            # Should have three 20 s files in each minute
            return to_process
        elif datetime.now() > dropdead:
            # Just process what we have.
            return to_process
        else:
            # Keep waiting
            logger.debug("Waiting for more files; have {0}".format(
                len(to_process)))
            sleep(2)
            continue

    return to_process
    
        
def main(args):
    logger.info("Downloading L2 LCFA data")
    to_process = download(args.raw_dir, args.satellite)
    logger.info("Ready to process: {0}".format(to_process))
    

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    main(args)

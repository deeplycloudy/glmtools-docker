import sys, os
import argparse
from datetime import datetime, timedelta
from time import sleep
from aws_goes import (GOESArchiveDownloader, GOESProduct, 
		      save_s3_product, netcdf_from_s3)

parse_desc = """ Create GLM grids fetched from the NOAA Big Data GOES bucket
on AWS."""

def create_parser():
    parser = argparse.ArgumentParser(description=parse_desc)
    parser.add_argument('-w', '--raw_dir', metavar='directory',
        required=True, dest='raw_dir', action='store',
        help="Raw L2 data will be saved to this directory, in subdirectories"
             "like /2018/Jul/04/")
    parser.add_argument('-g', '--grid_dir', metavar='directory',
        required=True, dest='grid_dir', action='store',
        help="Gridded data will be saved to this directory, in subdirectories" 
             "like /2018/Jul/04/")
    return parser

def download(raw_dir):
    # Fetch the previous minute of data. Get one minute ago, and then round down
    # to the nearest minute
    dt1min = timedelta(0, 60)
    lastmin = datetime.now() - dt1min
    startdate = datetime(lastmin.year, lastmin.month, lastmin.day, 
                          lastmin.hour, lastmin.minute)
    enddate = startdate + dt1min
    
    # at most, wait a few minutes for the full minute to be available
    dropdead = lastmin + dt1min*5
    
    raw_path = os.path.join(raw_dir, startdate.strftime('%Y/%b/%d'))
    # grid_path = os.path.join(args.grid_dir, startdate.strftime('%Y/%b/%d'))
    if not os.path.exists(raw_path):
        os.makedirs(raw_path)
    # if not os.path.exists(grid_path):
        # os.makedirs(grid_path)

    arc = GOESArchiveDownloader()

    while True:
        to_process = []
        GLM_prods = arc.get_range(startdate, enddate, GOESProduct(typ='GLM'))
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
            print("Waiting for more files; have", len(to_process))
            sleep(2)
            continue

    return to_process

def main(args):
    to_process = download(args.raw_dir)

    grid_spec = ["--fixed_grid", "--split_events",
                "--goes_position", "east", "--goes_sector", "meso",
                "--dx=2.0", "--dy=2.0",
                "--ctr_lat=33.5", "--ctr_lon=-101.5",
                ]
    cmd_args = ["-o", args.grid_dir] + grid_spec + to_process

    # need to copy make_glm_grids to this driectory as part of driver script
    from make_GLM_grids import create_parser as create_grid_parser
    from make_GLM_grids import grid_setup
    grid_parser = create_grid_parser()
    grid_args = grid_parser.parse_args(cmd_args)    
    from multiprocessing import freeze_support
    freeze_support()
    gridder, glm_filenames, start_time, end_time, grid_kwargs = grid_setup(grid_args)
    gridder(glm_filenames, start_time, end_time, **grid_kwargs)

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    main(args)

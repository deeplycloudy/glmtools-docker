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
    parser.add_argument('-p', '--plot', metavar='directory',
        required=False, dest='plot_dir', action='store', default='',
        help="Plots of the gridded data will be saved to this directory,"
             "in subdirectories like /2018/Jul/04/")
    parser.add_argument('-g', '--grid_dir', metavar='directory',
        required=True, dest='grid_dir', action='store',
        help="Gridded data will be saved to this directory, in subdirectories" 
             "like /2018/Jul/04/")
    parser.add_argument('-c', '--scene', dest='scene', action='store',
        default='C',
        help="One of C, M1, M2, or F, matching the scene ID part of the"
             " filename")
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

def download(raw_dir):
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
            logger.DEBUG("Waiting for more files; have {0}".format(
                len(to_process)))
            sleep(2)
            continue

    return to_process

def wait_for_local_data(raw_dir):
    startdate, enddate, dropdead = get_last_minute()
    raw_path = os.path.join(raw_dir, startdate.strftime('%Y/%b/%d'))

    twentysec = timedelta(0, 20)
    prod = GOESProduct(typ='GLM')

    # Construct a pattern that will match the start time of each of the
    # GLM files in this minute.
    GLM_prods = [os.path.join(raw_path, os.path.split(prod.with_start_time(
                    startdate + twentysec*ti))[-1] +'*.nc')
                 for ti in range(3)]
    logger.info("Looking for {0}".format(GLM_prods))
    while True:
        to_process = []
        for this_prod in GLM_prods:
            to_process.extend(glob.glob(this_prod))
        if len(to_process) >= 3:
            # Should have three 20 s files in each minute
            return to_process
        elif datetime.now() > dropdead:
            # Just process what we have.
            return to_process
        else:
            # Keep waiting
            logger.debug("Waiting for more local files; have {0}".format(
                len(to_process)))
            sleep(2)
            continue
        # Use aws filename assembly infrastructure
        return to_process

def make_plots(gridfiles, outdir):
    import os
    import matplotlib.pyplot as plt

    from glmtools.io.imagery import open_glm_time_series

    from plots import plot_glm

    fields_6panel = ['flash_extent_density', 'average_flash_area','total_energy', 
                     'group_extent_density', 'average_group_area', 'group_centroid_density']
    
    glm_grids = open_glm_time_series(gridfiles)

    time_options = glm_grids.time.to_series()
    time_options.sort_values(inplace=True)

    fig = plt.figure(figsize=(18,12))
    file_tag = 'fed_afa_toe_ged_aga_gcd'
    images_out = []
    for t in time_options:
        plot_glm(fig, glm_grids, t, fields_6panel, subplots=(2,3))

        outpath = os.path.join(outdir, '20%s' %(t.strftime('%y/%b/%d')))
        if os.path.exists(outpath) == False:
            os.makedirs(outpath)

        # EOL field catalog convention
        eol_template = 'satellite.GOES-16.{0}.GLM_{1}.png'
        time_str = t.strftime('%Y%m%d%H%M')

        png_name = eol_template.format(time_str, file_tag)
        outfile=os.path.join(outpath, png_name)
        outfile = outfile.replace(' ', '_')
        outfile = outfile.replace(':', '')
        images_out.append(outfile)
        fig.savefig(outfile, facecolor='black', dpi=150)
    return images_out
    
        
def main(args):
    # to_process = download(args.raw_dir)
    to_process = wait_for_local_data(args.raw_dir)
    logger.info("Processing {0}".format(to_process))

    grid_spec = ["--fixed_grid", "--split_events",
                "--goes_position", "east",
		        "--width=2000", "--height=2000",
                "--dx=2.0", "--dy=2.0",
                "--ctr_lat=-29.0", "--ctr_lon=-64.0",
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
    logger.info("About to grid {0}".format(glm_filenames))
    the_grids = gridder(glm_filenames, start_time, end_time, **grid_kwargs)
    logger.info("Created {0}".format(the_grids))
    
    # Since the_grids is probably empty, due to some weird bug in glmtools,
    # we will just go find the correct times from the files to_process.
    # The above command only grids one minute at a time, so we just find the
    # start time of the earliest file.
    
    from glmtools.io.glm import parse_glm_filename
    raw_filenames = [os.path.split(fntp)[-1] for fntp in to_process]
    starts = [parse_glm_filename(fntp)[3] for fntp in raw_filenames]
    startdate = min(starts)
    
    mode='M3'
    platform='G16'
    grid_path = os.path.join(args.grid_dir, startdate.strftime('%Y/%b/%d'))
    # "OR_GLM-L2-GLMC-M3_G16_s20181011100000_e20181011101000_c20181011124580.nc 
    # Won't know file created time.
    dataset_name = "OR_GLM-L2-GLM{3}-{0}_{1}_s{2}*.nc".format(
        mode, platform, startdate.strftime('%Y%j%H%M%S0'), args.scene)
    expected_grid_full_path = os.path.join(grid_path, dataset_name)
    # logger.debug("Expecting grid {0}".format(expected_grid_full_path))
    expected_file = glob.glob(expected_grid_full_path)
    logger.debug("Expecting grid {0}".format(expected_file))
    
    if args.plot_dir != '':
        image_filenames = make_plots(expected_file, args.plot_dir)
        eol = "ftp://catalog.eol.ucar.edu/pub/incoming/catalog/relampago/"
        curl_template = "curl -T {0} {1}"
        logger.debug("Preparing to upload image(s) to EOL ")
        for imgf in image_filenames:
            curl_cmd = curl_template.format(imgf, eol).split()
            logger.debug("Curl cmd is {0}".format(curl_cmd))
            output = subprocess.check_output(curl_cmd, stderr=subprocess.STDOUT)
            logger.debug("{0}".format(output))
            logger.info("Uploaded image {0} to EOL".format(imgf))

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    main(args)

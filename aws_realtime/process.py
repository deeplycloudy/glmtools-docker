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
    parser.add_argument('-d', '--date', metavar='%Y-%m-%dT%H:%M:%SZ',
        required=True, dest='date', action='store',
        help="Download data at this time (UTC)")
    parser.add_argument('-s', '--satellite', metavar='GOES platform string',
        required=True, dest='satellite', action='store',
        help="goes16, goes17, etc.")
    parser.add_argument('-p', '--plot', metavar='directory',
        required=False, dest='plot_dir', action='store', default='',
        help="Plots of the gridded data will be saved to this directory,"
             "in subdirectories like /2018/Jul/04/")
    parser.add_argument('-g', '--grid_dir', metavar='directory',
        required=True, dest='grid_dir', action='store',
        default="{start_time:%Y/%b/%d}/{dataset_name}",
        help="Gridded data will be saved to this directory, by default in" 
             "subdirectories like /2018/Jul/04/")
    parser.add_argument('-c', '--scene', dest='scene', action='store',
        default='C',
        help="One of C, M1, M2, or F, matching the scene ID part of the"
             " filename")
    parser.add_argument('-r', '--resolution', dest='resolution', action='store',
        default=2.0, type=float,
        help="2.0 or 4.0, the nominal pixel size in km")
    return parser
    
def get_the_time(now, duration=60, minutes_to_try=5):
    # Fetch data begginning with datetime *now* and ending with
    # duration seconds later
    dt1min = timedelta(0, duration)
    lastmin = now
    startdate = datetime(lastmin.year, lastmin.month, lastmin.day, 
                          lastmin.hour, lastmin.minute)
    enddate = startdate + dt1min
    
    # at most, wait a few minutes for the full minute to be available
    dropdead = lastmin + dt1min*minutes_to_try

    return startdate, enddate, dropdead


def wait_for_local_data(raw_dir, satellite, date):
    startdate, enddate, dropdead = get_the_time(date, duration=60)
    raw_path = os.path.join(raw_dir, startdate.strftime('%Y/%b/%d'))

    twentysec = timedelta(0, 20)
    prod = GOESProduct(typ='GLM', satellite=satellite)

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

    # from plots import plot_glm
    from glmtools.plot.grid import plot_glm_grid

    fields_6panel = ['flash_extent_density', 'average_flash_area','total_energy', 
                     'group_extent_density', 'average_group_area', 'group_centroid_density']
    
    glm_grids = open_glm_time_series(gridfiles)

    time_options = glm_grids.time.to_series()
    time_options.sort_values(inplace=True)

    # For conus, a 3x2 panel plot is (2500*3),(1500*2), or a ratio of 2.5
    fig = plt.figure(figsize=(25,10))
    file_tag = 'fed_afa_toe_ged_aga_gcd'
    images_out = []
    for t in time_options:
        plot_glm_grid(fig, glm_grids, t, fields_6panel, subplots=(2,3))

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
    date = datetime.strptime(args.date, '%Y-%m-%dT%H:%M:%SZ')
    to_process = wait_for_local_data(args.raw_dir, args.satellite, date)
    logger.info("Processing {0}".format(to_process))

    scene_code_names= {'C':'conus', 'F':'full'}
    satellite_positions = {'goes16':'east', 'goes17':'west'}
    satellite_platform_filename_code = {'goes16':'G16', 'goes17':'G17'}
    grid_spec = ["--fixed_grid", "--split_events",
                "--goes_position",
                satellite_positions[args.satellite],
                "--goes_sector",
                scene_code_names[args.scene],
                "--dx={0:3.1f}".format(args.resolution), 
                "--dy={0:3.1f}".format(args.resolution),
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
    platform=satellite_platform_filename_code[args.satellite]
    
    grid_path = args.grid_dir.replace('/{dataset_name}', '').format(start_time=startdate)
    # grid_path = os.path.join(args.grid_dir, startdate.strftime('%Y/%b/%d'))
    # "OR_GLM-L2-GLMC-M3_G16_s20181011100000_e20181011101000_c20181011124580.nc 
    # Won't know file created time.
    dataset_name = "OR_GLM-L2-GLM{3}-{0}_{1}_s{2}*.nc".format(
        mode, platform, startdate.strftime('%Y%j%H%M%S0'), args.scene)
    expected_grid_full_path = os.path.join(grid_path, dataset_name)
    # logger.debug("Expecting grid {0}".format(expected_grid_full_path))
    print(expected_grid_full_path)
    expected_file = glob.glob(expected_grid_full_path)
    logger.debug("Expecting grid {0}".format(expected_file))
    
    if args.plot_dir != '':
        image_filenames = make_plots(expected_file, args.plot_dir)
        # eol = "ftp://catalog.eol.ucar.edu/pub/incoming/catalog/relampago/"
        # curl_template = "curl -T {0} {1}"
        # logger.debug("Preparing to upload image(s) to EOL ")
        # for imgf in image_filenames:
        #     curl_cmd = curl_template.format(imgf, eol).split()
        #     logger.debug("Curl cmd is {0}".format(curl_cmd))
        #     output = subprocess.check_output(curl_cmd, stderr=subprocess.STDOUT)
        #     logger.debug("{0}".format(output))
        #     logger.info("Uploaded image {0} to EOL".format(imgf))

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    main(args)

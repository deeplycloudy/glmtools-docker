#!/bin/bash

# After an observation minute ends, the GLM data take some time to process
# through the ground system. This is typically at least 20 s. 

# Assuming this script is kicked off at the start of each minute, and
# process.py processes the previous minute, this logic should keep us as
# current as possible.

SATELLITE=goes16
LCFADIR=/glm_raw_data
PLOTDIR=/glm_plots
GRIDDIR=/glm_grid_data/{start_time:%Y/%b/%d}/{dataset_name}

cd /home/glm/aws_realtime/
cp /home/glm/glmtools/examples/grid/make_GLM_grids.py .
source activate glmval

sleep 20s
# Make the grids and make plots
python download.py -w $LCFADIR -s $SATELLITE
python process.py -w $LCFADIR -s $SATELLITE -g $GRIDDIR -p $PLOTDIR -c C
python process.py -w $LCFADIR -s $SATELLITE -g $GRIDDIR -p $PLOTDIR -c F

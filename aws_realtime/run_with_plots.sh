#!/bin/bash

# After an observation minute ends, the GLM data take some time to process
# through the ground system. This is typically at least 20 s. 

# Assuming this script is kicked off at the start of each minute, and
# process.py processes the previous minute, this logic should keep us as
# current as possible.

cd /home/glm/aws_realtime/
cp /home/glm/glmtools/examples/grid/make_GLM_grids.py .
source activate glmval

sleep 20s
# Make the grids and make plots
python process.py -w /glm_raw_data -g /glm_grid_data -p /glm_plots -c C
# python process.py -w /archive/GLM/GLM-L2-LCFA_G16/ -g ../testrun/grid -p ../testrun/plot -c M1

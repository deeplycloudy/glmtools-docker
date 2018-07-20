#!/bin/bash

# After an observation minute ends, the GLM data take some time to process
# through the ground system. This is typically at least 20 s. 

# Assuming this script is kicked off at the start of each minute, and
# process.py processes the previous minute, this logic should keep us as
# current as possible.

sleep 20s

cd /home/glm/aws_realtime/
cp /home/glm/glmtools/examples/grid/make_GLM_grids.py .
source activate glmval
python process.py -w /glm_raw_data -g /glm_grid_data

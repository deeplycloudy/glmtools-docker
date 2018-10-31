#!/bin/bash

GRIDCONTAINER=glm-conus
GLMRAW=/archive/GLM/GLM-L2-LCFA_G16
GLMGRID=/archive/GLM/GLM-L2-GRID_G16

source activate glmval
# docker run -d \
#   --mount type=bind,src=$GLMRAW,dst=/glm_raw_data \
#   --mount type=bind,src=$GLMGRID,dst=/glm_grid_data \
#   $GRIDCONTAINER /home/glm/aws_realtime/run.sh
docker exec -d glm-conus /home/glm/aws_realtime/run.sh
docker exec -d glm-relampago /home/glm/aws_realtime/run_with_plots.sh

# This command waits for files based on datetime.now(), so we want to ensure it
# uses the same processing minute as the long-running GLM processing script.
# -g is the path to the gridded data inside the ldm container.
# run.sh in the glm gridding container waits 20s before running the gridding
# script. This should start both scripts at about the same time.
sleep 20
# python ldm_insert.py -g $GLMGRID
docker exec -d ldm-prod python /home/ldm/ldm_insert.py -g /glm_grid_data
docker exec -d ldm-prod python /home/ldm/ldm_insert.py -g /glm_grid_relampago
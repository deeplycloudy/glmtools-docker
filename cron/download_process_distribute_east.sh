#!/bin/bash

# The containers below are assumed to be already started and running, with all
# necessary paths mounted.
PROCESSSCRIPT=/home/glm/aws_realtime/run_with_plots_east.sh
GRIDCONTAINER=glm-prod-east
LDMCONTAINER=ldm-prod

# source activate glmval
docker exec $GRIDCONTAINER $PROCESSSCRIPT

# This command waits for files based on datetime.now(), so we want to ensure it
# uses the same processing minute as the long-running GLM processing script.
# -g is the path to the gridded data inside the ldm container.
# run.sh in the glm gridding container waits 20s before running the gridding
# script. This should start both scripts at about the same time.
# sleep 20
docker exec -d  $LDMCONTAINER python /home/ldm/ldm_insert.py -g /glm_grid_data

# Wait a bit of extra time for the full disk to finish processing since it
# is started sequentially after the conus processing
# sleep 10
docker exec -d $LDMCONTAINER python /home/ldm/ldm_insert.py -g /glm_grid_data -c F

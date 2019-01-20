#!/bin/bash

# The containers below are assumed to be already started and running, with all
# necessary paths mounted.
GRIDCONTAINER=glm-conus
LDMCONTAINER=ldm-prod

source activate glmval
docker exec -d $GRIDCONTAINER /home/glm/aws_realtime/run_with_plots.sh

# This command waits for files based on datetime.now(), so we want to ensure it
# uses the same processing minute as the long-running GLM processing script.
# -g is the path to the gridded data inside the ldm container.
# run.sh in the glm gridding container waits 20s before running the gridding
# script. This should start both scripts at about the same time.
sleep 20
docker exec -d $LDMCONTAINER python /home/ldm/ldm_insert.py -g /glm_grid_data

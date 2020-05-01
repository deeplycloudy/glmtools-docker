#!/bin/bash

# After an observation minute ends, the GLM data take some time to process
# through the ground system. This is typically at least 20 s. So wait 80s,
# which is the end of the observation minute plus 20 s.

# Process this date and satellite platform
# 2020-03-14T17:15:50+00:00
DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
SATELLITE=goes17
sleep 80s

# The containers below are assumed to be already started and running, with all
# necessary paths mounted. Paths are within the containers.
PROCESSSCRIPT="/home/glm/aws_realtime/run_with_plots.sh $DATE $SATELLITE"
GRIDCONTAINER=glm-17
LDMCONTAINER=ldm-prod
LDMGRIDDIR=/home/ldm/var/data/GLM-L2-GRID_G17

# source activate glmval
timeout 2m docker exec $GRIDCONTAINER $PROCESSSCRIPT

#docker exec $LDMCONTAINER python /home/ldm/ldm_insert.py -d $DATE -g $LDMGRIDDIR -c C -s $SATELLITE
#docker exec $LDMCONTAINER python /home/ldm/ldm_insert.py -d $DATE -g $LDMGRIDDIR -c F -s $SATELLITE

/home/ec2-user/sources/glmtools-docker/cron/rsync_to_graupel_west.sh
#!/bin/bash

# After an observation minute ends, the GLM data take some time to process
# through the ground system. This is typically at least 20 s. So wait 80s,
# which is the end of the observation minute plus 20 s.

# Process this date and satellite platform
# 2020-03-14T17:15:50+00:00
DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
SATELLITE=goes16
sleep 80s

# The containers below are assumed to be already started and running, with all
# necessary paths mounted. Paths are within the containers.
PROCESSSCRIPT="/home/glm/aws_realtime/run_with_plots.sh $DATE $SATELLITE"
GRIDCONTAINER=glm-16
LDMCONTAINER=ldm-prod
LDMGRIDDIR=/home/ldm/var/data/GLM-L2-GRID_G16

# source activate glmval
timeout 2m docker exec $GRIDCONTAINER $PROCESSSCRIPT

dockerconus="docker exec $LDMCONTAINER python3 /home/ldm/ldm_insert.py -d $DATE -g $LDMGRIDDIR -c C -s $SATELLITE"
dockerfull="docker exec $LDMCONTAINER python3 /home/ldm/ldm_insert.py -d $DATE -g $LDMGRIDDIR -c F -s $SATELLITE"

/home/ec2-user/sources/glmtools-docker/cron/rsync_to_graupel_east.sh
ssh -p 2388 ebruning@localhost "$dockerconus && $dockerfull"

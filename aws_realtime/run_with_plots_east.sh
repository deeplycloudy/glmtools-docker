#!/bin/bash

# Date and time string matchign the format of date -Iseconds
DATE=$1
SATELLITE=$2

LCFADIR=/glm_raw_data
PLOTDIR=/glm_plots
GRIDDIR=/glm_grid_data/{start_time:%Y/%b/%d}/{dataset_name}

cd /home/glm/aws_realtime/
cp /home/glm/glmtools/examples/grid/make_GLM_grids.py .
source activate glmval

# 2020-03-14T17:15:50+00:00
# DATE=`date -Iseconds`
# Make the grids and make plots
# sleep 80s
python download.py -w $LCFADIR -s $SATELLITE -d $DATE
python process.py -w $LCFADIR -s $SATELLITE  -d $DATE -g $GRIDDIR -c C
# -p $PLOTDIR
# python process.py -w $LCFADIR -s $SATELLITE -d $DATE -g $GRIDDIR -c F

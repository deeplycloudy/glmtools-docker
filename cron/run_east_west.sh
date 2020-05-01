#!/bin/bash
cd /home/ec2-user/sources/glmtools-docker/cron
timeout 4m ./download_process_distribute_east.sh
# timeout 4m ./download_process_distribute_west.sh


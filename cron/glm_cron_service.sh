#!/bin/bash

# rm below should only remove volumes created within the image, and should 
# leave volumes created by docker volume create and bind mounts untouched.
docker run --rm -d --name docker-cron                         \
  -v /var/run/docker.sock:/var/run/docker.sock                \
  --env TASK_SCHEDULE='* * * * *'                             \
  -v $PWD/containerInfo.json:/usr/src/containerInfo.json      \
  camilin87/docker-cron

# glmtools-docker
Dockerized glmtools

## Setup

### Build the glmtest Docker image

```
cd ~/sources/glmtools-docker
docker build -t glmtest .
```
## Process some GLM data. 

To look around the glmtest image,

```bash
# Start up an interactive shell, mounting the raw L2 and destination grid
# directories on your local server (here, in /archive) to glm_raw_data and glm_grid_data in the container
docker run -i -t \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-LCFA_G16,dst=/glm_raw_data' \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-GRID_G16,dst=/glm_grid_data' \
  glmtest /bin/bash
```

To process the current minute,

```bash
docker run -i -t \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-LCFA_G16,dst=/glm_raw_data' \
  --mount 'type=bind,src=/archive/GLM/GLM-L2-GRID_G16,dst=/glm_grid_data' \
  glmtest /home/glm/aws_realtime/run.sh
```

There is also a docker-based cron service (not using the system cron) that can
process GLM data on a regular schedule. It uses the
https://github.com/camilin87/docker-cron image, as described here:
https://www.tddapps.com/2017/02/18/how-to-run-any-container-on-a-schedule/

See the the `README` in the cron directory for usage.
